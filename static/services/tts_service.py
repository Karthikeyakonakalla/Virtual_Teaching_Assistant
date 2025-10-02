"""Text-to-Speech service for audio output."""

import os
import io
import logging
import base64
from typing import Dict, Any, Optional
import pyttsx3
from gtts import gTTS

logger = logging.getLogger(__name__)


class TTSService:
    """Service for converting text to speech."""
    
    def __init__(self):
        """Initialize the TTS service."""
        # Try to initialize offline TTS engine
        try:
            self.offline_engine = pyttsx3.init()
            self._configure_offline_engine()
            self.offline_available = True
        except Exception as e:
            logger.warning(f"Offline TTS not available: {str(e)}")
            self.offline_engine = None
            self.offline_available = False
    
    def _configure_offline_engine(self):
        """Configure the offline TTS engine."""
        if not self.offline_engine:
            return
        
        # Set properties
        self.offline_engine.setProperty('rate', 150)  # Speed
        self.offline_engine.setProperty('volume', 0.9)  # Volume
        
        # Try to set Indian English voice if available
        voices = self.offline_engine.getProperty('voices')
        for voice in voices:
            if 'india' in voice.name.lower() or 'en_IN' in voice.id:
                self.offline_engine.setProperty('voice', voice.id)
                break
    
    def synthesize_speech(
        self,
        text: str,
        language: str = 'en-in',
        speed: float = 1.0,
        use_offline: bool = False
    ) -> Dict[str, Any]:
        """Convert text to speech.
        
        Args:
            text: Text to convert
            language: Language code
            speed: Speech speed (1.0 is normal)
            use_offline: Use offline engine if available
            
        Returns:
            Dictionary containing audio data and metadata
        """
        try:
            # Clean text for better speech
            cleaned_text = self._clean_text_for_speech(text)
            
            if use_offline and self.offline_available:
                return self._offline_synthesis(cleaned_text, speed)
            else:
                return self._online_synthesis(cleaned_text, language, speed)
            
        except Exception as e:
            logger.error(f"Error synthesizing speech: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'audio_data': None
            }
    
    def _online_synthesis(
        self,
        text: str,
        language: str = 'en-in',
        speed: float = 1.0
    ) -> Dict[str, Any]:
        """Synthesize speech using gTTS (Google TTS).
        
        Args:
            text: Text to convert
            language: Language code
            speed: Speech speed
            
        Returns:
            Dictionary with audio data
        """
        try:
            # Map language codes
            lang_map = {
                'en-in': 'en',  # gTTS uses 'en' with Indian accent
                'en-us': 'en',
                'hi': 'hi'
            }
            gtts_lang = lang_map.get(language.lower(), 'en')
            
            # Create gTTS object
            tts = gTTS(
                text=text,
                lang=gtts_lang,
                slow=(speed < 1.0),
                tld='co.in' if 'in' in language.lower() else 'com'
            )
            
            # Save to bytes
            audio_buffer = io.BytesIO()
            tts.write_to_fp(audio_buffer)
            audio_data = audio_buffer.getvalue()
            
            # Convert to base64 for easy transmission
            audio_b64 = base64.b64encode(audio_data).decode('utf-8')
            
            return {
                'success': True,
                'audio_data': audio_data,
                'audio_base64': audio_b64,
                'format': 'mp3',
                'language': language,
                'engine': 'gTTS'
            }
            
        except Exception as e:
            logger.error(f"Online TTS failed: {str(e)}")
            # Try offline as fallback
            if self.offline_available:
                return self._offline_synthesis(text, speed)
            raise
    
    def _offline_synthesis(self, text: str, speed: float = 1.0) -> Dict[str, Any]:
        """Synthesize speech using offline engine.
        
        Args:
            text: Text to convert
            speed: Speech speed
            
        Returns:
            Dictionary with audio data
        """
        if not self.offline_available:
            return {
                'success': False,
                'error': 'Offline TTS not available',
                'audio_data': None
            }
        
        try:
            # Set speed
            current_rate = self.offline_engine.getProperty('rate')
            self.offline_engine.setProperty('rate', int(current_rate * speed))
            
            # Save to file
            temp_file = 'temp_audio.mp3'
            self.offline_engine.save_to_file(text, temp_file)
            self.offline_engine.runAndWait()
            
            # Read audio data
            with open(temp_file, 'rb') as f:
                audio_data = f.read()
            
            # Clean up
            os.remove(temp_file)
            
            # Convert to base64
            audio_b64 = base64.b64encode(audio_data).decode('utf-8')
            
            return {
                'success': True,
                'audio_data': audio_data,
                'audio_base64': audio_b64,
                'format': 'mp3',
                'engine': 'pyttsx3'
            }
            
        except Exception as e:
            logger.error(f"Offline TTS failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'audio_data': None
            }
    
    def _clean_text_for_speech(self, text: str) -> str:
        """Clean text for better speech synthesis.
        
        Args:
            text: Original text
            
        Returns:
            Cleaned text
        """
        import re
        
        # Remove LaTeX math expressions and replace with readable text
        text = re.sub(r'\$\$([^$]+)\$\$', r'[Mathematical expression: \1]', text)
        text = re.sub(r'\$([^$]+)\$', r'\1', text)
        
        # Replace common math symbols
        replacements = {
            '\\alpha': 'alpha',
            '\\beta': 'beta',
            '\\gamma': 'gamma',
            '\\delta': 'delta',
            '\\theta': 'theta',
            '\\pi': 'pi',
            '\\sigma': 'sigma',
            '\\mu': 'mu',
            '\\lambda': 'lambda',
            '\\omega': 'omega',
            '\\infty': 'infinity',
            '\\rightarrow': 'gives',
            '\\leftarrow': 'from',
            '\\Rightarrow': 'implies',
            '\\Leftarrow': 'implied by',
            '\\leftrightarrow': 'if and only if',
            '\\approx': 'approximately equals',
            '\\neq': 'not equal to',
            '\\leq': 'less than or equal to',
            '\\geq': 'greater than or equal to',
            '\\times': 'times',
            '\\div': 'divided by',
            '\\pm': 'plus or minus',
            '\\mp': 'minus or plus',
            '\\sqrt': 'square root of',
            '\\sum': 'sum of',
            '\\int': 'integral of',
            '\\partial': 'partial derivative',
            '^2': ' squared',
            '^3': ' cubed',
            '_': ' subscript ',
            '^': ' to the power of '
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        # Clean up multiple spaces
        text = re.sub(r'\s+', ' ', text)
        
        # Add pauses for better readability
        text = text.replace('.', '. ')
        text = text.replace(',', ', ')
        text = text.replace(':', ': ')
        text = text.replace(';', '; ')
        
        # Handle step markers
        text = re.sub(r'\*\*Step (\d+)', r'Step \1.', text)
        text = text.replace('**', '')
        
        return text.strip()
    
    def batch_synthesize(
        self,
        texts: list,
        language: str = 'en-in'
    ) -> list:
        """Synthesize multiple texts.
        
        Args:
            texts: List of texts to convert
            language: Language code
            
        Returns:
            List of audio results
        """
        results = []
        
        for text in texts:
            result = self.synthesize_speech(text, language)
            results.append(result)
        
        return results
    
    def save_audio(self, audio_data: bytes, file_path: str):
        """Save audio data to file.
        
        Args:
            audio_data: Audio data bytes
            file_path: Path to save file
        """
        try:
            with open(file_path, 'wb') as f:
                f.write(audio_data)
            
            logger.info(f"Audio saved to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving audio: {str(e)}")
            return False
    
    def get_available_voices(self) -> list:
        """Get list of available voices.
        
        Returns:
            List of voice options
        """
        voices = []
        
        # Online voices (gTTS languages)
        voices.extend([
            {'id': 'en-in', 'name': 'English (India)', 'engine': 'gTTS'},
            {'id': 'en-us', 'name': 'English (US)', 'engine': 'gTTS'},
            {'id': 'hi', 'name': 'Hindi', 'engine': 'gTTS'}
        ])
        
        # Offline voices
        if self.offline_available and self.offline_engine:
            for voice in self.offline_engine.getProperty('voices'):
                voices.append({
                    'id': voice.id,
                    'name': voice.name,
                    'engine': 'pyttsx3'
                })
        
        return voices
