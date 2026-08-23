"""Backward-compatible import path for the sentiment API client."""

from .sentiment import get_clova_sentiment

__all__ = ["get_clova_sentiment"]
