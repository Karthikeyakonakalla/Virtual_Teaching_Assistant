"""Query API endpoints for handling user questions."""

import os
import uuid
import logging
from pathlib import Path
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename

from services import (
    GeminiClient,
    OCRService,
    STTService,
    TTSService,
    RAGPipeline,
    SolutionFormatter
)

logger = logging.getLogger(__name__)

# Create blueprint
query_bp = Blueprint('query', __name__)

# Initialize services
gemini_client = None
ocr_service = None
stt_service = None
tts_service = None
rag_pipeline = None
solution_formatter = None


def init_services():
    """Initialize all services."""
    global gemini_client, ocr_service, stt_service, tts_service, rag_pipeline, solution_formatter
    
    if not gemini_client:
        gemini_client = GeminiClient()
    if not ocr_service:
        ocr_service = OCRService()
    if not stt_service:
        stt_service = STTService()
    if not tts_service:
        tts_service = TTSService()
    if not rag_pipeline:
        rag_pipeline = RAGPipeline()
    if not solution_formatter:
        solution_formatter = SolutionFormatter()


@query_bp.route('/query', methods=['POST'])
def submit_query():
    """Submit a new query for processing.
    
    Accepts:
    - Text query in JSON body
    - Audio file upload
    - Image file upload
    
    Returns:
        JSON response with query ID and initial status
    """
    init_services()
    
    try:
        query_id = str(uuid.uuid4())
        query_text = None
        input_type = 'text'

        data = request.get_json(silent=True)

        # Handle text input
        if data and 'query' in data:
            query_text = data['query']
            input_type = 'text'
            logger.info(f"Received text query: {query_text[:100]}...")
        
        # Handle audio input
        elif 'audio' in request.files:
            audio_file = request.files['audio']
            if audio_file and allowed_audio_file(audio_file.filename):
                # Save audio file
                filename = secure_filename(f"{query_id}_audio.wav")
                audio_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                audio_file.save(audio_path)
                
                # Transcribe audio
                transcription_result = stt_service.transcribe_file(audio_path)
                
                if transcription_result['success']:
                    query_text = transcription_result['transcript']
                    input_type = 'audio'
                    logger.info(f"Transcribed audio query: {query_text}")
                else:
                    return jsonify({
                        'success': False,
                        'error': transcription_result.get('error', 'Transcription failed')
                    }), 400
        
        # Handle image input
        elif 'image' in request.files:
            image_file = request.files['image']
            if image_file and allowed_image_file(image_file.filename):
                # Save image file
                filename = secure_filename(f"{query_id}_image.{image_file.filename.split('.')[-1]}")
                image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                image_file.save(image_path)

                # Send raw image to Groq vision model
                analysis_result = gemini_client.analyze_image(
                    image_path,
                    request.form.get('context', '')
                )

                if analysis_result['success']:
                    formatted = solution_formatter.format_solution(
                        analysis_result['analysis'],
                        query_type='general'
                    )

                    return jsonify({
                        'success': True,
                        'query_id': query_id,
                        'input_type': 'image',
                        'solution': formatted,
                        'processed': True
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': analysis_result.get('error', 'Failed to process image')
                    }), 400
        
        else:
            return jsonify({
                'success': False,
                'error': 'No valid input provided'
            }), 400
        
        # Process the query
        if query_text:
            # Detect subject/topic
            subject = detect_subject(query_text)
            
            # Search for relevant context using RAG
            context = rag_pipeline.search(
                query_text,
                top_k=current_app.config['TOP_K_RETRIEVAL'],
                subject_filter=subject
            )
            
            # Generate solution
            response = gemini_client.generate_response(
                query_text,
                context,
                temperature=current_app.config['TEMPERATURE'],
                max_tokens=current_app.config['MAX_TOKENS']
            )
            
            if response['success']:
                # Format the solution
                formatted = solution_formatter.format_solution(
                    response['answer'],
                    query_type=detect_query_type(query_text)
                )
                
                # Generate audio if requested
                audio_data = None
                if data and data.get('include_audio', False):
                    tts_result = tts_service.synthesize_speech(
                        formatted['display_text']
                    )
                    if tts_result['success']:
                        audio_data = tts_result['audio_base64']
                
                return jsonify({
                    'success': True,
                    'query_id': query_id,
                    'input_type': input_type,
                    'query': query_text,
                    'subject': subject,
                    'solution': formatted,
                    'context_used': context,
                    'audio': audio_data,
                    'processed': True
                })
            else:
                return jsonify({
                    'success': False,
                    'query_id': query_id,
                    'error': response.get('error', 'Failed to generate solution')
                }), 500
        
        return jsonify({
            'success': False,
            'error': 'No query text could be extracted'
        }), 400
        
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@query_bp.route('/query/<query_id>/followup', methods=['POST'])
def submit_followup(query_id):
    """Handle follow-up questions for an existing query."""
    init_services()

    try:
        data = request.get_json(silent=True) or {}
        question = (data.get('question') or '').strip()
        previous_solution = (data.get('previous_solution') or '').strip()

        if not question:
            return jsonify({
                'success': False,
                'error': 'Follow-up question is required.'
            }), 400

        subject = detect_subject(question)

        context = rag_pipeline.search(
            question,
            top_k=current_app.config['TOP_K_RETRIEVAL'],
            subject_filter=subject
        )

        if previous_solution:
            context.insert(0, {
                'content': f"Previous solution summary:\n{previous_solution}"
            })

        followup_prompt = (
            "You previously answered a problem. Use that context if provided and answer the follow-up question.\n"
            f"Follow-up Question: {question}"
        )

        response = gemini_client.generate_response(
            followup_prompt,
            context,
            temperature=current_app.config['TEMPERATURE'],
            max_tokens=current_app.config['MAX_TOKENS']
        )

        if not response['success']:
            return jsonify({
                'success': False,
                'query_id': query_id,
                'error': response.get('error', 'Failed to generate follow-up answer')
            }), 500

        formatted = solution_formatter.format_solution(
            response['answer'],
            query_type=detect_query_type(question)
        )

        return jsonify({
            'success': True,
            'query_id': query_id,
            'answer': formatted.get('display_text', response['answer']),
            'solution': formatted,
            'context_used': context,
            'subject': subject
        })

    except Exception as e:
        logger.error(f"Error processing follow-up: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@query_bp.route('/query/<query_id>', methods=['GET'])
def get_query_result(query_id):
    """Get the result of a processed query.
    
    Args:
        query_id: UUID of the query
        
    Returns:
        JSON response with query result
    """
    # In a production system, this would retrieve from a database
    # For now, return a placeholder
    return jsonify({
        'query_id': query_id,
        'status': 'completed',
        'message': 'Query result would be retrieved from database'
    })


@query_bp.route('/query/<query_id>/audio', methods=['GET'])
def get_audio_response(query_id):
    """Generate audio response for a query.
    
    Args:
        query_id: UUID of the query
        
    Returns:
        JSON response with audio data
    """
    init_services()
    
    try:
        # Get the solution text (would be from database in production)
        solution_text = request.args.get('text', 'Solution text not provided')
        
        # Generate audio
        tts_result = tts_service.synthesize_speech(solution_text)
        
        if tts_result['success']:
            return jsonify({
                'success': True,
                'audio': tts_result['audio_base64'],
                'format': tts_result['format']
            })
        else:
            return jsonify({
                'success': False,
                'error': tts_result.get('error', 'Audio generation failed')
            }), 500
            
    except Exception as e:
        logger.error(f"Error generating audio: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@query_bp.route('/history', methods=['GET'])
def get_query_history():
    """Get query history for the current user.
    
    Returns:
        JSON response with query history
    """
    # In production, this would retrieve from database based on user session
    return jsonify({
        'success': True,
        'history': [],
        'message': 'Query history would be retrieved from database'
    })


def allowed_image_file(filename):
    """Check if file is an allowed image type.
    
    Args:
        filename: Name of the file
        
    Returns:
        Boolean indicating if file is allowed
    """
    allowed = current_app.config['ALLOWED_EXTENSIONS']
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed


def allowed_audio_file(filename):
    """Check if file is an allowed audio type.
    
    Args:
        filename: Name of the file
        
    Returns:
        Boolean indicating if file is allowed
    """
    allowed = {'wav', 'mp3', 'ogg', 'm4a', 'webm'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed


def detect_subject(text):
    """Detect subject from query text.
    
    Args:
        text: Query text
        
    Returns:
        Detected subject or None
    """
    text_lower = text.lower()
    
    physics_keywords = ['force', 'velocity', 'electric', 'magnetic', 'optics']
    chemistry_keywords = ['element', 'reaction', 'acid', 'base', 'organic']
    maths_keywords = ['equation', 'derivative', 'matrix', 'probability', 'integral']
    
    physics_score = sum(1 for kw in physics_keywords if kw in text_lower)
    chemistry_score = sum(1 for kw in chemistry_keywords if kw in text_lower)
    maths_score = sum(1 for kw in maths_keywords if kw in text_lower)
    
    scores = {
        'physics': physics_score,
        'chemistry': chemistry_score,
        'mathematics': maths_score
    }
    
    max_score = max(scores.values())
    if max_score > 0:
        return max(scores, key=scores.get)
    
    return None


def detect_query_type(text):
    """Detect the type of query.
    
    Args:
        text: Query text
        
    Returns:
        Query type string
    """
    text_lower = text.lower()
    
    if any(phrase in text_lower for phrase in ['option', 'choose', 'which of', 'select']):
        return 'mcq'
    elif any(phrase in text_lower for phrase in ['calculate', 'find the value', 'compute']):
        return 'numerical'
    elif any(phrase in text_lower for phrase in ['true or false', 'correct or incorrect']):
        return 'true_false'
    else:
        return 'general'
