@echo off
echo Installing dependencies...
pip install -r requirements.txt
playwright install chromium

echo Starting HH Scraper...
python -m uvicorn backend.main:app --reload
pause
