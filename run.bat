@echo off
REM Single-click launcher for Windows
REM Starts Ollama in the background (if not already running), then opens TheLocalTutor.

REM Check if Ollama is already running
curl -s --max-time 2 http://localhost:11434/api/tags >nul 2>&1
if %errorlevel% neq 0 (
  echo Starting Ollama...
  start "" ollama serve
  REM Wait for it to come up
  timeout /t 5 /nobreak >nul
)

echo Launching TheLocalTutor...
start "" thelocaltutor
