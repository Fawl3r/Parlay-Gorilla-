"""OpenAI service wrapper"""

from openai import AsyncOpenAI
from typing import List, Dict, Any
from app.core.config import settings
import json


class OpenAIService:
    """OpenAI service for generating explanations and analysis"""
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = "gpt-4o-mini"  # Using mini model for cost efficiency
    
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
        # Build prompt
        legs_text = "\n".join([
            f"{i+1}. {leg['game']} - {leg['market_type'].upper()}: {leg['outcome']} "
            f"(Odds: {leg['odds']}, Confidence: {leg['confidence']:.1f}%)"
            for i, leg in enumerate(legs)
        ])
        
        prompt = f"""You are F3 Parlay AI, an honest sports betting analyst. Analyze this {len(legs)}-leg parlay:

{legs_text}

Risk Profile: {risk_profile}
Overall Hit Probability: {parlay_probability:.1%}
Average Confidence: {overall_confidence:.1f}%

Provide:
1. A brief summary explaining why each leg was chosen (2-3 sentences per leg)
2. Identify the highest-risk leg(s) and explain why
3. Overall parlay risk assessment
4. A clear reminder about responsible gambling

Format your response as:
SUMMARY: [your summary]
RISK_NOTES: [your risk analysis]"""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional sports betting analyst. Be honest, data-driven, and always emphasize responsible gambling."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=800,
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
            
            return {
                "summary": summary or content[:400],
                "risk_notes": risk_notes or "Please bet responsibly. Never wager more than you can afford to lose."
            }
            
        except Exception as e:
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
        sections = []
        for profile_name, block in triple_data.items():
            parlay = block.get("parlay", {})
            config = block.get("config", {})
            legs = parlay.get("legs", [])
            leg_lines = "\n".join([
                f"- {leg.get('game')} | {leg.get('market_type', '').upper()} | {leg.get('outcome')} "
                f"(Odds {leg.get('odds')}, Confidence {leg.get('confidence', 0):.1f}%)"
                for leg in legs
            ]) or "No legs available."
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
        
        prompt = f"""You are F3 Parlay AI, an honest sports betting analyst. You will receive three parlay descriptions (SAFE, BALANCED, DEGEN).
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

Parlay data:
{"\n".join(sections)}
"""

        try:
            response = await self.client.chat.completions.create(
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
            )
            content = response.choices[0].message.content.strip()
            parsed = json.loads(content)
            # Ensure required keys exist
            result = {}
            for profile in ["safe", "balanced", "degen"]:
                entry = parsed.get(profile, {})
                result[profile] = {
                    "summary": entry.get("summary") or "No summary provided.",
                    "risk_notes": entry.get("risk_notes") or "Risk notes unavailable.",
                    "highlight_leg": entry.get("highlight_leg") or "No highlight available.",
                }
            return result
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

