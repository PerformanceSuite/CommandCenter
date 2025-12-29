"""
Discussion Prompt Generation for AI Arena Debates

Generates contextual prompts for each round of debate,
incorporating previous responses and encouraging convergence.
"""

from __future__ import annotations

from ..agents import AgentResponse
from .state import ConsensusLevel, DebateRound


class DiscussionPromptGenerator:
    """
    Generates discussion prompts for multi-round debates.

    Creates context-aware prompts that:
    - Summarize previous round discussions
    - Highlight areas of agreement and disagreement
    - Encourage agents to refine their positions
    - Guide toward consensus without forcing agreement
    """

    def generate_initial_prompt(
        self,
        question: str,
        context: str | None = None,
    ) -> str:
        """
        Generate the initial round prompt.

        Args:
            question: The main question or hypothesis to debate
            context: Optional additional context

        Returns:
            Formatted prompt for round 1
        """
        prompt = f"## Debate Question\n\n{question}\n"

        if context:
            prompt = f"## Background Context\n\n{context}\n\n{prompt}"

        prompt += """
## Instructions

You are participating in Round 1 of a multi-model debate. Other AI models
will also respond to this question. In subsequent rounds, you'll see their
perspectives and can refine your position.

For this initial round:
1. Provide your independent analysis
2. Be specific about your reasoning
3. Clearly state your confidence level
4. List key evidence supporting your position

Your response will be shared with other participants in the next round.
"""
        return prompt

    def generate_followup_prompt(
        self,
        question: str,
        previous_rounds: list[DebateRound],
        current_round: int,
        consensus_level: ConsensusLevel | None = None,
        context: str | None = None,
    ) -> str:
        """
        Generate a follow-up round prompt with previous discussion context.

        Args:
            question: The original question
            previous_rounds: List of previous debate rounds
            current_round: Current round number (1-indexed)
            consensus_level: Consensus level from previous round
            context: Optional additional context

        Returns:
            Formatted prompt for the current round
        """
        prompt = f"## Debate Question (Round {current_round})\n\n{question}\n\n"

        if context:
            prompt += f"## Background Context\n\n{context}\n\n"

        # Add summary of previous discussions
        prompt += self._summarize_previous_rounds(previous_rounds)

        # Add consensus status
        if consensus_level:
            prompt += self._format_consensus_status(consensus_level)

        # Add round-specific instructions
        prompt += self._get_round_instructions(current_round, consensus_level)

        return prompt

    def _summarize_previous_rounds(self, rounds: list[DebateRound]) -> str:
        """Summarize previous round discussions."""
        if not rounds:
            return ""

        summary = "## Previous Discussion Summary\n\n"

        for round_data in rounds:
            summary += f"### Round {round_data.round_number + 1}\n\n"

            # Group by position if possible
            positions = self._extract_positions(round_data.responses)

            if len(positions) == 1:
                summary += "**All participants agreed:**\n"
                for response in round_data.responses:
                    summary += f"- {response.agent_name}: {self._truncate(response.answer, 150)}\n"
            else:
                for position, responses in positions.items():
                    agents = [r.agent_name for r in responses]
                    avg_confidence = sum(r.confidence for r in responses) / len(responses)
                    summary += f"**Position ({', '.join(agents)}, avg confidence: {avg_confidence:.0f}%):**\n"
                    summary += f"{self._truncate(position, 200)}\n\n"

            summary += "\n"

        return summary

    def _extract_positions(self, responses: list[AgentResponse]) -> dict[str, list[AgentResponse]]:
        """Extract distinct positions from responses."""
        positions: dict[str, list[AgentResponse]] = {}

        for response in responses:
            # Use first 100 chars of answer as position key
            # In practice, you might use semantic similarity
            position_key = response.answer[:100].strip()
            if position_key not in positions:
                positions[position_key] = []
            positions[position_key].append(response)

        return positions

    def _format_consensus_status(self, level: ConsensusLevel) -> str:
        """Format the current consensus status."""
        status_messages = {
            ConsensusLevel.STRONG: (
                "## Current Status: Strong Consensus\n\n"
                "The group has reached strong agreement. Consider whether your "
                "position aligns with the consensus or if you have compelling "
                "reasons to maintain a different view.\n\n"
            ),
            ConsensusLevel.MODERATE: (
                "## Current Status: Moderate Consensus\n\n"
                "There is general agreement among participants, though some "
                "uncertainty remains. Focus on clarifying any remaining points "
                "of disagreement.\n\n"
            ),
            ConsensusLevel.WEAK: (
                "## Current Status: Weak Consensus\n\n"
                "A slight majority agrees, but confidence is mixed. Consider "
                "the strongest arguments from each side and refine your position.\n\n"
            ),
            ConsensusLevel.DEADLOCK: (
                "## Current Status: No Consensus\n\n"
                "Participants hold different views. Focus on:\n"
                "- Identifying the core disagreements\n"
                "- Evaluating the strength of competing arguments\n"
                "- Finding common ground where possible\n\n"
            ),
        }
        return status_messages.get(level, "")

    def _get_round_instructions(
        self,
        current_round: int,
        consensus_level: ConsensusLevel | None,
    ) -> str:
        """Get instructions specific to the current round."""
        base_instructions = """
## Instructions for This Round

Having reviewed the previous discussion:

1. **Evaluate Arguments**: Consider the strongest points from each perspective
2. **Update Your Position**: Adjust your view if compelling arguments warrant it
3. **Explain Changes**: If your position changed, explain why
4. **Maintain Integrity**: Don't change position just to achieve consensus
5. **Update Confidence**: Reflect new information in your confidence score

"""
        if current_round >= 3:
            base_instructions += """
**Final Round Notice**: This is a late round. Focus on:
- Crystallizing the key insights from the debate
- Clearly stating areas of agreement and remaining disagreement
- Providing a definitive answer with appropriate confidence

"""

        if consensus_level == ConsensusLevel.DEADLOCK:
            base_instructions += """
**Deadlock Resolution**: Since no consensus has emerged:
- Identify the fundamental source of disagreement
- Propose a synthesis or compromise if appropriate
- If synthesis isn't possible, clearly articulate why positions remain irreconcilable

"""

        return base_instructions

    def _truncate(self, text: str, max_length: int) -> str:
        """Truncate text to max length with ellipsis."""
        if len(text) <= max_length:
            return text
        return text[: max_length - 3] + "..."

    def generate_synthesis_prompt(
        self,
        question: str,
        rounds: list[DebateRound],
        final_consensus: ConsensusLevel,
    ) -> str:
        """
        Generate a prompt for synthesizing the final answer.

        Used when the orchestrator needs to compile the final result
        from multiple agent perspectives.
        """
        prompt = f"""## Debate Synthesis Required

**Original Question**: {question}

**Debate Summary**:
- Total Rounds: {len(rounds)}
- Final Consensus Level: {final_consensus.value}

"""

        # Add key points from each round
        for round_data in rounds:
            prompt += f"### Round {round_data.round_number + 1}\n"
            for response in round_data.responses:
                prompt += f"- **{response.agent_name}** (confidence: {response.confidence}%): "
                prompt += f"{self._truncate(response.answer, 100)}\n"
            prompt += "\n"

        prompt += """
## Synthesis Task

Based on the complete debate above, provide:
1. **Final Answer**: The synthesized conclusion incorporating all perspectives
2. **Confidence**: Overall confidence in this answer (0-100)
3. **Key Insights**: Main points of agreement
4. **Remaining Uncertainties**: Areas where disagreement persists
5. **Dissenting Views**: Important minority positions that should be noted
"""

        return prompt
