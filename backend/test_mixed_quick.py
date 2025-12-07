"""Quick test for mixed sports parlay API."""
import asyncio
import httpx
import json

async def test_mixed_sports():
    print("Testing Mixed Sports Parlay API...")
    print("=" * 60)
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        # Test mixed NFL + NBA parlay
        response = await client.post(
            "http://localhost:8000/api/parlay/suggest",
            json={
                "num_legs": 5,
                "risk_profile": "balanced",
                "sports": ["NFL", "NBA"],
                "mix_sports": True
            }
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            legs = data.get("legs", [])
            print(f"Generated {len(legs)} legs")
            
            sport_counts = {}
            for leg in legs:
                sport = leg.get("sport", "NFL")
                sport_counts[sport] = sport_counts.get(sport, 0) + 1
                game = leg.get("game", "Unknown")
                pick = leg.get("outcome", "")
                conf = leg.get("confidence", 0)
                print(f"  [{sport}] {game} - {pick} ({conf:.1f}% conf)")
            
            print(f"\nSports distribution: {sport_counts}")
            print(f"Overall confidence: {data.get('overall_confidence', 0):.1f}%")
            print(f"Hit probability: {data.get('parlay_hit_prob', 0) * 100:.2f}%")
            print("\n✓ SUCCESS: Mixed sports parlay working!")
        else:
            print(f"Error: {response.text[:500]}")

if __name__ == "__main__":
    asyncio.run(test_mixed_sports())

