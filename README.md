# TheLocalTutor

An offline AI-powered desktop study assistant. Import your lecture PDFs and PowerPoints, generate practice questions using a local AI model, and track your performance — no internet required.

## Requirements

- Python 3.11+
- [Ollama](https://ollama.com) installed and running locally
- At least one Ollama model pulled (e.g. `ollama pull llama3.2`)

## Setup

```bash
cd TheLocalTutor
pip install -e .
```

## Running

```bash
thelocaltutor
```

Or directly:

```bash
python -m thelocaltutor.app
```

## Supported Formats

- PDF (`.pdf`)
- PowerPoint (`.pptx`)

## AI

TheLocalTutor uses [Ollama](https://ollama.com) for local AI inference. Ollama must be running (`ollama serve`) before generating questions. Configure the model in Settings.
