"""
Validation Report Generator

Creates structured reports from hypothesis validation results,
suitable for stakeholder communication and decision-making.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import structlog

from .schema import Hypothesis, HypothesisCategory, HypothesisStatus, HypothesisValidationResult

logger = structlog.get_logger(__name__)


@dataclass
class ValidationReport:
    """Structured validation report for stakeholder communication."""

    report_id: str
    title: str
    generated_at: datetime
    hypothesis_count: int

    # Summary statistics
    total_validated: int = 0
    total_invalidated: int = 0
    total_inconclusive: int = 0
    average_confidence: float = 0.0
    total_cost: float = 0.0

    # Executive summary
    executive_summary: str = ""
    key_findings: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)

    # Detailed sections
    sections: list[dict[str, Any]] = field(default_factory=list)

    # Metadata
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_markdown(self) -> str:
        """Convert report to Markdown format."""
        lines = [
            f"# {self.title}",
            "",
            f"*Generated: {self.generated_at.strftime('%Y-%m-%d %H:%M UTC')}*",
            "",
            "---",
            "",
            "## Executive Summary",
            "",
            self.executive_summary,
            "",
            "### Key Findings",
            "",
        ]

        for finding in self.key_findings:
            lines.append(f"- {finding}")

        lines.extend(
            [
                "",
                "### Recommendations",
                "",
            ]
        )

        for rec in self.recommendations:
            lines.append(f"- {rec}")

        if self.risks:
            lines.extend(
                [
                    "",
                    "### Key Risks",
                    "",
                ]
            )
            for risk in self.risks:
                lines.append(f"- ⚠️ {risk}")

        lines.extend(
            [
                "",
                "---",
                "",
                "## Summary Statistics",
                "",
                "| Metric | Value |",
                "|--------|-------|",
                f"| Hypotheses Evaluated | {self.hypothesis_count} |",
                f"| Validated | {self.total_validated} |",
                f"| Invalidated | {self.total_invalidated} |",
                f"| Inconclusive | {self.total_inconclusive} |",
                f"| Average Confidence | {self.average_confidence:.1f}% |",
                f"| Total Cost | ${self.total_cost:.2f} |",
                "",
            ]
        )

        # Add detailed sections
        for section in self.sections:
            lines.extend(
                [
                    "---",
                    "",
                    f"## {section['title']}",
                    "",
                    section.get("content", ""),
                    "",
                ]
            )

        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        """Convert report to dictionary."""
        return {
            "report_id": self.report_id,
            "title": self.title,
            "generated_at": self.generated_at.isoformat(),
            "hypothesis_count": self.hypothesis_count,
            "total_validated": self.total_validated,
            "total_invalidated": self.total_invalidated,
            "total_inconclusive": self.total_inconclusive,
            "average_confidence": self.average_confidence,
            "total_cost": self.total_cost,
            "executive_summary": self.executive_summary,
            "key_findings": self.key_findings,
            "recommendations": self.recommendations,
            "risks": self.risks,
            "sections": self.sections,
            "metadata": self.metadata,
        }


class ValidationReportGenerator:
    """
    Generates validation reports from hypothesis validation results.

    Example:
        generator = ValidationReportGenerator()

        # Generate report for a batch of results
        report = generator.generate_batch_report(
            title="Q1 2025 Market Validation",
            hypotheses=hypotheses,
            results=validation_results,
        )

        # Export as markdown
        markdown = report.to_markdown()
    """

    def __init__(self):
        """Initialize the report generator."""
        self._report_counter = 0

    def generate_single_report(
        self,
        hypothesis: Hypothesis,
        result: HypothesisValidationResult,
        title: str | None = None,
    ) -> ValidationReport:
        """
        Generate a report for a single hypothesis validation.

        Args:
            hypothesis: The validated hypothesis
            result: The validation result
            title: Optional custom title

        Returns:
            ValidationReport for the single hypothesis
        """
        self._report_counter += 1
        report_id = f"rpt_{datetime.utcnow().strftime('%Y%m%d')}_{self._report_counter:04d}"

        title = title or f"Validation Report: {hypothesis.statement[:50]}..."

        report = ValidationReport(
            report_id=report_id,
            title=title,
            generated_at=datetime.utcnow(),
            hypothesis_count=1,
            total_validated=1 if result.status == HypothesisStatus.VALIDATED else 0,
            total_invalidated=1 if result.status == HypothesisStatus.INVALIDATED else 0,
            total_inconclusive=1 if result.status == HypothesisStatus.NEEDS_MORE_DATA else 0,
            average_confidence=result.validation_score,
            total_cost=result.total_cost,
        )

        # Generate executive summary
        report.executive_summary = self._generate_single_summary(hypothesis, result)

        # Key findings
        report.key_findings = [
            f"Hypothesis Status: **{result.status.value.upper()}**",
            f"Validation Confidence: {result.validation_score:.1f}%",
            f"Debate Rounds: {result.rounds_taken}",
            f"Consensus: {'Reached' if result.consensus_reached else 'Not reached'}",
        ]

        # Recommendations
        report.recommendations = [result.recommendation]

        # Follow-up questions as risks/next steps
        if result.follow_up_questions:
            report.risks = [f"Unresolved question: {q}" for q in result.follow_up_questions[:3]]

        # Detailed sections
        report.sections = [
            {
                "title": "Hypothesis Details",
                "content": self._format_hypothesis_details(hypothesis),
            },
            {
                "title": "Debate Summary",
                "content": self._format_debate_summary(result),
            },
            {
                "title": "Evidence Collected",
                "content": self._format_evidence(hypothesis, result),
            },
        ]

        return report

    def generate_batch_report(
        self,
        title: str,
        hypotheses: list[Hypothesis],
        results: list[HypothesisValidationResult],
    ) -> ValidationReport:
        """
        Generate a comprehensive report for multiple hypothesis validations.

        Args:
            title: Report title
            hypotheses: List of validated hypotheses
            results: List of validation results (same order as hypotheses)

        Returns:
            ValidationReport for the batch
        """
        self._report_counter += 1
        report_id = f"rpt_{datetime.utcnow().strftime('%Y%m%d')}_{self._report_counter:04d}"

        if len(hypotheses) != len(results):
            raise ValueError("Hypotheses and results lists must have same length")

        # Calculate statistics
        validated = sum(1 for r in results if r.status == HypothesisStatus.VALIDATED)
        invalidated = sum(1 for r in results if r.status == HypothesisStatus.INVALIDATED)
        inconclusive = sum(1 for r in results if r.status == HypothesisStatus.NEEDS_MORE_DATA)
        avg_confidence = sum(r.validation_score for r in results) / len(results) if results else 0
        total_cost = sum(r.total_cost for r in results)

        report = ValidationReport(
            report_id=report_id,
            title=title,
            generated_at=datetime.utcnow(),
            hypothesis_count=len(hypotheses),
            total_validated=validated,
            total_invalidated=invalidated,
            total_inconclusive=inconclusive,
            average_confidence=avg_confidence,
            total_cost=total_cost,
        )

        # Generate executive summary
        report.executive_summary = self._generate_batch_summary(hypotheses, results)

        # Key findings
        report.key_findings = self._extract_key_findings(hypotheses, results)

        # Recommendations
        report.recommendations = self._generate_batch_recommendations(hypotheses, results)

        # Risks
        report.risks = self._identify_risks(hypotheses, results)

        # Detailed sections by category
        report.sections = self._generate_category_sections(hypotheses, results)

        return report

    def generate_category_report(
        self,
        category: HypothesisCategory,
        hypotheses: list[Hypothesis],
        results: list[HypothesisValidationResult],
    ) -> ValidationReport:
        """
        Generate a report focused on a specific hypothesis category.

        Args:
            category: The category to report on
            hypotheses: All hypotheses
            results: All results

        Returns:
            Category-specific ValidationReport
        """
        # Filter to category
        category_pairs = [(h, r) for h, r in zip(hypotheses, results) if h.category == category]
        if not category_pairs:
            raise ValueError(f"No hypotheses found for category: {category.value}")

        cat_hypotheses = [p[0] for p in category_pairs]
        cat_results = [p[1] for p in category_pairs]

        return self.generate_batch_report(
            title=f"{category.value.title()} Hypothesis Validation Report",
            hypotheses=cat_hypotheses,
            results=cat_results,
        )

    def _generate_single_summary(
        self, hypothesis: Hypothesis, result: HypothesisValidationResult
    ) -> str:
        """Generate executive summary for single hypothesis."""
        status_desc = {
            HypothesisStatus.VALIDATED: "appears to be well-supported",
            HypothesisStatus.INVALIDATED: "appears to be contradicted by evidence",
            HypothesisStatus.NEEDS_MORE_DATA: "requires additional research",
        }

        desc = status_desc.get(result.status, "has been evaluated")

        return f"""This report presents the validation results for the hypothesis:

> "{hypothesis.statement}"

After multi-model AI debate analysis, this hypothesis **{desc}** with {result.validation_score:.1f}% confidence.
The debate {'reached consensus' if result.consensus_reached else 'did not reach full consensus'}
after {result.rounds_taken} round{'s' if result.rounds_taken != 1 else ''}.

**Key Conclusion:** {result.final_answer}"""

    def _generate_batch_summary(
        self, hypotheses: list[Hypothesis], results: list[HypothesisValidationResult]
    ) -> str:
        """Generate executive summary for batch validation."""
        validated = sum(1 for r in results if r.status == HypothesisStatus.VALIDATED)
        invalidated = sum(1 for r in results if r.status == HypothesisStatus.INVALIDATED)
        inconclusive = sum(1 for r in results if r.status == HypothesisStatus.NEEDS_MORE_DATA)

        return f"""This report summarizes the validation of {len(hypotheses)} business hypotheses
through AI Arena multi-model debate analysis.

**Results Overview:**
- {validated} hypotheses ({validated / len(hypotheses) * 100:.0f}%) were **validated**
- {invalidated} hypotheses ({invalidated / len(hypotheses) * 100:.0f}%) were **invalidated**
- {inconclusive} hypotheses ({inconclusive / len(hypotheses) * 100:.0f}%) require **more data**

The validation process used multiple AI models (Claude, Gemini, GPT) in structured debates
to evaluate each hypothesis from multiple perspectives."""

    def _extract_key_findings(
        self, hypotheses: list[Hypothesis], results: list[HypothesisValidationResult]
    ) -> list[str]:
        """Extract key findings from validation results."""
        findings = []

        # High confidence validations
        high_conf_validated = [
            (h, r)
            for h, r in zip(hypotheses, results)
            if r.status == HypothesisStatus.VALIDATED and r.validation_score >= 80
        ]
        if high_conf_validated:
            findings.append(
                f"{len(high_conf_validated)} hypothesis(es) validated with high confidence (80%+)"
            )

        # Critical invalidations
        high_impact_invalid = [
            (h, r)
            for h, r in zip(hypotheses, results)
            if r.status == HypothesisStatus.INVALIDATED and h.impact.value == "high"
        ]
        if high_impact_invalid:
            findings.append(
                f"⚠️ {len(high_impact_invalid)} high-impact hypothesis(es) were invalidated"
            )

        # Consensus rates
        consensus_count = sum(1 for r in results if r.consensus_reached)
        findings.append(
            f"AI agents reached consensus on {consensus_count}/{len(results)} "
            f"({consensus_count / len(results) * 100:.0f}%) of hypotheses"
        )

        return findings

    def _generate_batch_recommendations(
        self, hypotheses: list[Hypothesis], results: list[HypothesisValidationResult]
    ) -> list[str]:
        """Generate recommendations from batch results."""
        recommendations = []

        # Validated high-impact items
        validated_high = [
            h
            for h, r in zip(hypotheses, results)
            if r.status == HypothesisStatus.VALIDATED and h.impact.value == "high"
        ]
        if validated_high:
            recommendations.append(
                f"Proceed confidently with {len(validated_high)} validated high-impact assumption(s)"
            )

        # Needs more data items
        needs_data = [
            h for h, r in zip(hypotheses, results) if r.status == HypothesisStatus.NEEDS_MORE_DATA
        ]
        if needs_data:
            recommendations.append(
                f"Prioritize research for {len(needs_data)} inconclusive hypothesis(es) "
                "before major resource commitments"
            )

        # Invalidated items requiring pivot
        invalidated = [
            h for h, r in zip(hypotheses, results) if r.status == HypothesisStatus.INVALIDATED
        ]
        if invalidated:
            recommendations.append(
                f"Review and pivot strategy for {len(invalidated)} invalidated assumption(s)"
            )

        return recommendations

    def _identify_risks(
        self, hypotheses: list[Hypothesis], results: list[HypothesisValidationResult]
    ) -> list[str]:
        """Identify risks from validation results."""
        risks = []

        # Low consensus debates
        low_consensus = [(h, r) for h, r in zip(hypotheses, results) if not r.consensus_reached]
        if low_consensus:
            risks.append(
                f"{len(low_consensus)} hypothesis(es) lack clear consensus - "
                "results may need human judgment"
            )

        # High-risk invalidated
        high_risk_invalid = [
            (h, r)
            for h, r in zip(hypotheses, results)
            if r.status == HypothesisStatus.INVALIDATED and h.risk.value == "high"
        ]
        if high_risk_invalid:
            risks.append(
                f"{len(high_risk_invalid)} previously high-risk assumption(s) confirmed as invalid - "
                "review downstream dependencies"
            )

        return risks

    def _generate_category_sections(
        self, hypotheses: list[Hypothesis], results: list[HypothesisValidationResult]
    ) -> list[dict[str, Any]]:
        """Generate report sections organized by category."""
        sections = []

        # Group by category
        by_category: dict[
            HypothesisCategory, list[tuple[Hypothesis, HypothesisValidationResult]]
        ] = {}
        for h, r in zip(hypotheses, results):
            if h.category not in by_category:
                by_category[h.category] = []
            by_category[h.category].append((h, r))

        for category, pairs in by_category.items():
            content_lines = [f"### {category.value.title()} Hypotheses\n"]

            for h, r in pairs:
                status_emoji = {
                    HypothesisStatus.VALIDATED: "✅",
                    HypothesisStatus.INVALIDATED: "❌",
                    HypothesisStatus.NEEDS_MORE_DATA: "🔍",
                }.get(r.status, "⏳")

                content_lines.append(f"**{status_emoji} {h.statement}**")
                content_lines.append(f"- Status: {r.status.value}")
                content_lines.append(f"- Confidence: {r.validation_score:.1f}%")
                content_lines.append(f"- Key insight: {r.final_answer[:150]}...")
                content_lines.append("")

            sections.append(
                {"title": f"{category.value.title()} Analysis", "content": "\n".join(content_lines)}
            )

        return sections

    def _format_hypothesis_details(self, hypothesis: Hypothesis) -> str:
        """Format hypothesis details for report."""
        return f"""| Field | Value |
|-------|-------|
| Statement | {hypothesis.statement} |
| Category | {hypothesis.category.value} |
| Impact | {hypothesis.impact.value} |
| Risk | {hypothesis.risk.value} |
| Testability | {hypothesis.testability.value} |
| Success Criteria | {hypothesis.success_criteria} |
| Context | {hypothesis.context or 'N/A'} |"""

    def _format_debate_summary(self, result: HypothesisValidationResult) -> str:
        """Format debate summary for report."""
        return f"""**Final Answer:** {result.final_answer}

**Reasoning Summary:**
{result.reasoning_summary}

**Debate Metrics:**
- Rounds: {result.rounds_taken}
- Consensus: {'Yes' if result.consensus_reached else 'No'}
- Duration: {result.duration_seconds:.1f} seconds
- Cost: ${result.total_cost:.4f}"""

    def _format_evidence(self, hypothesis: Hypothesis, result: HypothesisValidationResult) -> str:
        """Format evidence for report."""
        lines = [
            "| Source | Evidence | Supports? | Confidence |",
            "|--------|----------|-----------|------------|",
        ]

        all_evidence = hypothesis.evidence + result.new_evidence
        for ev in all_evidence[:10]:  # Limit to 10 for readability
            supports = "✅ Yes" if ev.supports else "❌ No"
            lines.append(
                f"| {ev.source[:30]} | {ev.content[:50]}... | {supports} | {ev.confidence}% |"
            )

        if len(all_evidence) > 10:
            lines.append(f"\n*...and {len(all_evidence) - 10} more evidence items*")

        return "\n".join(lines)
