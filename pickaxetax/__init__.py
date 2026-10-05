"""Pickaxe Tax: measure and cut wasted AI compute. #AntiTokenMaxing"""

from .analyze import analyze
from .ingest import ingest_text

__version__ = "0.2.0"
__all__ = ["analyze", "ingest_text", "__version__"]
