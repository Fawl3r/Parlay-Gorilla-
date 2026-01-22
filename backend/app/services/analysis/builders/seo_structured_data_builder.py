"""Build JSON-LD structured data for SEO."""

from typing import Dict, Any, Optional
from datetime import datetime


class SEOStructuredDataBuilder:
    """Generate JSON-LD structured data for search engines."""
    
    @staticmethod
    def build(
        *,
        game: Any,  # Game model
        analysis: Dict[str, Any],
        odds_snapshot: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Build JSON-LD structured data for SportsEvent schema.
        
        Returns:
            Dict with @context, @type, and all required fields for SportsEvent
        """
        home_team = game.home_team
        away_team = game.away_team
        start_time = game.start_time.isoformat() if hasattr(game.start_time, "isoformat") else str(game.start_time)
        
        # Build structured data
        structured_data = {
            "@context": "https://schema.org",
            "@type": "SportsEvent",
            "name": f"{away_team} vs {home_team}",
            "sport": game.sport,
            "startDate": start_time,
            "homeTeam": {
                "@type": "SportsTeam",
                "name": home_team,
            },
            "awayTeam": {
                "@type": "SportsTeam",
                "name": away_team,
            },
        }
        
        # Add location if available
        if hasattr(game, "venue") and game.venue:
            structured_data["location"] = {
                "@type": "Place",
                "name": game.venue,
            }
        
        # Add betting odds (if available)
        if odds_snapshot.get("home_ml") or odds_snapshot.get("away_ml"):
            structured_data["offers"] = []
            
            if odds_snapshot.get("home_ml"):
                structured_data["offers"].append({
                    "@type": "Offer",
                    "price": odds_snapshot["home_ml"],
                    "priceCurrency": "USD",
                    "name": f"{home_team} Moneyline",
                })
            
            if odds_snapshot.get("away_ml"):
                structured_data["offers"].append({
                    "@type": "Offer",
                    "price": odds_snapshot["away_ml"],
                    "priceCurrency": "USD",
                    "name": f"{away_team} Moneyline",
                })
        
        # Add description from analysis
        if analysis.get("opening_summary"):
            structured_data["description"] = analysis["opening_summary"][:200]  # Truncate for SEO
        
        return structured_data
