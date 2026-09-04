#!/usr/bin/env bash
# Single-click launcher for macOS / Linux
# Starts Ollama in the background (if not already running), then opens TheLocalTutor.

set -e

# Start Ollama if it isn't already running
if ! curl -s --max-time 2 http://localhost:11434/api/tags >/dev/null 2>&1; then
  echo "Starting Ollama…"
  (ollama serve >/dev/null 2>&1 &)
  # Wait for it to come up
  for i in $(seq 1 15); do
    if curl -s --max-time 1 http://localhost:11434/api/tags >/dev/null 2>&1; then
      break
    fi
    sleep 1
  done
fi

echo "Launching TheLocalTutor…"
exec thelocaltutor
