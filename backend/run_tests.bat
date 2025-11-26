@echo off
REM Test script runner for Windows

echo Running Games Endpoint Test...
python test_games_endpoint.py

echo.
echo Running Database Test...
python test_database_games.py

echo.
echo Running Odds API Test...
python test_odds_api.py

pause

