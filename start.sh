#!/bin/bash
# Exit on error
set -e

echo "Starting LazyMorning Backend (FastAPI)..."
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 &

echo "Starting LazyMorning Frontend (Streamlit) on port ${PORT:-8501}..."
python -m streamlit run frontend/app.py --server.port "${PORT:-8501}" --server.address 0.0.0.0 --server.headless true
