@echo off
echo Starting LazyMorning Frontend (Streamlit)...
python -m streamlit run frontend/app.py --server.port 8501 --server.headless false
pause
