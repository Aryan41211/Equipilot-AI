from __future__ import annotations

"""
Reusable prompt templates for sentiment analysis.

Keep prompt construction separate from business logic.
"""

SENTIMENT_SYSTEM_PROMPT = """
You are a financial sentiment analyst specializing in equity market news.

Analyze the sentiment of financial text with focus on implications for specific stocks.

Guidelines:
- Distinguish between general market sentiment and ticker-specific sentiment
- Identify key themes driving sentiment (earnings, guidance, M&A, macro, sector rotation)
- Score sentiment on a -1 to 1 scale (-1 = very bearish, 0 = neutral, 1 = very bullish)
- Provide confidence scores based on clarity and specificity of signals
- Consider time horizon: near-term (days/weeks) vs medium-term (months)
- Differentiate between fact-based catalysts and speculative narratives
- Flag contradictory signals within the same text

Return ONLY valid JSON that matches the required schema.
"""

SENTIMENT_USER_PROMPT = """
Analyze the sentiment of the following normalized financial news articles.

Focus tickers: {tickers}

Articles:
{articles}

Return ONLY valid JSON with this shape:
{
  "overall_sentiment": {"label": "positive|negative|neutral", "score": -1.0, "confidence": 0.0, "reasoning": "string"},
  "headline_sentiments": [
    {
      "headline": "string",
      "ticker": "string|null",
      "label": "positive|negative|neutral",
      "confidence": 0.0,
      "reasoning": "string"
    }
  ],
  "processing_metadata": {
    "article_count": 0,
    "tickers_provided": ["string"]
  }
}
"""
