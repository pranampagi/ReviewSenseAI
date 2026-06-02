"""SQLAlchemy ORM models for the relational database.

Import all models here so Alembic and ``Base.metadata.create_all`` discover every table.
"""

from .analysis import AnalysisResult
from .product import Product
from .review import Review
from .user import User

__all__ = ["User", "Product", "Review", "AnalysisResult"]
