@echo off
echo ============================================
echo   Financial Offer Generator (Streamlit)
echo ============================================
echo.

set ANACONDA=%USERPROFILE%\anaconda3
set PYTHON=%ANACONDA%\python.exe
set SCRIPTS=%ANACONDA%\Scripts

echo Python: %PYTHON%
echo.

echo Checking / installing dependencies...
"%SCRIPTS%\pip.exe" install streamlit python-docx --quiet
echo.

echo Starting app...
echo Your browser will open at http://localhost:8501
echo Press Ctrl+C to stop.
echo.

"%SCRIPTS%\streamlit.exe" run "%~dp0app.py"
pause
