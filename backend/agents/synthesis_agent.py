# EquiPilot AI - Synthesis Agent
# Research report generation agent

import asyncio
from typing import Any

from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from backend.exceptions.synthesis_exceptions import (
    SynthesisProviderError,
    SynthesisTimeoutError,
    SynthesisValidationError,
)
from backend.prompts.research_prompt import (
    REPORT_SYSTEM_PROMPT,
    STRUCTURED_OUTPUT_INSTRUCTIONS,
    build_report_prompt,
)
from backend.schemas.market_data import MarketData
from backend.schemas.news import NewsArticle
from backend.schemas.report import Citation, ReportSection, ResearchReport
from backend.schemas.research_report import SynthesizedReport
from backend.schemas.sentiment import SentimentAnalysis
from backend.services.llm_service import get_llm_service
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class SynthesisAgent:
    """Agent for synthesizing research data into comprehensive reports."""

    def __init__(self):
        self.llm = get_llm_service()

    async def generate_report(
        self,
        query: str,
        tickers: list[str],
        market_data: dict[str, MarketData],
        news_articles: list[NewsArticle],
        sentiment_analysis: SentimentAnalysis | None = None,
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

        prompt = build_report_prompt(
            query=query,
            tickers=tickers,
            market_data=market_data,
            news_articles=news_articles,
            sentiment_analysis=sentiment_analysis,
            max_length=max_length,
        )

        schema = SynthesizedReport.model_json_schema()

        json_data = await self._call_llm_with_retry(prompt, schema)

        try:
            synthesized = SynthesizedReport.model_validate(json_data)
        except Exception as e:
            logger.error("Failed to validate synthesized report", error=str(e))
            raise SynthesisValidationError(f"Schema validation failed: {e}")

        report = self._synthesized_to_research_report(
            synthesized=synthesized,
            query=query,
            tickers=tickers,
            market_data=market_data,
            news_articles=news_articles,
            sentiment_analysis=sentiment_analysis,
        )

        return report

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((SynthesisProviderError, SynthesisTimeoutError)),
    )
    async def _call_llm_with_retry(self, prompt: str, schema: dict[str, Any]) -> dict[str, Any]:
        """Call the LLM with retry logic for transient failures."""
        try:
            return await self.llm.structured_completion(
                system_prompt=REPORT_SYSTEM_PROMPT.format(max_length=5000) + STRUCTURED_OUTPUT_INSTRUCTIONS,
                user_prompt=prompt,
                schema=schema,
                model=self.llm.default_model,
                temperature=0.3,
            )
        except Exception as e:
            error_str = str(e).lower()
            if "timeout" in error_str or isinstance(e, asyncio.TimeoutError):
                raise SynthesisTimeoutError(str(e))
            raise SynthesisProviderError(str(e))

    def _synthesized_to_research_report(
        self,
        synthesized: SynthesizedReport,
        query: str,
        tickers: list[str],
        market_data: dict[str, MarketData],
        news_articles: list[NewsArticle],
        sentiment_analysis: SentimentAnalysis | None,
    ) -> ResearchReport:
        """Map SynthesizedReport into the existing ResearchReport structure."""
        sections = [
            ReportSection(
                id="executive_summary",
                title="Executive Summary",
                level=1,
                content=synthesized.executive_summary,
                order=1,
            ),
            ReportSection(
                id="market_snapshot",
                title="Market Snapshot",
                level=1,
                content=synthesized.market_snapshot or "No market data available.",
                order=2,
            ),
            ReportSection(
                id="news_summary",
                title="News Summary",
                level=1,
                content=synthesized.news_summary or "No news articles available.",
                order=3,
            ),
            ReportSection(
                id="sentiment_summary",
                title="Sentiment Analysis",
                level=1,
                content=synthesized.sentiment_summary or "No sentiment data available.",
                order=4,
            ),
            ReportSection(
                id="key_observations",
                title="Key Observations",
                level=1,
                content="\n".join(f"- {obs}" for obs in synthesized.key_observations) if synthesized.key_observations else "None.",
                order=5,
            ),
            ReportSection(
                id="risks",
                title="Risk Factors",
                level=1,
                content="\n".join(f"- {risk}" for risk in synthesized.risks) if synthesized.risks else "None identified.",
                order=6,
            ),
        ]

        market_data_sources = [
            Citation(
                id=f"market_{t}",
                type="market_data",
                title=f"{t} Market Data",
                source="yfinance",
            )
            for t in tickers
        ]

        news_sources = [
            Citation(
                id=f"news_{i}",
                type="news",
                title=a.title,
                url=str(a.url),
                source=a.source,
                date=a.published_at,
            )
            for i, a in enumerate(news_articles[:20])
        ]

        sentiment_sources = []
        if sentiment_analysis:
            sentiment_sources.append(
                Citation(
                    id="sentiment_overall",
                    type="sentiment",
                    title="Overall Sentiment Analysis",
                    source="llm",
                )
            )

        total_citations = len(news_articles) + len(tickers) + len(sentiment_sources)
        unique_sources = len(set(a.source for a in news_articles)) + (1 if sentiment_analysis else 0) + (1 if market_data else 0)

        return ResearchReport(
            request_id="",
            query=query,
            tickers=tickers,
            generated_at=synthesized.generated_at,
            executive_summary=synthesized.executive_summary,
            sections=sections,
            market_data_sources=market_data_sources,
            news_sources=news_sources,
            sentiment_sources=sentiment_sources,
            total_citations=total_citations,
            unique_sources=unique_sources,
            confidence_score=synthesized.confidence,
            disclaimer=synthesized.disclaimer,
        )
