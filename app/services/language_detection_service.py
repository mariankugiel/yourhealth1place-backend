"""
Language Detection Service using OpenAI

Detects the language of document text using OpenAI API.
Provides fallback mechanisms for edge cases.
"""
import logging
from typing import Optional
from app.core.config import settings

# Try to import OpenAI, fallback if not available
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logging.warning("OpenAI package not installed. Language detection will use fallback mode.")

logger = logging.getLogger(__name__)


def detect_document_language(
    text: str, 
    fallback: str = 'en'
) -> str:
    """
    Detect language from document text using OpenAI API.
    
    Args:
        text: Document text (should be at least 50-100 characters for accuracy)
        fallback: Language code to use if detection fails. Default: 'en'
    
    Returns:
        Language code (e.g., 'pt', 'en', 'es', 'fr', 'de', etc.)
    
    Examples:
        >>> detect_document_language("Este é um documento em português")
        'pt'
        >>> detect_document_language("This is an English document")
        'en'
        >>> detect_document_language("Este documento es en español")
        'es'
    """
    print(f"[LANGUAGE DETECTION] Starting language detection. Text length: {len(text) if text else 0} chars")
    
    if not text or len(text.strip()) < 20:
        print(f"[LANGUAGE DETECTION] Text too short ({len(text) if text else 0} chars). Using fallback: {fallback}")
        logger.warning(
            f"Text too short for reliable language detection ({len(text) if text else 0} chars). "
            f"Using fallback: {fallback}"
        )
        return fallback
    
    if not OPENAI_AVAILABLE or not settings.OPENAI_API_KEY:
        print(f"[LANGUAGE DETECTION] ✗ OpenAI not available. Using fallback: {fallback}")
        logger.warning("OpenAI not available for language detection. Using fallback.")
        return fallback
    
    try:
        # Initialize OpenAI client
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        model = "gpt-4o-mini"  # Cost-efficient model
        
        # Use first 2000 characters for faster processing and cost efficiency
        sample_text = text[:2000] if len(text) > 2000 else text
        
        # Clean text: remove excessive whitespace but keep structure
        sample_text = ' '.join(sample_text.split())
        
        print(f"[LANGUAGE DETECTION] Analyzing sample text ({len(sample_text)} chars) with OpenAI")
        
        # Use OpenAI to detect language
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a language detection expert. Analyze the provided text and identify its language. Return ONLY the ISO 639-1 language code (e.g., 'en', 'pt', 'es', 'fr', 'de', etc.). Do not include any explanation or additional text."
                },
                {
                    "role": "user",
                    "content": f"Detect the language of this text and return only the ISO 639-1 language code:\n\n{sample_text}"
                }
            ],
            temperature=0.1,  # Low temperature for consistent results
            max_tokens=10  # Only need language code
        )
        
        detected_language = response.choices[0].message.content.strip().lower()
        
        # Validate language code (should be 2 characters)
        if len(detected_language) == 2 and detected_language.isalpha():
            print(f"[LANGUAGE DETECTION] ✓ Detected language: {detected_language}")
            logger.info(f"Detected language: {detected_language}")
            return detected_language
        else:
            print(f"[LANGUAGE DETECTION] ✗ Invalid language code returned: {detected_language}. Using fallback: {fallback}")
            logger.warning(f"Invalid language code from OpenAI: {detected_language}. Using fallback: {fallback}")
            return fallback
            
    except Exception as e:
        print(f"[LANGUAGE DETECTION] ✗ Detection error: {e}. Using fallback: {fallback}")
        logger.error(f"Language detection error: {e}. Using fallback: {fallback}", exc_info=True)
        return fallback
