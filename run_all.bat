@echo off
echo ========================================================
echo   Starting LazyMorning — Your Overnight Life Assistant
echo ========================================================
start "LazyMorning Backend" cmd /k "python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload"
timeout /t 2 /nobreak >nul
start "LazyMorning Frontend" cmd /k "python -m streamlit run frontend/app.py --server.port 8501"
echo Services launched!
echo - Backend API Docs: http://127.0.0.1:8000/docs
echo - Frontend Dashboard: http://localhost:8501
