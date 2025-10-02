"""OCR service for extracting text from images."""

import os
import logging
import base64
from typing import Dict, Any, Optional
import cv2
import numpy as np
from groq import Groq

logger = logging.getLogger(__name__)


class OCRService:
    """Service for performing OCR on images containing JEE problems."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the OCR service."""
        self.api_key = api_key or os.getenv('GROQ_API_KEY')
        if not self.api_key:
            raise ValueError("GROQ_API_KEY not provided")
        
        self.client = Groq(api_key=self.api_key)
        self.model = os.getenv('GROQ_MODEL', 'meta-llama/llama-4-scout-17b-16e-instruct')
    
    def extract_text(self, image_path: str) -> Dict[str, Any]:
        """Extract text from an image using Groq Vision.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Dictionary containing extracted text and metadata
        """
        try:
            # Preprocess the image
            processed_path = self._preprocess_image(image_path)
            
            # Encode image to base64
            with open(processed_path, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode('utf-8')
            
            # Build OCR prompt
            prompt = """Extract ALL text from this image, including:
            1. Mathematical equations and expressions (convert to LaTeX format)
            2. Chemical formulas and reactions
            3. Diagrams labels and annotations
            4. Question text and options (if multiple choice)
            5. Any tables or structured data
            
            Format the output as:
            - Main Question Text
            - Mathematical Expressions (in LaTeX)
            - Chemical Formulas (if any)
            - Diagram descriptions (if any)
            - Answer options (if multiple choice)
            
            Be extremely accurate with numbers, symbols, and notation."""
            
            # Generate response using Groq
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}",
                                },
                            },
                        ],
                    }
                ],
                temperature=0.3,
                max_tokens=2048,
            )
            
            # Parse the extracted text
            extracted = self._parse_extracted_text(response.choices[0].message.content)
            
            # Clean up temporary file if created
            if processed_path != image_path and os.path.exists(processed_path):
                os.remove(processed_path)
            
            return {
                'success': True,
                'extracted_text': extracted['text'],
                'latex_expressions': extracted['latex'],
                'chemical_formulas': extracted['chemicals'],
                'has_diagram': extracted['has_diagram'],
                'question_type': extracted['question_type'],
                'raw_text': response.choices[0].message.content
            }
            
        except Exception as e:
            logger.error(f"Error extracting text from image: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'extracted_text': '',
                'latex_expressions': [],
                'chemical_formulas': []
            }
    
    def _preprocess_image(self, image_path: str) -> str:
        """Preprocess image to improve OCR accuracy.
        
        Args:
            image_path: Path to the original image
            
        Returns:
            Path to the processed image
        """
        try:
            # Read the image
            img = cv2.imread(image_path)
            
            # Convert to grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Apply denoising
            denoised = cv2.fastNlMeansDenoising(gray)
            
            # Apply adaptive thresholding for better contrast
            thresh = cv2.adaptiveThreshold(
                denoised, 255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY,
                11, 2
            )
            
            # Deskew if needed
            angle = self._get_skew_angle(thresh)
            if abs(angle) > 0.5:
                thresh = self._rotate_image(thresh, angle)
            
            # Save processed image
            processed_path = image_path.replace('.', '_processed.')
            cv2.imwrite(processed_path, thresh)
            
            return processed_path
            
        except Exception as e:
            logger.warning(f"Image preprocessing failed: {str(e)}. Using original image.")
            return image_path
    
    def _get_skew_angle(self, image: np.ndarray) -> float:
        """Detect skew angle in the image.
        
        Args:
            image: Input image array
            
        Returns:
            Skew angle in degrees
        """
        try:
            # Find all contours
            contours, _ = cv2.findContours(
                image, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE
            )
            
            # Find minimum area rectangle for all contours
            all_points = []
            for contour in contours:
                all_points.extend(contour.reshape(-1, 2).tolist())
            
            if len(all_points) < 5:
                return 0.0
            
            all_points = np.array(all_points)
            rect = cv2.minAreaRect(all_points)
            angle = rect[2]
            
            # Adjust angle
            if angle < -45:
                angle = -(90 + angle)
            else:
                angle = -angle
            
            return angle
            
        except Exception:
            return 0.0
    
    def _rotate_image(self, image: np.ndarray, angle: float) -> np.ndarray:
        """Rotate image by given angle.
        
        Args:
            image: Input image array
            angle: Rotation angle in degrees
            
        Returns:
            Rotated image
        """
        h, w = image.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(
            image, M, (w, h),
            flags=cv2.INTER_CUBIC,
            borderMode=cv2.BORDER_REPLICATE
        )
        return rotated
    
    def _parse_extracted_text(self, raw_text: str) -> Dict[str, Any]:
        """Parse the raw extracted text into structured format.
        
        Args:
            raw_text: Raw text from OCR
            
        Returns:
            Structured dictionary with parsed content
        """
        import re
        
        result = {
            'text': raw_text,
            'latex': [],
            'chemicals': [],
            'has_diagram': False,
            'question_type': 'descriptive'
        }
        
        # Extract LaTeX expressions
        latex_pattern = r'\$([^$]+)\$|\$\$([^$]+)\$\$'
        latex_matches = re.findall(latex_pattern, raw_text)
        result['latex'] = [m[0] or m[1] for m in latex_matches]
        
        # Extract chemical formulas
        chem_pattern = r'[A-Z][a-z]?\d*(?:\([^)]+\)\d*)?(?:[+-]\d*)?'
        chem_matches = re.findall(chem_pattern, raw_text)
        result['chemicals'] = [m for m in chem_matches if len(m) > 1]
        
        # Check for diagram mentions
        diagram_keywords = ['diagram', 'figure', 'graph', 'circuit', 'structure']
        result['has_diagram'] = any(keyword in raw_text.lower() for keyword in diagram_keywords)
        
        # Detect question type
        if re.search(r'\(a\)|\(A\)|option|choose', raw_text, re.IGNORECASE):
            result['question_type'] = 'multiple_choice'
        elif re.search(r'true\s+or\s+false|T/F', raw_text, re.IGNORECASE):
            result['question_type'] = 'true_false'
        elif re.search(r'fill\s+in\s+the\s+blank|complete', raw_text, re.IGNORECASE):
            result['question_type'] = 'fill_blank'
        
        return result
    
    def extract_handwriting(self, image_path: str) -> Dict[str, Any]:
        """Specialized extraction for handwritten content.
        
        Args:
            image_path: Path to the handwritten image
            
        Returns:
            Dictionary containing extracted handwritten text
        """
        try:
            # Encode image to base64
            with open(image_path, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode('utf-8')
            
            # Specific prompt for handwriting
            prompt = """This image contains handwritten text, possibly including:
            - Mathematical equations
            - Chemical formulas
            - Rough work or calculations
            - Diagrams or sketches
            
            Please extract all handwritten content accurately, paying special attention to:
            1. Mathematical symbols and notation
            2. Subscripts and superscripts
            3. Fractions and complex expressions
            4. Any corrections or strikethroughs
            
            Convert mathematical expressions to LaTeX format."""
            
            # Generate response using Groq
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}",
                                },
                            },
                        ],
                    }
                ],
                temperature=0.3,
                max_tokens=2048,
            )
            
            return {
                'success': True,
                'handwritten_text': response.choices[0].message.content,
                'confidence': 0.85  # Placeholder confidence score
            }
            
        except Exception as e:
            logger.error(f"Error extracting handwriting: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'handwritten_text': ''
            }
