import json
import logging
import google.generativeai as genai
from dataclasses import dataclass
from bot.config import config

logger = logging.getLogger(__name__)

@dataclass
class CensorResult:
    is_harmful: bool
    category: str
    confidence: float
    reason: str

class AICensor:
    def __init__(self):
        if config.GEMINI_API_KEY:
            genai.configure(api_key=config.GEMINI_API_KEY)
            self.model = genai.GenerativeModel('gemini-2.0-flash')
        else:
            self.model = None

    async def analyze_message(self, text: str, context: list[str] = None) -> CensorResult:
        if not self.model:
            return CensorResult(is_harmful=False, category="ok", confidence=1.0, reason="AI not configured")

        prompt = f"""
        Analyze the following message and determine its category.
        Strictly output valid JSON only, in this format: {{"category": "...", "confidence": 0.0-1.0, "reason": "..."}}
        Categories: spam, scam, adult, ads, ok.
        Context (previous messages): {context or []}
        Message: "{text}"
        """
        try:
            response = await self.model.generate_content_async(prompt)
            # Remove markdown formatting if present
            response_text = response.text.strip().removeprefix("```json").removesuffix("```").strip()
            data = json.loads(response_text)
            
            category = data.get("category", "ok").lower()
            confidence = float(data.get("confidence", 0.0))
            reason = data.get("reason", "")
            
            is_harmful = category in ["spam", "scam", "adult", "ads"]
            
            return CensorResult(is_harmful=is_harmful, category=category, confidence=confidence, reason=reason)
        except Exception as e:
            logger.error(f"Error in AICensor: {e}")
            return CensorResult(is_harmful=False, category="ok", confidence=0.0, reason=f"Error: {str(e)}")

ai_censor = AICensor()
