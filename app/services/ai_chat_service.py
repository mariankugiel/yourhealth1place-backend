import logging
from typing import List, Dict, Any, Optional

from app.core.config import settings

# Try to import OpenAI, fallback if not available
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logging.warning("OpenAI package not installed. AI Chat service will use fallback mode.")

logger = logging.getLogger(__name__)


class AIChatService:
    """Service for handling AI chat conversations with Saluso Support"""
    
    def __init__(self):
        """Initialize the AI Chat Service with OpenAI client"""
        if OPENAI_AVAILABLE and settings.OPENAI_API_KEY:
            try:
                self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
                self.model = "gpt-4o-mini"  # Using GPT-4o-mini for cost efficiency
                self.openai_enabled = True
            except Exception as e:
                logging.error(f"Failed to initialize OpenAI client: {e}")
                self.client = None
                self.model = None
                self.openai_enabled = False
        else:
            self.client = None
            self.model = None
            self.openai_enabled = False
            logging.warning("OpenAI not available. AI Chat service will use fallback mode.")
    
    def generate_chat_response(
        self,
        user_message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """
        Generate AI chat response using OpenAI
        
        Args:
            user_message: The user's message
            conversation_history: Optional list of previous messages in format:
                [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
        
        Returns:
            AI response string
        """
        if not self.openai_enabled or not self.client:
            logger.warning("OpenAI not available. Returning fallback response.")
            return "I'm sorry, but the AI chat service is currently unavailable. Please try again later or contact support."
        
        if not user_message or not user_message.strip():
            return "I'm here to help! Please let me know what you need assistance with."
        
        try:
            # Build messages array for OpenAI
            messages = []
            
            # System prompt for Saluso Support
            system_prompt = (
                "You are Saluso Support, a helpful and friendly support assistant for the Saluso health platform. "
                "Your role is to help users with questions about:\n"
                "- Health records and medical information\n"
                "- Appointments and scheduling\n"
                "- Medications and prescriptions\n"
                "- Lab results and test reports\n"
                "- General platform usage and features\n"
                "- Account and profile management\n\n"
                "Be concise, clear, and empathetic. If you cannot answer a question or it requires medical advice, "
                "direct users to contact their healthcare provider or use the appropriate platform features. "
                "Always maintain a professional and supportive tone."
            )
            
            messages.append({
                "role": "system",
                "content": system_prompt
            })
            
            # Add conversation history if provided (last 20 messages to stay within token limits)
            if conversation_history:
                # Take last 20 messages to manage token usage
                recent_history = conversation_history[-20:] if len(conversation_history) > 20 else conversation_history
                messages.extend(recent_history)
            
            # Add current user message
            messages.append({
                "role": "user",
                "content": user_message.strip()
            })
            
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,  # Balanced creativity
                max_tokens=500,  # Reasonable response length
            )
            
            ai_response = response.choices[0].message.content.strip()
            
            if not ai_response:
                logger.warning("OpenAI returned empty response")
                return "I apologize, but I didn't receive a proper response. Could you please rephrase your question?"
            
            logger.info(f"✅ [AI Chat] Successfully generated response (tokens: {response.usage.total_tokens if response.usage else 'unknown'})")
            return ai_response
            
        except Exception as e:
            logger.error(f"❌ [AI Chat] Failed to generate response: {e}", exc_info=True)
            return "I'm sorry, I encountered an error while processing your message. Please try again in a moment."
    
    def is_available(self) -> bool:
        """Check if AI chat service is available"""
        return self.openai_enabled and self.client is not None


# Create singleton instance
ai_chat_service = AIChatService()

