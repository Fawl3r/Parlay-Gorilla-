"""OpenAI service wrapper"""

from openai import AsyncOpenAI
from typing import List, Dict, Any
from app.core.config import settings
import json
import asyncio

from app.services.ai_text_sanitizer import AiTextSanitizer


class _DisabledChatCompletions:
    async def create(self, *args, **kwargs):  # pragma: no cover
        raise RuntimeError("OpenAI is disabled (set OPENAI_ENABLED=true to enable).")


class _DisabledChat:
    def __init__(self):  # pragma: no cover
        self.completions = _DisabledChatCompletions()


class _DisabledOpenAIClient:
    def __init__(self):  # pragma: no cover
        self.chat = _DisabledChat()


class OpenAIService:
    """OpenAI service for generating explanations and analysis"""
    
    def __init__(self):
        self._enabled = bool(getattr(settings, "openai_enabled", True)) and bool(settings.openai_api_key)
        self.client = AsyncOpenAI(api_key=settings.openai_api_key) if self._enabled else _DisabledOpenAIClient()
        self.model = "gpt-4o-mini"  # Using mini model for cost efficiency
        self._sanitizer = AiTextSanitizer()
    
    async def generate_parlay_explanation(
        self,
        legs: List[Dict],
        risk_profile: str,
        parlay_probability: float,
        overall_confidence: float
    ) -> Dict:
        """
        Generate AI explanation for a parlay
        
        Args:
            legs: List of parlay legs with game info
            risk_profile: User's risk profile (conservative, balanced, degen)
            parlay_probability: Overall parlay hit probability
            overall_confidence: Average confidence score
            
        Returns:
            Dictionary with 'summary' and 'risk_notes'
        """
        if not self._enabled:
            return {
                "summary": f"This {len(legs)}-leg parlay has a {parlay_probability:.1%} chance of hitting. Each leg was selected based on probability analysis and confidence scores.",
                "risk_notes": f"Risk Profile: {risk_profile}. Overall confidence: {overall_confidence:.1f}%. Remember: All betting involves risk. Never wager more than you can afford to lose.",
            }
        # Build prompt
        legs_text = "\n".join(
            [
                f"{leg['game']} | {leg['market_type'].upper()} | Pick: {leg['outcome']} | Odds {leg['odds']} | Model confidence {leg['confidence']:.1f}%"
                for leg in legs
            ]
        )
        
        prompt = f"""You are Parlay Gorilla, a professional sports betting analyst. Analyze this {len(legs)}-leg parlay and write like a real analyst previewing the slate.

CRITICAL FORMAT RULES:
Output plain text only.
Do not use markdown formatting (no bold markers, no bullet lists, no numbered lists, no markdown headings).
Do not use asterisks for formatting.
Do not invent injuries, quotes, or statistics that are not provided below.
Base your reasoning on the leg details (market, pick, odds) and the model confidence, plus general matchup dynamics.

LEG DETAILS:
{legs_text}

Risk Profile: {risk_profile}
Overall Hit Probability: {parlay_probability:.1%}
Average Confidence: {overall_confidence:.1f}%

Write two sections.

SUMMARY:
Start with one short intro paragraph framing the parlay and the risk profile.
Then write one short paragraph per leg. Each leg paragraph must begin with: "<Matchup> — Pick: <pick> (Odds <odds>, Confidence <confidence>)." Follow with 1-2 sentences of rationale.

RISK_NOTES:
Write one paragraph identifying the biggest swing leg(s) and why (variance, matchup volatility, market type, or lower confidence).
Then add one short bankroll/responsible gambling reminder (one sentence).

Format your response as:
SUMMARY: [your summary]
RISK_NOTES: [your risk analysis]"""

        try:
            # Add timeout to prevent hanging (30 seconds max)
            response = await asyncio.wait_for(
                self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "You are a veteran sports betting analyst. "
                                "Write clean, professional prose. Use complete sentences. "
                                "Plain text only; no markdown formatting, no emojis, no slang."
                            )
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=0.4,
                    max_tokens=800,
                ),
                timeout=30.0  # 30 second timeout for OpenAI calls
            )
            
            content = response.choices[0].message.content
            
            # Parse response
            summary = ""
            risk_notes = ""
            
            if "SUMMARY:" in content:
                parts = content.split("RISK_NOTES:")
                summary = parts[0].replace("SUMMARY:", "").strip()
                if len(parts) > 1:
                    risk_notes = parts[1].strip()
            else:
                # Fallback: split by paragraphs
                paragraphs = content.split("\n\n")
                summary = "\n\n".join(paragraphs[:len(paragraphs)//2])
                risk_notes = "\n\n".join(paragraphs[len(paragraphs)//2:])

            summary = self._sanitizer.sanitize(summary or content[:400])
            risk_notes = self._sanitizer.sanitize(
                risk_notes or "Please bet responsibly. Never wager more than you can afford to lose."
            )
            
            return {
                "summary": summary,
                "risk_notes": risk_notes,
            }
            
        except asyncio.TimeoutError:
            print("[OpenAIService] OpenAI request timed out after 30 seconds")
            # Fallback if OpenAI times out
            return {
                "summary": f"This {len(legs)}-leg parlay has a {parlay_probability:.1%} chance of hitting. Each leg was selected based on probability analysis and confidence scores.",
                "risk_notes": f"Risk Profile: {risk_profile}. Overall confidence: {overall_confidence:.1f}%. Remember: All betting involves risk. Never wager more than you can afford to lose."
            }
        except Exception as e:
            print(f"[OpenAIService] OpenAI request failed: {e}")
            # Fallback if OpenAI fails
            return {
                "summary": f"This {len(legs)}-leg parlay has a {parlay_probability:.1%} chance of hitting. Each leg was selected based on probability analysis and confidence scores.",
                "risk_notes": f"Risk Profile: {risk_profile}. Overall confidence: {overall_confidence:.1f}%. Remember: All betting involves risk. Never wager more than you can afford to lose."
            }

    async def generate_triple_parlay_explanations(
        self,
        triple_data: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Dict[str, str]]:
        """
        Generate explanations for safe/balanced/degen parlays in one structured JSON response.
        """
        if not self._enabled:
            fallback = {}
            for profile_name in ["safe", "balanced", "degen"]:
                fallback[profile_name] = {
                    "summary": f"{profile_name.title()} parlay assembled using probability-driven leg selection.",
                    "risk_notes": "AI explanations are disabled. Bet responsibly.",
                    "highlight_leg": "N/A",
                }
            return fallback
        sections = []
        for profile_name, block in triple_data.items():
            parlay = block.get("parlay", {})
            config = block.get("config", {})
            legs = parlay.get("legs", [])
            leg_lines = "\n".join(
                [
                    f"{leg.get('game')} | {leg.get('market_type', '').upper()} | Pick: {leg.get('outcome')} | Odds {leg.get('odds')} | Confidence {leg.get('confidence', 0):.1f}%"
                    for leg in legs
                ]
            ) or "No legs available."
            sections.append(
                f"""{profile_name.upper()} PARLAY:
LENGTH: {parlay.get('num_legs')} legs
SPORT: {config.get('sport', 'N/A')}
RISK_PROFILE: {config.get('risk_profile', profile_name)}
HIT_PROBABILITY: {parlay.get('parlay_hit_prob', 0):.3f}
CONFIDENCE: {parlay.get('overall_confidence', 0):.1f}%
LEGS:
{leg_lines}
"""
            )
        
        prompt = f"""You are Parlay Gorilla, an honest sports betting analyst. You will receive three parlay descriptions (SAFE, BALANCED, DEGEN).
For EACH parlay, return structured JSON with this exact schema:
{{
  "safe": {{"summary": "...", "risk_notes": "...", "highlight_leg": "..."}},
  "balanced": {{"summary": "...", "risk_notes": "...", "highlight_leg": "..."}},
  "degen": {{"summary": "...", "risk_notes": "...", "highlight_leg": "..."}}
}}

Rules:
- Provide concise summaries (2-3 sentences) and specific risk notes.
- highlight_leg should name the riskiest or most pivotal leg and explain why in <= 1 sentence.
- Output VALID JSON ONLY. Do not wrap in markdown. Do not add commentary outside JSON.
- IMPORTANT: The string fields MUST be plain text (no markdown formatting like **bold**, no bullet/numbered lists, no asterisks).

Parlay data:
{"\n".join(sections)}
"""

        try:
            # Add timeout to prevent hanging (45 seconds max for triple parlays)
            response = await asyncio.wait_for(
                self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "You are a professional sports betting analyst. "
                                "Be honest, data-driven, concise, and always emphasize responsible gambling. "
                                "Output valid JSON exactly matching the requested schema."
                            ),
                        },
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.7,
                    max_tokens=1200,
                ),
                timeout=45.0  # 45 second timeout for triple parlay explanations
            )
            content = response.choices[0].message.content.strip()
            parsed = json.loads(content)
            # Ensure required keys exist
            result = {}
            for profile in ["safe", "balanced", "degen"]:
                entry = parsed.get(profile, {})
                summary = self._sanitizer.sanitize(entry.get("summary") or "")
                risk_notes = self._sanitizer.sanitize(entry.get("risk_notes") or "")
                highlight_leg = self._sanitizer.sanitize(entry.get("highlight_leg") or "")
                result[profile] = {
                    "summary": summary or "No summary provided.",
                    "risk_notes": risk_notes or "Risk notes unavailable.",
                    "highlight_leg": highlight_leg or "No highlight available.",
                }
            return result
        except asyncio.TimeoutError:
            print("[OpenAIService] Triple parlay explanation timed out after 45 seconds")
            # Fallback: provide generic notes
            fallback = {}
            for profile_name in ["safe", "balanced", "degen"]:
                fallback[profile_name] = {
                    "summary": f"{profile_name.title()} parlay assembled using probability-driven leg selection.",
                    "risk_notes": "Unable to fetch detailed AI analysis. Bet responsibly.",
                    "highlight_leg": "N/A",
                }
            return fallback
        except Exception as exc:
            print(f"[OpenAIService] Triple explanation failed: {exc}")
            # Fallback: provide generic notes
            fallback = {}
            for profile_name in ["safe", "balanced", "degen"]:
                fallback[profile_name] = {
                    "summary": f"{profile_name.title()} parlay assembled using probability-driven leg selection.",
                    "risk_notes": "Unable to fetch detailed AI analysis. Bet responsibly.",
                    "highlight_leg": "N/A",
                }
            return fallback

    async def generate_custom_parlay_analysis(
        self,
        legs: List[Dict],
        combined_ai_probability: float,
        overall_confidence: float,
        weak_legs: List[str],
        strong_legs: List[str]
    ) -> Dict[str, str]:
        """
        Generate AI analysis for a user-built custom parlay.
        
        Args:
            legs: List of leg dictionaries with game, pick, confidence, etc.
            combined_ai_probability: Combined AI-calculated probability
            overall_confidence: Overall confidence score
            weak_legs: List of weak leg descriptions
            strong_legs: List of strong leg descriptions
        
        Returns:
            Dictionary with 'summary' and 'risk_notes'
        """
        if not self._enabled:
            confidence_text = (
                "high" if overall_confidence >= 60 else "moderate" if overall_confidence >= 40 else "risky"
            )
            weak_warning = f" Watch out for: {', '.join(weak_legs[:2])}." if weak_legs else ""
            return {
                "summary": (
                    f"This {len(legs)}-leg parlay has a {combined_ai_probability:.2f}% combined probability according to our model. "
                    f"The overall confidence is {confidence_text} at {overall_confidence:.1f}/100.{weak_warning}"
                ),
                "risk_notes": (
                    f"With {len(legs)} legs, this parlay carries inherent risk. "
                    f"Consider the {len(weak_legs)} leg(s) flagged as concerns. "
                    "Never bet more than you can afford to lose."
                ),
            }
        legs_text = "\n".join(
            [
                f"{leg['game']} | Pick: {leg['pick']} | Odds {leg['odds']} | AI Prob {leg['ai_probability']:.1f}% | Confidence {leg['confidence']:.1f}% | Recommendation {leg['recommendation']}"
                for leg in legs
            ]
        )
        
        weak_text = "\n".join(weak_legs) if weak_legs else "None identified"
        strong_text = "\n".join(strong_legs) if strong_legs else "None identified"
        
        prompt = f"""You are Parlay Gorilla, a professional sports betting analyst. A user has built their own custom {len(legs)}-leg parlay. Write a clean, professional assessment.

CRITICAL FORMAT RULES:
Output plain text only.
Do not use markdown formatting (no bold markers, no bullet lists, no numbered lists, no asterisks).
Do not invent injuries, quotes, or statistics that are not provided below.

USER'S PICKS:
{legs_text}

ANALYSIS METRICS:
Combined AI Probability: {combined_ai_probability:.2f}%
Overall Confidence Score: {overall_confidence:.1f}/100
Number of Legs: {len(legs)}

WEAK LEGS (concerns):
{weak_text}

STRONG LEGS (high confidence):
{strong_text}

Provide an honest, helpful analysis.

SUMMARY: Give a concise assessment of the overall parlay (3-4 sentences). Mention the strongest pick and any concerning picks. Be supportive but honest about the odds.

RISK_NOTES: Identify specific risks and concerns. If there are weak legs, explain why. Suggest if any legs should be reconsidered. End with a responsible gambling reminder.

Format your response as:
SUMMARY: [your analysis]
RISK_NOTES: [specific risks and advice]"""

        try:
            # Add timeout to prevent hanging (30 seconds max)
            response = await asyncio.wait_for(
                self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "You are a professional sports betting analyst known as Parlay Gorilla. "
                                "Be honest and constructive. When a user's picks are risky, say so clearly "
                                "but supportively. Focus on actionable insights. Always promote responsible gambling."
                            )
                        },
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=600,
                ),
                timeout=30.0  # 30 second timeout for custom parlay analysis
            )
            
            content = response.choices[0].message.content
            
            # Parse response
            summary = ""
            risk_notes = ""
            
            if "SUMMARY:" in content:
                parts = content.split("RISK_NOTES:")
                summary = parts[0].replace("SUMMARY:", "").strip()
                if len(parts) > 1:
                    risk_notes = parts[1].strip()
            else:
                paragraphs = content.split("\n\n")
                summary = "\n\n".join(paragraphs[:len(paragraphs)//2])
                risk_notes = "\n\n".join(paragraphs[len(paragraphs)//2:])

            summary = self._sanitizer.sanitize(summary or content[:500])
            risk_notes = self._sanitizer.sanitize(
                risk_notes or "Always bet responsibly. Never wager more than you can afford to lose."
            )
            
            return {
                "summary": summary,
                "risk_notes": risk_notes,
            }
            
        except asyncio.TimeoutError:
            print("[OpenAIService] Custom parlay analysis timed out after 30 seconds")
            # Provide informative fallback
            confidence_text = "high" if overall_confidence >= 60 else "moderate" if overall_confidence >= 40 else "risky"
            weak_warning = f" Watch out for: {', '.join(weak_legs[:2])}." if weak_legs else ""
            
            return {
                "summary": f"This {len(legs)}-leg parlay has a {combined_ai_probability:.2f}% combined probability according to our model. The overall confidence is {confidence_text} at {overall_confidence:.1f}/100.{weak_warning}",
                "risk_notes": f"With {len(legs)} legs, this parlay carries inherent risk. Each leg must hit for the parlay to win. Consider the {len(weak_legs)} leg(s) flagged as concerns. Never bet more than you can afford to lose."
            }
        except Exception as e:
            print(f"[OpenAIService] Custom parlay analysis failed: {e}")
            # Provide informative fallback
            confidence_text = "high" if overall_confidence >= 60 else "moderate" if overall_confidence >= 40 else "risky"
            weak_warning = f" Watch out for: {', '.join(weak_legs[:2])}." if weak_legs else ""
            
            return {
                "summary": f"This {len(legs)}-leg parlay has a {combined_ai_probability:.2f}% combined probability according to our model. The overall confidence is {confidence_text} at {overall_confidence:.1f}/100.{weak_warning}",
                "risk_notes": f"With {len(legs)} legs, this parlay carries inherent risk. Each leg must hit for the parlay to win. Consider the {len(weak_legs)} leg(s) flagged as concerns. Never bet more than you can afford to lose."
            }
