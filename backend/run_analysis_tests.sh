#!/bin/bash

echo "============================================================"
echo "Parlay Gorilla Analysis System - Test Suite"
echo "============================================================"
echo

cd "$(dirname "$0")"

echo "Running Model Tests..."
python test_analysis_models.py
if [ $? -ne 0 ]; then
    echo "Model tests failed!"
    exit 1
fi

echo
echo "Running Stats Scraper Tests..."
python test_stats_scraper.py
if [ $? -ne 0 ]; then
    echo "Stats scraper tests failed!"
    exit 1
fi

echo
echo "Running Analysis Generator Tests..."
python test_analysis_generator.py
if [ $? -ne 0 ]; then
    echo "Analysis generator tests failed!"
    exit 1
fi

echo
echo "Running API Route Tests..."
python test_analysis_api.py
if [ $? -ne 0 ]; then
    echo "API route tests failed!"
    exit 1
fi

echo
echo "Running Frontend Component Verification..."
python test_frontend_components.py
if [ $? -ne 0 ]; then
    echo "Frontend verification failed!"
    exit 1
fi

echo
echo "============================================================"
echo "Running Comprehensive Test Suite..."
echo "============================================================"
python test_analysis_all.py

echo
echo "============================================================"
echo "All Analysis System Tests Complete!"
echo "============================================================"

