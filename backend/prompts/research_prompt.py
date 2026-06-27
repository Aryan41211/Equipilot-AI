from datetime import datetime
from typing import Any, Dict, List, Optional

from backend.schemas.market_data import MarketData
from backend.schemas.news import NewsArticle
from backend.schemas.sentiment import SentimentAnalysis

REPORT_SYSTEM_PROMPT = """
You are an expert equity research analyst with 15+ years of experience at top-tier
investment banks. Generate comprehensive, institutional-quality research reports.

Guidelines:
- Use professional, objective, and precise language
- Structure with clear markdown headings (##, ###)
- Cite ALL data points with specific sources in brackets
- Present balanced analysis: bull case, bear case, base case
- Quantify claims with specific numbers, percentages, ratios
- Include risk factors section with specific, actionable risks
- Write for sophisticated investors (not retail)
- Maximum length: {max_length} characters

Citation Format: [Source: Type, Date] e.g., [Source: yfinance, 2024-01-15] or [Source: Reuters, 2024-01-15]
"""

STRUCTURED_OUTPUT_INSTRUCTIONS = """
Generate a JSON object that matches this exact schema:
{
  "company": "string or null",
  "ticker": "string",
  "generated_at": "ISO 8601 datetime string",
  "executive_summary": "2-3 paragraph markdown string",
  "market_snapshot": "string or null",
  "news_summary": "string or null",
  "sentiment_summary": "string or null",
  "key_observations": ["string"],
  "risks": ["string"],
  "confidence": 0.0 to 1.0,
  "disclaimer": "string"
}

Return ONLY a valid JSON object. No markdown, no code fences, no extra text.
"""

RESEARCH_REPORT_TEMPLATE = """
Research Query: {query}
Tickers: {tickers}

MARKET DATA:
{market_data}

NEWS ARTICLES:
{news_data}

SENTIMENT ANALYSIS:
{sentiment_data}

Generate a comprehensive equity research report following the structure and guidelines above.
Focus on answering the research query with actionable insights.
"""


def build_market_data_summary(market_data: Dict[str, MarketData]) -> str:
    """Build market data section for the prompt."""
    if not market_data:
        return "No market data available."

    lines: List[str] = []
    for ticker, data in market_data.items():
        lines.append(f"\n### {ticker} ({data.company_name or 'N/A'})")
        if data.current_price is not None:
            lines.append(f"- Current Price: ${data.current_price:.2f}")
        if data.change_percent is not None:
            lines.append(f"- Change: {data.change_percent:+.2f}%")
        if data.fundamentals:
            fund = data.fundamentals
            if fund.market_cap is not None:
                lines.append(f"- Market Cap: ${fund.market_cap:,.0f}")
            if fund.pe_ratio is not None:
                lines.append(f"- P/E Ratio: {fund.pe_ratio:.2f}")
            if fund.dividend_yield is not None:
                lines.append(f"- Dividend Yield: {fund.dividend_yield:.2%}")

    return "\n".join(lines)


def build_news_summary(news_articles: List[NewsArticle]) -> str:
    """Build news section for the prompt."""
    if not news_articles:
        return "No news articles available."

    lines: List[str] = []
    for article in news_articles[:10]:
        lines.append(f"\n- **{article.title}** ({article.source}, {article.published_at.strftime('%Y-%m-%d')})")
        if article.description:
            lines.append(f"  {article.description[:200]}...")

    return "\n".join(lines)


def build_sentiment_summary(sentiment_analysis: Optional[SentimentAnalysis]) -> str:
    """Build sentiment section for the prompt."""
    if not sentiment_analysis:
        return "No sentiment analysis available."

    lines: List[str] = []
    sent = sentiment_analysis.overall_sentiment
    lines.append(f"\nOverall Sentiment: {sent.label} (score: {sent.score:.2f}, confidence: {sent.confidence:.2f})")
    lines.append(f"Reasoning: {sentiment_analysis.reasoning}")

    for hs in sentiment_analysis.headline_sentiments[:5]:
        ticker_info = f" ({hs.ticker})" if hs.ticker else ""
        lines.append(f"- {hs.headline}{ticker_info}: {hs.label} (confidence: {hs.confidence:.2f})")

    return "\n".join(lines)


def build_report_prompt(
    query: str,
    tickers: List[str],
    market_data: Dict[str, MarketData],
    news_articles: List[NewsArticle],
    sentiment_analysis: Optional[SentimentAnalysis],
    max_length: int = 5000,
) -> str:
    """Build the complete research report prompt."""
    market_summary = build_market_data_summary(market_data)
    news_summary = build_news_summary(news_articles)
    sentiment_summary = build_sentiment_summary(sentiment_analysis)

    return RESEARCH_REPORT_TEMPLATE.format(
        query=query,
        tickers=", ".join(tickers),
        market_data=market_summary,
        news_data=news_summary,
        sentiment_data=sentiment_summary,
    )
