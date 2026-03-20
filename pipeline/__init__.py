# pipeline/__init__.py
# Public API for the pipeline package.

from .pipeline_a import PipelineA
from .csv_bank_parser import BankStatementParser, BankMovement

__all__ = ["PipelineA", "BankStatementParser", "BankMovement"]
