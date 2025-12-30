"""Prompt templates for analysis copy (multi-sport, non-technical).

These prompts are intended to produce consistent, user-friendly copy for the
analysis detail page redesign. They avoid technical jargon and focus on what a
user should do next.

Important:
- Do not mention models/algorithms/data sources in generated copy.
- Keep outputs concise and decision-focused.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List


@dataclass(frozen=True)
class AnalysisPromptTemplates:
    """Container for all analysis prompt templates."""

    MASTER_ANALYSIS_PROMPT: str = (
        "You are an expert sports analyst writing for everyday users.\n\n"
        "Your goal:\n"
        "Be clear\n"
        "Be confident\n"
        "Be concise\n"
        "Avoid technical jargon\n"
        "Never mention:\n"
        "Models\n"
        "Algorithms\n"
        "Data sources\n"
        "Percentages unless explicitly requested\n"
        "Tone:\n"
        "Confident\n"
        "Neutral\n"
        "Helpful\n"
        "Always explain what the information means for the user.\n"
    )

    @staticmethod
    def quick_take_prompt(
        *,
        sport: str,
        home_team: str,
        away_team: str,
        favored_team: str,
        confidence_percent: int,
        risk_level: str,
        key_factors: List[str],
    ) -> str:
        return (
            'Generate a "Quick Take" for the following matchup.\n\n'
            "Inputs:\n"
            f"Sport: {sport}\n"
            f"Home Team: {home_team}\n"
            f"Away Team: {away_team}\n"
            f"Favored Team: {favored_team}\n"
            f"Confidence Percentage: {confidence_percent}\n"
            f"Risk Level: {risk_level}\n"
            f"Primary Reasoning Points: {key_factors}\n"
            "\n"
            "Output format:\n"
            "🏈 Quick Take\n"
            "AI favors: {favored_team}\n"
            "Confidence: {Low | Medium | High} ({confidence_percent}%)\n"
            "Risk level: {risk_level}\n"
            "Recommended action:\n"
            "{short recommendation}\n"
            "Why:\n"
            "{1–2 sentences explaining the main edge in plain English}\n"
            "\n"
            "Rules:\n"
            "No jargon\n"
            "No stats\n"
            "No bullet points\n"
            "Max 70 words total\n"
        )

    @staticmethod
    def key_drivers_prompt(*, positive_factors: List[str], risk_factors: List[str]) -> str:
        return (
            "Summarize the top reasons behind this prediction.\n\n"
            "Inputs:\n"
            f"Positive Factors: {positive_factors}\n"
            f"Risk Factors: {risk_factors}\n"
            "\n"
            "Output format:\n"
            "Top Factors Driving This Pick\n"
            "{positive factor}\n"
            "{positive factor}\n"
            "− {risk factor}\n"
            "\n"
            "Rules:\n"
            "Max 3 bullets\n"
            "Always include at least one risk\n"
            "Each bullet under 12 words\n"
        )

    @staticmethod
    def probability_explanation_prompt(*, favored_probability: int) -> str:
        return (
            "Explain win probability in plain English.\n\n"
            "Inputs:\n"
            f"Favored Team Probability: {favored_probability}\n"
            "\n"
            "Output:\n"
            "One sentence explaining what this probability means for a typical user.\n"
            "\n"
            "Rules:\n"
            "Do not explain math\n"
            "Do not mention models\n"
            "Use friendly language\n"
        )

    @staticmethod
    def bet_option_prompt(
        *,
        bet_type: str,
        lean: str,
        confidence_level: str,
        risk_level: str,
        summary: str,
    ) -> str:
        return (
            "Generate a betting insight for this option.\n\n"
            "Inputs:\n"
            f"Bet Type: {bet_type}\n"
            f"Lean: {lean}\n"
            f"Confidence Level: {confidence_level}\n"
            f"Risk Level: {risk_level}\n"
            f"Reasoning Summary: {summary}\n"
            "\n"
            "Output format:\n"
            "AI Lean: {side}\n"
            "\n"
            "Confidence: {Confidence Level}\n"
            "Risk: {Risk Level}\n"
            "Explanation:\n"
            "{1 short sentence explaining why}\n"
            "\n"
            "Rules:\n"
            "Max 40 words\n"
            "No stats\n"
            "One recommendation only\n"
        )

    @staticmethod
    def matchup_breakdown_prompt(
        *,
        unit_a: str,
        unit_b: str,
        strengths: Iterable[str],
        weaknesses: Iterable[str],
    ) -> str:
        strengths_list = ", ".join([str(x).strip() for x in strengths if str(x).strip()][:6])
        weaknesses_list = ", ".join([str(x).strip() for x in weaknesses if str(x).strip()][:6])
        return (
            "Explain the matchup in simple terms.\n\n"
            "Inputs:\n"
            f"Unit A: {unit_a}\n"
            f"Unit B: {unit_b}\n"
            f"Key Strengths: {strengths_list}\n"
            f"Key Weaknesses: {weaknesses_list}\n"
            "\n"
            "Output format:\n"
            "{Unit A} vs {Unit B}\n"
            "\n"
            "Summary:\n"
            "{1 sentence overview}\n"
            "Key Notes:\n"
            "• {insight}\n"
            "• {insight}\n"
            "\n"
            "Rules:\n"
            "Max 3 bullets\n"
            "Plain English\n"
            "No percentages\n"
        )

    @staticmethod
    def trends_prompt(*, recent_form: str, home_away_context: str, situational_notes: str) -> str:
        return (
            "Summarize relevant trends.\n\n"
            "Inputs:\n"
            f"Recent Form\n{recent_form}\n"
            f"Home/Away Context\n{home_away_context}\n"
            f"Situational Notes\n{situational_notes}\n"
            "\n"
            "Output:\n"
            "3 concise bullet points explaining what trends suggest.\n"
            "\n"
            "Rules:\n"
            "Each bullet < 15 words\n"
            "No historical deep dives\n"
        )


