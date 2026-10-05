"""ANTITOKENMAXING: conversation skeletons instead of conversation transcripts."""

from .analyze import analyze
from .ingest import ingest_text

__version__ = "0.1.0"
__all__ = ["analyze", "ingest_text", "__version__"]
