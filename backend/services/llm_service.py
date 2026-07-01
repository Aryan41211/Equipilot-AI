# EquiPilot AI - LLM Service
# Wrapper for OpenAI API integration

import json
from typing import Any

from openai import AsyncOpenAI

from backend.config import settings
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class LLMService:
    """Service for interacting with OpenAI LLM API."""

    def __init__(self):
        if not settings.openai_api_key:
            raise ValueError("OpenAI API key not configured")

        self.client = AsyncOpenAI(
            api_key=settings.openai_api_key,
            timeout=settings.llm_api_timeout,
        )
        self.default_model = settings.openai_model
        self.mini_model = settings.openai_model_mini

    async def close(self):
        """Close the client."""
        await self.client.close()

    async def chat_completion(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float = 0.3,
        max_tokens: int | None = None,
        response_format: dict[str, str] | None = None,
        stream: bool = False,
    ) -> Any:
        """
        Generate chat completion.

        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model to use (defaults to default_model)
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
            response_format: Optional format specification (e.g., {"type": "json_object"})
            stream: Whether to stream the response

        Returns:
            Completion response or async generator for streaming
        """
        model = model or self.default_model

        try:
            response = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens or settings.llm_max_tokens,
                response_format=response_format,
                stream=stream,
            )

            if stream:
                return response

            return response.choices[0].message.content

        except Exception as e:
            logger.error("LLM completion failed", model=model, error=str(e))
            raise

    async def structured_completion(
        self,
        system_prompt: str,
        user_prompt: str,
        schema: dict[str, Any],
        model: str | None = None,
        temperature: float = 0.1,
    ) -> dict[str, Any]:
        """
        Generate structured JSON completion following a schema.

        Args:
            system_prompt: System instructions
            user_prompt: User query
            schema: JSON schema for response validation
            model: Model to use
            temperature: Sampling temperature

        Returns:
            Parsed JSON response
        """
        schema_prompt = f"""
        Respond with a valid JSON object matching this schema:
        {json.dumps(schema, indent=2)}
        """

        messages = [
            {"role": "system", "content": system_prompt + schema_prompt},
            {"role": "user", "content": user_prompt},
        ]

        response = await self.chat_completion(
            messages=messages,
            model=model,
            temperature=temperature,
            response_format={"type": "json_object"},
        )

        try:
            return json.loads(response)
        except json.JSONDecodeError as e:
            logger.error("Failed to parse JSON response", response=response, error=str(e))
            raise

    async def classify_query(
        self,
        query: str,
        categories: list[str],
    ) -> dict[str, Any]:
        """Classify a query into categories."""
        schema = {
            "type": "object",
            "properties": {
                "category": {"type": "string", "enum": categories},
                "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                "reasoning": {"type": "string"},
                "extracted_tickers": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["category", "confidence", "reasoning", "extracted_tickers"],
        }

        system_prompt = (
            "You are a financial query classifier. Analyze the user's query and determine "
            "the primary category, extract any stock tickers mentioned, and provide reasoning."
        )

        user_prompt = f"Query: {query}\n\nCategories: {', '.join(categories)}"

        return await self.structured_completion(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            schema=schema,
            model=self.mini_model,
            temperature=0.1,
        )

    async def extract_tickers(self, query: str) -> list[str]:
        """Extract stock tickers from a query."""
        schema = {
            "type": "object",
            "properties": {
                "tickers": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["tickers"],
        }

        system_prompt = (
            "Extract all stock ticker symbols mentioned in the query. "
            "Return them as uppercase strings (e.g., AAPL, MSFT, GOOGL). "
            "Include both explicit tickers and implied ones from company names."
        )

        return await self.structured_completion(
            system_prompt=system_prompt,
            user_prompt=query,
            schema=schema,
            model=self.mini_model,
            temperature=0.0,
        ).get("tickers", [])

    async def analyze_sentiment(
        self,
        text: str,
        tickers: list[str] | None = None,
    ) -> dict[str, Any]:
        """Analyze sentiment of financial text."""
        schema = {
            "type": "object",
            "properties": {
                "overall": {
                    "type": "object",
                    "properties": {
                        "label": {"type": "string", "enum": ["positive", "negative", "neutral"]},
                        "score": {"type": "number", "minimum": -1, "maximum": 1},
                        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                    },
                    "required": ["label", "score", "confidence"],
                },
                "ticker_sentiments": {
                    "type": "object",
                    "additionalProperties": {
                        "type": "object",
                        "properties": {
                            "label": {"type": "string", "enum": ["positive", "negative", "neutral"]},
                            "score": {"type": "number", "minimum": -1, "maximum": 1},
                            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                        },
                        "required": ["label", "score", "confidence"],
                    },
                },
                "key_themes": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "theme": {"type": "string"},
                            "sentiment": {"type": "string", "enum": ["positive", "negative", "neutral"]},
                            "relevance": {"type": "number", "minimum": 0, "maximum": 1},
                        },
                        "required": ["theme", "sentiment", "relevance"],
                    },
                },
            },
            "required": ["overall", "ticker_sentiments", "key_themes"],
        }

        system_prompt = (
            "You are a financial sentiment analyzer. Analyze the sentiment of the provided "
            "text, focusing on implications for the mentioned tickers. Provide overall sentiment, "
            "per-ticker sentiment, and key themes driving sentiment."
        )

        user_prompt = f"Text: {text}"
        if tickers:
            user_prompt += f"\n\nFocus tickers: {', '.join(tickers)}"

        return await self.structured_completion(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            schema=schema,
            model=self.mini_model,
            temperature=0.1,
        )

    async def generate_report(
        self,
        prompt: str,
        schema: dict[str, Any] | None = None,
    ) -> str:
        """Generate a research report."""
        messages = [
            {"role": "system", "content": self._get_report_system_prompt()},
            {"role": "user", "content": prompt},
        ]

        return await self.chat_completion(
            messages=messages,
            model=self.default_model,
            temperature=0.3,
            max_tokens=settings.llm_max_tokens,
        )

    def _get_report_system_prompt(self) -> str:
        """Get system prompt for report generation."""
        return """
        You are an expert equity research analyst. Generate comprehensive, well-structured
        research reports based on the provided market data, news, and sentiment analysis.

        Guidelines:
        - Use professional, objective tone
        - Cite all data sources explicitly
        - Structure with clear headings and sections
        - Include executive summary, key findings, risks, and conclusion
        - Present balanced analysis (bull and bear cases)
        - Quantify claims with specific data points
        - Include appropriate disclaimers
        - Output in markdown format
        """


# Singleton instance
llm_service = None


def get_llm_service() -> LLMService:
    """Get or create LLM service singleton."""
    global llm_service
    if llm_service is None:
        llm_service = LLMService()
    return llm_service
