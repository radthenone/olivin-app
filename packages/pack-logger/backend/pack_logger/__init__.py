"""
Pack Logger - Universal logging package.
"""
from __future__ import annotations

from .logger import LoggingConfigDict, PackLogger, configure_logging, log
from .middleware import ApiLoggingMiddleware

__version__: str = "0.1.0"
__all__: list[str] = [
    "PackLogger",
    "LoggingConfigDict",
    "log",
    "configure_logging",
    "ApiLoggingMiddleware",
]
