# EquiPilot AI - Synthesis Agent
# Research report generation agent

from typing import List, Dict, Any, Optional
from backend.services.llm_service import get_llm_service
from backend.schemas.report import ResearchReport, ReportSection, Citation
from backend.schemas.market_data import MarketData
from backend.schemas.news import NewsArticle
from backend.schemas.sentiment import SentimentAnalysis
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class SynthesisAgent:
    """Agent for synthesizing research data into comprehensive reports."""

    def __init__(self):
        self.llm = get_llm_service()

    async def generate_report(
        self,
        query: str,
        tickers: List[str],
        market_data: Dict[str, MarketData],
        news_articles: List[NewsArticle],
        sentiment_analysis: Optional[SentimentAnalysis] = None,
        max_length: int = 5000,
    ) -> ResearchReport:
        """
        Generate a research report from collected data.

        Args:
            query: Original research query
            tickers: Analyzed tickers
            market_data: Market data for tickers
            news_articles: Relevant news articles
            sentiment_analysis: Sentiment analysis results
            max_length: Maximum report length

        Returns:
            ResearchReport with structured content
        """
        logger.info("Generating report", query=query[:100], tickers=tickers)

        # Build prompt with all data
        prompt = self._build_prompt(
            query=query,
            tickers=tickers,
            market_data=market_data,
            news_articles=news_articles,
            sentiment_analysis=sentiment_analysis,
            max_length=max_length,
        )

        # Generate report using LLM
        report_text = await self.llm.generate_report(prompt)

        # Parse and structure the report
        report = self._parse_report(
            request_id="",  # Will be filled by caller
            query=query,
            tickers=tickers,
            report_text=report_text,
            market_data=market_data,
            news_articles=news_articles,
            sentiment_analysis=sentiment_analysis,
        )

        return report

    def _build_prompt(
        self,
        query: str,
        tickers: List[str],
        market_data: Dict[str, MarketData],
        news_articles: List[NewsArticle],
        sentiment_analysis: Optional[SentimentAnalysis],
        max_length: int,
    ) -> str:
        """Build the prompt for report generation."""

        # Format market data
        market_summary = ""
        for ticker, data in market_data.items():
            market_summary += f"\n### {ticker} ({data.company_name or 'N/A'})\n"
            if data.current_price:
                market_summary += f"- Current Price: ${data.current_price:.2f}\n"
            if data.change_percent is not None:
                market_summary += f"- Change: {data.change_percent:+.2f}%\n"
            if data.fundamentals:
                fund = data.fundamentals
                market_summary += f"- Market Cap: ${fund.market_cap:,.0f}\n" if fund.market_cap else ""
                market_summary += f"- P/E Ratio: {fund.pe_ratio:.2f}\n" if fund.pe_ratio else ""
                market_summary += f"- Dividend Yield: {fund.dividend_yield:.2%}\n" if fund.dividend_yield else ""

        # Format news
        news_summary = ""
        for article in news_articles[:10]:  # Limit to top 10
            news_summary += f"\n- **{article.title}** ({article.source}, {article.published_at.strftime('%Y-%m-%d')})\n"
            if article.description:
                news_summary += f"  {article.description[:200]}...\n"

        # Format sentiment
        sentiment_summary = ""
        if sentiment_analysis:
            sent = sentiment_analysis.overall_sentiment
            sentiment_summary = f"\nOverall Sentiment: {sent.label} ({sent.score:.2f}, confidence: {sent.confidence:.2f})\n"
            for ticker, t_sent in sentiment_analysis.ticker_sentiments.items():
                sentiment_summary += f"- {ticker}: {t_sent.label} ({t_sent.score:.2f})\n"

        prompt = f"""
        Research Query: {query}
        Tickers: {', '.join(tickers)}

        MARKET DATA:
        {market_summary}

        NEWS ARTICLES:
        {news_summary}

        SENTIMENT ANALYSIS:
        {sentiment_summary}

        INSTRUCTIONS:
        Generate a comprehensive equity research report addressing the query.
        Maximum length: {max_length} characters.

        Structure the report with:
        1. Executive Summary
        2. Company Overview (for each ticker)
        3. Financial Analysis
        4. Market Position & Competitive Landscape
        5. News & Sentiment Analysis
        6. Key Risks
        7. Conclusion

        Requirements:
        - Use professional, objective tone
        - Cite specific data points from the provided sources
        - Present balanced analysis (bull and bear cases)
        - Include appropriate disclaimers
        - Output in markdown format with clear headings
        """

        return prompt

    def _parse_report(
        self,
        request_id: str,
        query: str,
        tickers: List[str],
        report_text: str,
        market_data: Dict[str, MarketData],
        news_articles: List[NewsArticle],
        sentiment_analysis: Optional[SentimentAnalysis],
    ) -> ResearchReport:
        """Parse generated report text into structured ResearchReport."""
        # For now, return a basic structure
        # TODO: Implement proper parsing of LLM output into sections

        return ResearchReport(
            request_id=request_id,
            query=query,
            tickers=tickers,
            executive_summary="Report generated successfully. Full parsing pending.",
            sections=[
                ReportSection(
                    id="full_report",
                    title="Full Report",
                    level=1,
                    content=report_text,
                    order=1,
                )
            ],
            market_data_sources=[
                Citation(
                    id=f"market_{t}",
                    type="market_data",
                    title=f"{t} Market Data",
                    source="yfinance",
                )
                for t in tickers
            ],
            news_sources=[
                Citation(
                    id=f"news_{i}",
                    type="news",
                    title=a.title,
                    url=str(a.url),
                    source=a.source,
                    date=a.published_at,
                )
                for i, a in enumerate(news_articles[:20])
            ],
            total_citations=len(news_articles) + len(tickers),
            unique_sources=len(set(a.source for a in news_articles)) + 1,
        )