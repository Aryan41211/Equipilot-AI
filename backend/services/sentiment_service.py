from __future__ import annotations

import asyncio
from collections.abc import Sequence
from typing import Any

from backend.exceptions.sentiment_exceptions import (
    SentimentMalformedResponseError,
    SentimentProviderError,
    SentimentTimeoutError,
    SentimentValidationError,
)
from backend.schemas.news import NewsArticle
from backend.schemas.sentiment import (
    HeadlineSentiment,
    SentimentAnalysis,
    SentimentProcessingMetadata,
    SentimentScore,
)
from backend.services.llm_service import get_llm_service

# Keep parsing/validation strictly typed to ensure deterministic failures.


class SentimentService:
    """Production-ready sentiment analysis service for news headlines."""

    def __init__(
        self,
        *,
        max_retries: int = 2,
        retry_backoff_seconds: float = 0.2,
        llm_timeout_seconds: float = 30.0,
    ) -> None:
        self.llm = get_llm_service()
        self.max_retries = max_retries
        self.retry_backoff_seconds = retry_backoff_seconds
        self.llm_timeout_seconds = llm_timeout_seconds

    async def analyze_articles(
        self,
        articles: Sequence[NewsArticle],
        tickers: Sequence[str],
    ) -> SentimentAnalysis:
        """
        Analyze sentiment for normalized news articles.

        Args:
            articles: normalized news articles
            tickers: tickers to focus on

        Returns:
            Structured SentimentAnalysis.

        Raises:
            SentimentTimeoutError: on provider timeout
            SentimentProviderError: on provider operational failure
            SentimentMalformedResponseError: on non-JSON or missing keys
            SentimentValidationError: on schema validation errors
        """
        if not articles:
            return self._empty_analysis(tickers=list(tickers))

        tickers_list = [t for t in tickers]
        articles_list = list(articles)

        last_error: Exception | None = None
        for attempt in range(self.max_retries + 1):
            try:
                parsed = await asyncio.wait_for(
                    self._call_llm(
                        articles=articles_list,
                        tickers=tickers_list,
                    ),
                    timeout=self.llm_timeout_seconds,
                )
                return parsed
            except SentimentTimeoutError as e:
                last_error = e
                if attempt >= self.max_retries:
                    raise
            except (SentimentMalformedResponseError, SentimentValidationError):
                # Deterministic: do not retry malformed/validation errors.
                raise
            except SentimentProviderError as e:
                last_error = e
                if attempt >= self.max_retries:
                    raise
            except Exception as e:
                last_error = e
                if attempt >= self.max_retries:
                    raise SentimentProviderError(str(e))

            await asyncio.sleep(self.retry_backoff_seconds * (attempt + 1))

        if last_error:
            raise SentimentProviderError(str(last_error))
        raise SentimentProviderError("Sentiment analysis failed unexpectedly.")

    async def _call_llm(
        self,
        *,
        articles: list[NewsArticle],
        tickers: list[str],
    ) -> SentimentAnalysis:
        """
        Calls LLM using existing llm_service. Do not duplicate provider logic.

        Uses LLMService.analyze_sentiment(text, tickers), then maps into our
        SentimentAnalysis schema.
        """
        text = "\n\n".join(
            [f"- {a.title or ''}" for a in articles if (a.title or "").strip()]
        )

        try:
            llm_payload = await self.llm.analyze_sentiment(text=text, tickers=tickers)
            return self._parse_and_validate(
                llm_payload,
                tickers=tickers,
                article_count=len(articles),
            )
        except TimeoutError as e:
            raise SentimentTimeoutError(str(e))
        except (SentimentTimeoutError, SentimentMalformedResponseError, SentimentValidationError):
            # Preserve typed exceptions from parsing/validation.
            raise
        except Exception as e:
            msg = str(e)
            if "timeout" in msg.lower():
                raise SentimentTimeoutError(msg)
            raise SentimentProviderError(msg)

    def _parse_and_validate(
        self,
        payload: dict[str, Any],
        tickers: list[str],
        article_count: int,
    ) -> SentimentAnalysis:
        """
        Convert llm_service.analyze_sentiment() payload into SentimentAnalysis schema.

        Expected llm_service output shape:
        {
          "overall": {"label": ..., "score": ..., "confidence": ...},
          "ticker_sentiments": { "TICKER": {"label","score","confidence"}, ...},
          "key_themes": [{"theme","sentiment","relevance"}, ...]
        }
        """
        try:
            overall_raw = payload["overall"]
            overall_score = SentimentScore(
                label=str(overall_raw["label"]),
                confidence=float(overall_raw["confidence"]),
                score=float(overall_raw["score"]),
            )

            ticker_sentiments_raw = payload.get("ticker_sentiments") or {}
            headline_sentiments: list[HeadlineSentiment] = []
            # We do not synthesize per-headline sentiment without per-headline data.
            # Instead, we attach ticker-level sentiment entries as "headline" rows
            # using a deterministic placeholder headline.
            for t, ts in ticker_sentiments_raw.items():
                headline_sentiments.append(
                    HeadlineSentiment(
                        headline=f"Ticker sentiment for {t}",
                        ticker=t,
                        label=str(ts["label"]),
                        confidence=float(ts["confidence"]),
                        reasoning="Derived from ticker-level sentiment.",
                    )
                )

            key_themes_raw = payload.get("key_themes") or []
            if key_themes_raw:
                # Use themes to build reasoning deterministically.
                reasoning = "; ".join(
                    [f"{kt.get('theme','')}={kt.get('sentiment','neutral')}" for kt in key_themes_raw]
                )
            else:
                reasoning = "No key themes provided by LLM."

            confidence = float(overall_raw["confidence"])
            processing_metadata = SentimentProcessingMetadata(
                article_count=article_count,
                tickers_provided=list(tickers),
            )

            return SentimentAnalysis(
                overall_sentiment=overall_score,
                confidence=confidence,
                reasoning=reasoning,
                headline_sentiments=headline_sentiments,
                processing_metadata=processing_metadata,
            )
        except KeyError as e:
            raise SentimentMalformedResponseError(f"Missing key in LLM response: {e!s}")
        except (TypeError, ValueError) as e:
            raise SentimentMalformedResponseError(f"Malformed LLM response: {e!s}")
        except Exception as e:
            # Distinguish schema validation problems from generic malformed payloads.
            # Pydantic validation errors indicate "validation" (typed).
            if "validation error" in str(e).lower():
                raise SentimentValidationError(str(e))
            raise SentimentMalformedResponseError(f"Malformed LLM response: {e!s}")

    def _empty_analysis(self, tickers: list[str]) -> SentimentAnalysis:
        # Provide deterministic empty sentiment output.
        neutral = SentimentScore(label="neutral", confidence=0.0, score=0.0)
        return SentimentAnalysis(
            overall_sentiment=neutral,
            confidence=0.0,
            reasoning="No articles provided; sentiment defaults to neutral.",
            headline_sentiments=[],
            processing_metadata=SentimentProcessingMetadata(
                article_count=0, tickers_provided=tickers
            ),
        )


# Singleton instance for existing import patterns
sentiment_service = SentimentService()
