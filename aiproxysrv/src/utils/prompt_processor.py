"""Prompt template processing utilities with fallback logic"""
import logging
from typing import Optional, Dict, Any
from db.models import PromptTemplate

# Configure logger
logger = logging.getLogger(__name__)

# Default values for fallback
DEFAULT_MODEL = "llama3.2:3b"
DEFAULT_TEMPERATURE = 0.7
DEFAULT_MAX_TOKENS = 2048

class PromptProcessor:
    """Utility class for processing prompt templates with fallback logic"""

    @staticmethod
    def resolve_ai_parameters(template: PromptTemplate) -> Dict[str, Any]:
        """
        Resolve AI parameters for a template with fallback to defaults.
        Logs which values are used for transparency.

        Args:
            template: PromptTemplate instance

        Returns:
            Dict with resolved model, temperature, and max_tokens
        """
        resolved_params = {}

        # Resolve model
        if template.model and template.model.strip():
            resolved_params['model'] = template.model
            logger.info(f"Using template model: {template.model} (template_id={template.id})")
        else:
            resolved_params['model'] = DEFAULT_MODEL
            logger.info(f"Using default model: {DEFAULT_MODEL} (template_id={template.id}, template_model=empty)")

        # Resolve temperature
        if template.temperature is not None:
            resolved_params['temperature'] = template.temperature
            logger.info(f"Using template temperature: {template.temperature} (template_id={template.id})")
        else:
            resolved_params['temperature'] = DEFAULT_TEMPERATURE
            logger.info(f"Using default temperature: {DEFAULT_TEMPERATURE} (template_id={template.id}, template_temperature=null)")

        # Resolve max_tokens
        if template.max_tokens is not None:
            resolved_params['max_tokens'] = template.max_tokens
            logger.info(f"Using template max_tokens: {template.max_tokens} (template_id={template.id})")
        else:
            resolved_params['max_tokens'] = DEFAULT_MAX_TOKENS
            logger.info(f"Using default max_tokens: {DEFAULT_MAX_TOKENS} (template_id={template.id}, template_max_tokens=null)")

        return resolved_params

    @staticmethod
    def build_prompt(template: PromptTemplate, user_input: str) -> str:
        """
        Build complete prompt from template and user input.

        Args:
            template: PromptTemplate instance
            user_input: User's input text

        Returns:
            Complete prompt string
        """
        pre_condition = template.pre_condition or ""
        post_condition = template.post_condition or ""

        # Build the complete prompt
        complete_prompt = f"{pre_condition}\n\n{user_input}\n\n{post_condition}".strip()

        logger.info(f"Built prompt for template {template.id} (category={template.category}, action={template.action})")

        return complete_prompt

    @staticmethod
    def process_template(template: PromptTemplate, user_input: str) -> Dict[str, Any]:
        """
        Complete template processing: resolve AI parameters and build prompt.

        Args:
            template: PromptTemplate instance
            user_input: User's input text

        Returns:
            Dict with 'prompt', 'model', 'temperature', 'max_tokens'
        """
        # Resolve AI parameters
        ai_params = PromptProcessor.resolve_ai_parameters(template)

        # Build prompt
        prompt = PromptProcessor.build_prompt(template, user_input)

        # Combine everything
        result = {
            'prompt': prompt,
            **ai_params
        }

        logger.info(f"Processed template {template.id}: model={result['model']}, "
                   f"temperature={result['temperature']}, max_tokens={result['max_tokens']}")

        return result