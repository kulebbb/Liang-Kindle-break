@echo off
setlocal
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
cd /d "%~dp0.."
echo Starting Bookdrop...
python "%~dp0bookdrop.py" %*
if errorlevel 1 pause
endlocal
