@echo off
title Menjalankan Dashboard Kehamilan & Chatbot Ollama
echo ========================================================
echo    DASHBOARD MONITORING KEHAMILAN (KRR, KRT, KRST)
echo            DENGAN ASISTEN AI OLLAMA
echo ========================================================
echo.
echo [1/2] Memeriksa instalasi paket Python...
python -c "import streamlit, pandas, plotly, requests" 2>nul
if %errorlevel% neq 0 (
    echo Menginstall paket yang dibutuhkan...
    pip install streamlit pandas plotly requests
)
echo Paket siap!
echo.
echo [2/2] Membuka Dashboard di Browser...
echo Dashboard berjalan di: http://localhost:8501
echo.
python -m streamlit run app.py
pause
