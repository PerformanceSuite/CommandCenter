"""
Hypothesis Validation Module for AI Arena

Provides structured hypothesis management and AI-driven validation
using multi-model debates.
"""

from .events import (
    HypothesisDebateRoundEvent,
    HypothesisEventPublisher,
    HypothesisEvidenceAddedEvent,
    HypothesisStatusChangedEvent,
    HypothesisValidationCompletedEvent,
    HypothesisValidationFailedEvent,
    HypothesisValidationStartedEvent,
    get_hypothesis_event_publisher,
)
from .registry import HypothesisRegistry
from .report import ValidationReport, ValidationReportGenerator
from .schema import (
    Hypothesis,
    HypothesisCategory,
    HypothesisCreate,
    HypothesisEvidence,
    HypothesisPriority,
    HypothesisStatus,
    HypothesisUpdate,
    HypothesisValidationResult,
    ImpactLevel,
    RiskLevel,
    TestabilityLevel,
)
from .storage import HypothesisEvidenceStorage, create_evidence_storage
from .validator import HypothesisValidator, ValidationConfig, validate_hypothesis_quick

__all__ = [
    # Schema types
    "Hypothesis",
    "HypothesisCreate",
    "HypothesisUpdate",
    "HypothesisStatus",
    "HypothesisCategory",
    "HypothesisEvidence",
    "HypothesisPriority",
    "HypothesisValidationResult",
    "ImpactLevel",
    "RiskLevel",
    "TestabilityLevel",
    # Validator
    "HypothesisValidator",
    "ValidationConfig",
    "validate_hypothesis_quick",
    # Registry
    "HypothesisRegistry",
    # Report
    "ValidationReportGenerator",
    "ValidationReport",
    # Events
    "HypothesisEventPublisher",
    "HypothesisValidationStartedEvent",
    "HypothesisValidationCompletedEvent",
    "HypothesisValidationFailedEvent",
    "HypothesisDebateRoundEvent",
    "HypothesisEvidenceAddedEvent",
    "HypothesisStatusChangedEvent",
    "get_hypothesis_event_publisher",
    # Storage
    "HypothesisEvidenceStorage",
    "create_evidence_storage",
]
