"""Multi-Model Gemini AI Service for Resume Operations.

This service intelligently uses multiple Gemini models for different tasks:
- gemini-2.0-flash-exp: Latest experimental model for complex generation
- gemini-1.5-flash: Stable model for refinement and variations
- gemini-1.5-flash-8b: Fast model for quick operations

Features automatic fallback, rate limiting, and error handling.
"""
import os
import json
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

logger = logging.getLogger(__name__)


class MultiModelAI:
    """Manages multiple Gemini AI models with intelligent routing and fallback."""

    # Model configurations (ordered by capability/preference)
    MODELS = {
        'generation': [
            'gemini-2.0-flash-exp',      # Latest experimental - best for complex generation
            'gemini-1.5-flash',          # Stable fallback
            'gemini-1.5-pro',            # Most capable (if available)
        ],
        'refinement': [
            'gemini-1.5-flash',          # Fast and accurate for refinement
            'gemini-2.0-flash-exp',      # Fallback to experimental
            'gemini-1.5-flash-8b',       # Lightweight fallback
        ],
        'variation': [
            'gemini-1.5-flash',          # Good balance for variations
            'gemini-2.0-flash-exp',      # Fallback
            'gemini-1.5-flash-8b',       # Fast fallback
        ],
        'analysis': [
            'gemini-1.5-flash-8b',       # Fast for simple analysis
            'gemini-1.5-flash',          # Fallback
        ]
    }

    def __init__(self):
        """Initialize multi-model AI service."""
        api_key = os.getenv('GOOGLE_GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')

        if not api_key:
            raise ValueError("GOOGLE_GEMINI_API_KEY environment variable not set")

        genai.configure(api_key=api_key)

        # Test available models
        self.available_models = self._discover_available_models()
        logger.info(f"Available Gemini models: {self.available_models}")

        # Safety settings for all models
        self.safety_settings = {
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }

        # Generation config
        self.generation_config = {
            'temperature': 0.7,
            'top_p': 0.95,
            'top_k': 40,
            'max_output_tokens': 8192,
        }

    def _discover_available_models(self) -> List[str]:
        """Discover which Gemini models are available."""
        try:
            available = []
            for model in genai.list_models():
                if 'generateContent' in model.supported_generation_methods:
                    model_name = model.name.replace('models/', '')
                    available.append(model_name)
            return available
        except Exception as e:
            logger.error(f"Failed to discover models: {e}")
            # Return default models as fallback
            return ['gemini-1.5-flash', 'gemini-2.0-flash-exp', 'gemini-1.5-flash-8b']

    def _get_best_model(self, task_type: str) -> Optional[str]:
        """Get the best available model for a specific task."""
        preferred_models = self.MODELS.get(task_type, self.MODELS['refinement'])

        for model_name in preferred_models:
            if model_name in self.available_models:
                logger.info(f"Selected model '{model_name}' for task '{task_type}'")
                return model_name

        # Ultimate fallback
        if self.available_models:
            fallback = self.available_models[0]
            logger.warning(f"No preferred model available for '{task_type}', using fallback: {fallback}")
            return fallback

        raise RuntimeError("No Gemini models available")

    def _create_model(self, model_name: str) -> genai.GenerativeModel:
        """Create a GenerativeModel instance with proper configuration."""
        return genai.GenerativeModel(
            model_name=model_name,
            safety_settings=self.safety_settings,
            generation_config=self.generation_config
        )

    def generate_content(
        self,
        prompt: str,
        task_type: str = 'generation',
        temperature: Optional[float] = None,
        max_retries: int = 3
    ) -> Tuple[str, str]:
        """
        Generate content using the best available model with automatic fallback.

        Args:
            prompt: The prompt to send to the model
            task_type: Type of task (generation, refinement, variation, analysis)
            temperature: Optional temperature override
            max_retries: Maximum retry attempts

        Returns:
            Tuple of (generated_text, model_used)
        """
        preferred_models = self.MODELS.get(task_type, self.MODELS['refinement'])

        # Override temperature if specified
        if temperature is not None:
            generation_config = self.generation_config.copy()
            generation_config['temperature'] = temperature
        else:
            generation_config = self.generation_config

        last_error = None

        for model_name in preferred_models:
            if model_name not in self.available_models:
                continue

            for attempt in range(max_retries):
                try:
                    logger.info(f"Attempting {task_type} with model {model_name} (attempt {attempt + 1}/{max_retries})")

                    model = genai.GenerativeModel(
                        model_name=model_name,
                        safety_settings=self.safety_settings,
                        generation_config=generation_config
                    )

                    response = model.generate_content(prompt)

                    if response.text:
                        logger.info(f"Successfully generated content with {model_name}")
                        return response.text, model_name
                    else:
                        logger.warning(f"Empty response from {model_name}")

                except Exception as e:
                    last_error = e
                    logger.warning(f"Error with {model_name} (attempt {attempt + 1}): {str(e)}")

                    # Don't retry on certain errors
                    if "quota" in str(e).lower() or "api key" in str(e).lower():
                        break

        # All models failed
        error_msg = f"All models failed for task '{task_type}'. Last error: {last_error}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)

    def generate_structured_json(
        self,
        prompt: str,
        task_type: str = 'generation',
        expected_keys: Optional[List[str]] = None
    ) -> Tuple[Dict, str]:
        """
        Generate structured JSON output with validation.

        Args:
            prompt: Prompt that should return JSON
            task_type: Type of task
            expected_keys: Optional list of keys that must be in the JSON

        Returns:
            Tuple of (parsed_json_dict, model_used)
        """
        text, model_used = self.generate_content(prompt, task_type)

        # Clean the response to extract JSON
        json_text = self._extract_json_from_text(text)

        try:
            data = json.loads(json_text)

            # Validate expected keys if provided
            if expected_keys:
                missing_keys = [key for key in expected_keys if key not in data]
                if missing_keys:
                    logger.warning(f"Missing expected keys: {missing_keys}")

            return data, model_used

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from model output: {e}")
            logger.error(f"Raw text: {text[:500]}...")
            raise ValueError(f"Model returned invalid JSON: {str(e)}")

    def _extract_json_from_text(self, text: str) -> str:
        """Extract JSON from text that may contain markdown code blocks or extra text."""
        # Remove markdown code blocks
        text = text.strip()

        # Remove ```json and ``` markers
        if text.startswith('```'):
            lines = text.split('\n')
            # Remove first line if it's ```json or ```
            if lines[0].strip().startswith('```'):
                lines = lines[1:]
            # Remove last line if it's ```
            if lines and lines[-1].strip() == '```':
                lines = lines[:-1]
            text = '\n'.join(lines)

        # Find JSON object boundaries
        start_idx = text.find('{')
        end_idx = text.rfind('}')

        if start_idx != -1 and end_idx != -1:
            text = text[start_idx:end_idx + 1]

        return text.strip()

    def get_model_info(self, task_type: str) -> Dict:
        """Get information about which model would be used for a task."""
        model_name = self._get_best_model(task_type)

        return {
            'taskType': task_type,
            'selectedModel': model_name,
            'availableModels': self.available_models,
            'preferredModels': self.MODELS.get(task_type, [])
        }

    def health_check(self) -> Dict:
        """Check health of all available models."""
        health_status = {
            'timestamp': datetime.utcnow().isoformat(),
            'apiKeyConfigured': bool(os.getenv('GOOGLE_GEMINI_API_KEY')),
            'availableModels': self.available_models,
            'modelTests': {}
        }

        # Test each available model with a simple prompt
        test_prompt = "Say 'OK' if you can read this."

        for model_name in self.available_models[:3]:  # Test first 3 to save quota
            try:
                model = self._create_model(model_name)
                response = model.generate_content(test_prompt)

                health_status['modelTests'][model_name] = {
                    'status': 'healthy',
                    'responseLength': len(response.text) if response.text else 0,
                    'timestamp': datetime.utcnow().isoformat()
                }
            except Exception as e:
                health_status['modelTests'][model_name] = {
                    'status': 'unhealthy',
                    'error': str(e),
                    'timestamp': datetime.utcnow().isoformat()
                }

        health_status['overallStatus'] = 'healthy' if len(self.available_models) > 0 else 'unhealthy'

        return health_status


# Global singleton instance
_ai_instance = None


def get_ai_service() -> MultiModelAI:
    """Get or create the global AI service instance."""
    global _ai_instance
    if _ai_instance is None:
        _ai_instance = MultiModelAI()
    return _ai_instance
