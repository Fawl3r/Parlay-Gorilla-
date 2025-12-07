@echo off
REM Run mixed sports parlay tests
echo ============================================================
echo Running Mixed Sports Parlay Tests
echo ============================================================
echo.

REM Unit tests (don't need server)
echo Running Unit Tests...
python -m pytest test_mixed_sports_parlay.py::TestMixedSportsParlayBuilderUnit test_mixed_sports_parlay.py::TestParlaySchemas -v --tb=short

echo.
echo ============================================================
echo Unit tests complete. Running API integration tests...
echo (Make sure the backend server is running on localhost:8000)
echo ============================================================
echo.

REM API tests (need server running)
python -m pytest test_mixed_sports_parlay.py::TestMixedSportsParlayAPI -v --tb=short -x

echo.
echo ============================================================
echo All tests complete!
echo ============================================================

