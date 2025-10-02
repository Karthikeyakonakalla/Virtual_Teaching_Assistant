"""Speech-to-Text service using Groq Whisper API."""

import os
import io
import logging
from typing import Dict, Any, Optional

import requests
from groq import Groq
from pydub import AudioSegment

logger = logging.getLogger(__name__)


class STTService:
    """Service for converting speech to text."""

    def __init__(self):
        """Initialize the STT service."""
        self.sample_rate = int(os.getenv('AUDIO_SAMPLE_RATE', 16000))
        self.max_duration = int(os.getenv('AUDIO_MAX_DURATION', 60))
        self.model = os.getenv('GROQ_STT_MODEL', 'whisper-large-v3-turbo')
        self.language = os.getenv('GROQ_STT_LANGUAGE', 'en')

        self.api_key = os.getenv('GROQ_API_KEY')
        if not self.api_key:
            logger.error("GROQ_API_KEY not found in environment variables")
            raise ValueError("GROQ_API_KEY is required for STTService")

        try:
            self.client = Groq(api_key=self.api_key)
            logger.info(f"Groq STT client initialized with model: {self.model}")
        except Exception as exc:
            logger.error(f"Failed to initialize Groq STT client: {exc}")
            raise

    def transcribe_audio(self, audio_data: bytes, format: str = 'wav') -> Dict[str, Any]:
        """Transcribe audio data to text using Groq Whisper."""
        try:
            # Convert audio to WAV if needed
            wav_data = audio_data if format == 'wav' else self._convert_to_wav(audio_data, format)

            audio_file = io.BytesIO(wav_data)
            audio_file.name = 'audio.wav'

            audio_file.seek(0)

            response = requests.post(
                "https://api.groq.com/openai/v1/audio/transcriptions",
                headers={
                    "Authorization": f"Bearer {self.api_key}"
                },
                data={
                    "model": self.model,
                    "response_format": "json",
                    "language": self.language,
                    "temperature": 0.0
                },
                files={
                    "file": (audio_file.name, audio_file, "audio/wav")
                },
                timeout=120
            )
            response.raise_for_status()

            transcription = response.json()

            transcript_text = transcription.get('text', '')

            transcript_text = transcript_text.strip()
            if not transcript_text:
                return {
                    'success': False,
                    'error': 'Transcription returned empty text',
                    'transcript': ''
                }

            subject = self._detect_subject(transcript_text)

            segments = transcription.get('segments')

            return {
                'success': True,
                'transcript': transcript_text,
                'language': self.language,
                'subject_hint': subject,
                'segments': segments
            }

        except Exception as exc:
            logger.error(f"Error transcribing audio with Groq Whisper: {exc}")
            return {
                'success': False,
                'error': str(exc),
                'transcript': ''
            }

    def transcribe_file(self, file_path: str) -> Dict[str, Any]:
        """Transcribe an audio file.
        
        Args:
            file_path: Path to the audio file
            
        Returns:
            Dictionary containing transcription
        """
        try:
            # Validate file
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Audio file not found: {file_path}")
            
            # Check duration
            duration = self._get_audio_duration(file_path)
            if duration > self.max_duration:
                return {
                    'success': False,
                    'error': f'Audio duration ({duration}s) exceeds maximum ({self.max_duration}s)',
                    'transcript': ''
                }
            
            # Read audio file
            with open(file_path, 'rb') as f:
                audio_data = f.read()
            
            # Get file format
            format = file_path.split('.')[-1].lower()
            
            return self.transcribe_audio(audio_data, format)
            
        except Exception as e:
            logger.error(f"Error transcribing file: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'transcript': ''
            }
    
    def _convert_to_wav(self, audio_data: bytes, format: str) -> bytes:
        """Convert audio data to WAV format.
        
        Args:
            audio_data: Original audio data
            format: Original format
            
        Returns:
            WAV audio data
        """
        try:
            # Create AudioSegment from data
            audio = AudioSegment.from_file(
                io.BytesIO(audio_data),
                format=format
            )
            
            # Convert to WAV
            audio = audio.set_frame_rate(self.sample_rate)
            audio = audio.set_channels(1)  # Mono
            
            # Export to bytes
            output = io.BytesIO()
            audio.export(output, format='wav')
            return output.getvalue()
            
        except Exception as e:
            logger.error(f"Error converting audio: {str(e)}")
            raise
    
    def _get_audio_duration(self, file_path: str) -> float:
        """Get duration of audio file in seconds.
        
        Args:
            file_path: Path to audio file
            
        Returns:
            Duration in seconds
        """
        try:
            audio = AudioSegment.from_file(file_path)
            return len(audio) / 1000.0  # Convert ms to seconds
        except Exception:
            return 0.0
    
    def _detect_subject(self, text: str) -> Optional[str]:
        """Detect subject from transcribed text.
        
        Args:
            text: Transcribed text
            
        Returns:
            Detected subject or None
        """
        text_lower = text.lower()
        
        # Subject keywords
        physics_keywords = [
            'force', 'velocity', 'acceleration', 'momentum', 'energy',
            'electric', 'magnetic', 'circuit', 'resistance', 'current',
            'optics', 'wave', 'thermodynamics', 'kinetic', 'potential'
        ]
        
        chemistry_keywords = [
            'element', 'compound', 'reaction', 'acid', 'base',
            'oxidation', 'reduction', 'mole', 'atomic', 'molecular',
            'organic', 'inorganic', 'equilibrium', 'solution', 'concentration'
        ]
        
        maths_keywords = [
            'equation', 'derivative', 'integral', 'matrix', 'vector',
            'probability', 'permutation', 'combination', 'trigonometry',
            'logarithm', 'polynomial', 'function', 'limit', 'differentiation'
        ]
        
        # Count keyword matches
        physics_count = sum(1 for kw in physics_keywords if kw in text_lower)
        chemistry_count = sum(1 for kw in chemistry_keywords if kw in text_lower)
        maths_count = sum(1 for kw in maths_keywords if kw in text_lower)
        
        # Return subject with highest count
        counts = {
            'physics': physics_count,
            'chemistry': chemistry_count,
            'mathematics': maths_count
        }
        
        if max(counts.values()) > 0:
            return max(counts, key=counts.get)
        
        return None
    
    def _offline_transcription(self, audio) -> Dict[str, Any]:
        """Fallback offline transcription method.
        
        Args:
            audio: Audio data from speech_recognition
            
        Returns:
            Dictionary with transcription attempt
        """
        try:
            # Try offline sphinx recognition
            transcript = self.recognizer.recognize_sphinx(audio)
            return {
                'success': True,
                'transcript': transcript,
                'language': 'en-US',
                'offline': True,
                'confidence': 0.7
            }
        except Exception:
            return {
                'success': False,
                'error': 'Transcription failed. Please check your internet connection.',
                'transcript': ''
            }
    
    def validate_audio(self, audio_data: bytes) -> Dict[str, Any]:
        """Validate audio data before transcription.
        
        Args:
            audio_data: Audio data to validate
            
        Returns:
            Validation result
        """
        try:
            # Check size
            size_mb = len(audio_data) / (1024 * 1024)
            if size_mb > 10:
                return {
                    'valid': False,
                    'error': f'Audio file too large ({size_mb:.1f}MB). Maximum is 10MB.'
                }
            
            # Try to load as audio
            audio = AudioSegment.from_file(io.BytesIO(audio_data))
            duration = len(audio) / 1000.0
            
            if duration > self.max_duration:
                return {
                    'valid': False,
                    'error': f'Audio too long ({duration:.1f}s). Maximum is {self.max_duration}s.'
                }
            
            return {
                'valid': True,
                'duration': duration,
                'size_mb': size_mb
            }
            
        except Exception as e:
            return {
                'valid': False,
                'error': f'Invalid audio file: {str(e)}'
            }
