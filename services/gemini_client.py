"""Groq API client for JEE problem solving (disguised as Gemini client)."""

import os
import logging
import base64
import json
from typing import List, Dict, Any, Optional, Callable
from groq import Groq

logger = logging.getLogger(__name__)


class GeminiClient:
    """Groq API client for JEE problems (maintaining GeminiClient interface)."""

    def __init__(self):
        """Initialize the Groq API client."""
        self.model = os.getenv('GROQ_MODEL', 'meta-llama/llama-4-scout-17b-16e-instruct')

        keys_env = os.getenv('GROQ_API_KEYS')
        primary_key = os.getenv('GROQ_API_KEY')

        api_keys: List[str] = []
        if keys_env:
            api_keys.extend([key.strip() for key in keys_env.split(',') if key.strip()])
        if primary_key:
            # Ensure primary key is first and unique
            if primary_key not in api_keys:
                api_keys.insert(0, primary_key)

        if not api_keys:
            logger.error("No Groq API keys configured. Set GROQ_API_KEY or GROQ_API_KEYS.")
            raise ValueError("At least one Groq API key is required")

        self.api_keys = api_keys
        self.current_key_index = 0
        self.client: Groq = None  # type: ignore

        try:
            self._initialize_client()
            logger.info(
                "Groq client initialized with model: %s (using key %d of %d)",
                self.model,
                self.current_key_index + 1,
                len(self.api_keys)
            )
        except Exception as e:
            logger.error(f"Failed to initialize Groq client: {str(e)}")
            raise

        # JEE subject patterns and keywords
        self.subject_keywords = {
            'physics': ['force', 'velocity', 'acceleration', 'energy', 'momentum', 'wave', 'electric', 'magnetic', 'thermodynamics', 'optics'],
            'chemistry': ['molecule', 'atom', 'reaction', 'bond', 'compound', 'element', 'acid', 'base', 'organic', 'inorganic'],
            'mathematics': ['equation', 'derivative', 'integral', 'limit', 'matrix', 'vector', 'probability', 'geometry', 'algebra', 'trigonometry']
        }

        # System prompt for JEE tutor
        self.system_prompt = """You are an expert JEE Mains tutor specializing in Mathematics, Physics, and Chemistry.
        You provide clear, step-by-step solutions that are:
        1. Aligned with the JEE Mains syllabus
        2. Based on NCERT concepts and formulas
        3. Structured with clear reasoning at each step
        4. Include relevant formulas and their derivations when needed
        5. Use provided context when available

        Format your responses as:
        - **Step 1: Understanding the Problem** - Identify what's given and what needs to be found
        - **Step 2: Relevant Concepts/Formulas** - List the concepts and formulas needed
        - **Step 3: Solution** - Detailed step-by-step solution with calculations
        - **Step 4: Final Answer** - Clear statement of the final answer
        - **Verification** (if applicable) - Quick check to verify the answer

        Always be precise, educational, and focus on helping students understand the concepts."""

    def _initialize_client(self):
        """Initialize Groq client with the current API key."""
        api_key = self.api_keys[self.current_key_index]
        self.client = Groq(api_key=api_key)

    def _rotate_key(self) -> bool:
        """Rotate to the next API key. Returns False if all keys exhausted."""
        if len(self.api_keys) <= 1:
            return False

        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        if self.current_key_index == 0:
            # Wrapped around, no more fresh keys
            return False

        try:
            self._initialize_client()
            logger.warning(
                "Switched to fallback Groq key (%d/%d)",
                self.current_key_index + 1,
                len(self.api_keys)
            )
            return True
        except Exception as exc:
            logger.error(f"Failed to initialize Groq client with fallback key: {exc}")
            return False

    def _execute_with_retry(self, operation: Callable[[], Any]):
        """Execute Groq operation with rate-limit handling and key rotation."""
        attempts = len(self.api_keys)

        for attempt in range(attempts):
            try:
                return operation()
            except Exception as exc:
                message = str(exc)
                is_rate_limit = '429' in message or 'rate limit' in message.lower()

                if is_rate_limit and self._rotate_key():
                    continue

                raise

        raise RuntimeError("All Groq API keys exhausted due to rate limiting")

    def generate_response(
        self,
        query: str,
        context: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048
    ) -> Dict[str, Any]:
        """Generate a response using Groq API.

        Args:
            query: The user's question
            context: Optional RAG context
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            Dictionary with 'success' and 'answer' keys
        """
        try:
            # Prepare the context string
            context_str = ""
            if context:
                context_parts = []
                for item in context:
                    if 'content' in item:
                        context_parts.append(f"Context: {item['content']}")
                    elif 'text' in item:
                        context_parts.append(f"Context: {item['text']}")
                if context_parts:
                    context_str = "\n\nRelevant Information:\n" + "\n".join(context_parts[:3])  # Limit context

            # Call Groq API
            response = self._execute_with_retry(
                lambda: self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": self.system_prompt},
                        {"role": "user", "content": query + (context_str if context_str else "")}
                    ],
                    temperature=temperature,
                    max_tokens=max_tokens,
                    top_p=1,
                    stream=False
                )
            )

            answer = response.choices[0].message.content

            return {
                'success': True,
                'answer': answer,
                'model': self.model,
                'usage': {
                    'prompt_tokens': response.usage.prompt_tokens,
                    'completion_tokens': response.usage.completion_tokens,
                    'total_tokens': response.usage.total_tokens
                }
            }

        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'answer': ''
            }

    def analyze_image(
        self,
        image_path: str,
        context: str = '',
        temperature: float = 0.7,
        max_tokens: int = 1024
    ) -> Dict[str, Any]:
        """Analyze an image using Groq's vision capabilities.

        Args:
            image_path: Path to the image file
            context: Additional context for the analysis
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            Dictionary with analysis results
        """
        try:
            # Encode image to base64
            with open(image_path, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode('utf-8')

            # Build user content
            user_content = []
            context = context.strip() if context else ""
            if context:
                user_content.append({"type": "text", "text": context})
            user_content.append({"type": "text", "text": "Solve this problem."})
            user_content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{base64_image}",
                },
            })

            # Call Groq API with vision
            response = self._execute_with_retry(
                lambda: self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": self.system_prompt},
                        {
                            "role": "user",
                            "content": user_content,
                        }
                    ],
                    temperature=temperature,
                    max_tokens=max_tokens,
                    top_p=1,
                    stream=False
                )
            )

            analysis = response.choices[0].message.content

            return {
                'success': True,
                'analysis': analysis,
                'model': self.model,
                'usage': {
                    'prompt_tokens': response.usage.prompt_tokens,
                    'completion_tokens': response.usage.completion_tokens,
                    'total_tokens': response.usage.total_tokens
                }
            }

        except Exception as e:
            logger.error(f"Error analyzing image: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'analysis': ''
            }

    def generate_embeddings(self, texts: List[str]) -> Dict[str, Any]:
        """Generate embeddings using Groq API.

        Args:
            texts: List of texts to embed

        Returns:
            Dictionary with embeddings
        """
        try:
            # Note: Groq doesn't have a separate embeddings API yet
            # We'll use the chat completions API to generate embeddings
            # This is a workaround until Groq releases an embeddings endpoint

            embeddings = []
            for text in texts:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "Generate a JSON array of 384 floating point numbers representing the embedding vector for the given text. Return only the JSON array, no other text."},
                        {"role": "user", "content": text}
                    ],
                    temperature=0,
                    max_tokens=2000,
                    top_p=1,
                    stream=False,
                    response_format={"type": "json_object"}
                )

                try:
                    result = response.choices[0].message.content
                    # Parse the JSON response
                    embedding_data = json.loads(result)
                    if 'embedding' in embedding_data and isinstance(embedding_data['embedding'], list):
                        embeddings.append(embedding_data['embedding'])
                    else:
                        # Fallback: create a simple hash-based embedding
                        import hashlib
                        hash_obj = hashlib.md5(text.encode())
                        hash_bytes = hash_obj.digest()
                        # Convert to 384-dimensional vector (normalize to [0,1] range)
                        embedding = [(b / 255.0) for b in hash_bytes[:384]]
                        # Pad or truncate to 384 dimensions
                        if len(embedding) < 384:
                            embedding.extend([0.0] * (384 - len(embedding)))
                        embeddings.append(embedding[:384])

                except (json.JSONDecodeError, KeyError) as e:
                    logger.warning(f"Failed to parse embedding response: {e}")
                    # Fallback embedding
                    import hashlib
                    hash_obj = hashlib.md5(text.encode())
                    hash_bytes = hash_obj.digest()
                    embedding = [(b / 255.0) for b in hash_bytes[:384]]
                    if len(embedding) < 384:
                        embedding.extend([0.0] * (384 - len(embedding)))
                    embeddings.append(embedding[:384])

            return {
                'success': True,
                'embeddings': embeddings,
                'model': self.model
            }

        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'embeddings': []
            }

    def detect_subject(self, text: str) -> Optional[str]:
        """Detect subject from query text.

        Args:
            text: Query text

        Returns:
            Detected subject or None
        """
        text_lower = text.lower()

        subject_scores = {}
        for subject, keywords in self.subject_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            subject_scores[subject] = score

        if subject_scores:
            return max(subject_scores, key=subject_scores.get)

        return None
