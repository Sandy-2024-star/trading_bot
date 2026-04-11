"""
Advanced News Reasoning using Local LLM (Ollama via LiteLLM).
Provides reasoned sentiment analysis beyond simple keyword matching.
"""

import json
import asyncio
from typing import Dict, List, Optional
from loguru import logger
from litellm import completion
from config.config import config

class NewsReasoner:
    """
    Uses a local LLM to analyze news impact and explain reasoning.
    """

    def __init__(self, model: str = "ollama/qwen-coder-3b"):
        self.model = config.LOCAL_LLM_MODEL if "ollama" in config.LOCAL_LLM_MODEL else f"ollama/{config.LOCAL_LLM_MODEL}"
        self.api_base = config.LOCAL_LLM_BASE_URL
        self.enabled = config.LOCAL_LLM_ENABLED

    async def analyze_news(self, headlines: List[str]) -> Dict:
        """
        Analyze a list of headlines and return sentiment + reasoning.
        """
        if not self.enabled or not headlines:
            return {"score": 0.0, "label": "NEUTRAL", "reason": "LLM Reasoning disabled or no headlines"}

        prompt = f"""
        Analyze the following financial news headlines and determine the overall market sentiment.
        Provide a sentiment score between -1.0 (extremely bearish) and 1.0 (extremely bullish).
        Also provide a short explanation (1-2 sentences) of your reasoning.

        Headlines:
        {chr(10).join([f"- {h}" for h in headlines])}

        Return ONLY a JSON object in this format:
        {{
            "score": float,
            "label": "BULLISH" | "BEARISH" | "NEUTRAL",
            "reason": "string"
        }}
        """

        try:
            # Use asyncio.to_thread if completion is blocking, but LiteLLM supports acompletion
            from litellm import acompletion
            
            response = await acompletion(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                api_base=self.api_base,
                response_format={"type": "json_object"},
                timeout=30
            )

            content = response.choices[0].message.content
            result = json.loads(content)
            
            logger.info(f"LLM Sentiment: {result.get('label')} ({result.get('score')})")
            return result

        except Exception as e:
            logger.error(f"Error in LLM news analysis: {e}")
            return {"score": 0.0, "label": "NEUTRAL", "reason": f"Error: {str(e)}"}

# Global instance
news_reasoner = NewsReasoner()
