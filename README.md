# TheLocalTutor

> **An offline, AI-powered desktop study assistant that turns your lecture materials into interactive practice.**

TheLocalTutor is a native desktop application built with Python and PySide6 that helps students transform their existing **PDF and PowerPoint lecture materials** into structured study content and practice questions.

Instead of manually creating revision questions from lecture notes, students can import their materials, let a **locally running AI model** analyze the content, and use the generated questions to actively practice what they have learned.

The application is designed around a simple principle:

> **Your study materials should remain on your computer, and your AI assistant should work for you without requiring a cloud service.**

TheLocalTutor uses **Ollama for local AI inference**, meaning generated questions can be produced without sending lecture materials to a third-party AI API.

---

## ✨ Features

### 📚 Document Import

Import educational materials directly into your local study library.

Supported formats:

- `.pdf`
- `.pptx`

The application copies imported materials into its managed storage, registers them in the local database, and processes their contents for later question generation.

Duplicate filenames are handled automatically to prevent existing materials from being overwritten.

---

### 🧠 Local AI Question Generation

TheLocalTutor integrates with **Ollama** to perform AI inference locally.

Instead of relying on a hosted AI API, the application communicates with an Ollama instance running on the user's machine.

This provides:

- No cloud AI dependency
- No API key requirement
- Local inference
- Greater control over study materials
- A more privacy-conscious workflow

The AI model can be configured through the application's settings.

---

### 📝 Automatic Content Processing

Imported documents are parsed into structured pages and then divided into manageable text chunks.

The processing pipeline is approximately:

```text
Document
   │
   ▼
Parser
   │
   ▼
Parsed Pages
   │
   ▼
Text Chunking
   │
   ▼
Database
   │
   ▼
AI Question Generation
   │
   ▼
Practice Session
```

Chunking uses configurable chunk sizes and overlap so that larger documents can be processed as smaller, manageable units.

---

### 🎯 Practice Sessions

Generated questions can be used through the application's interactive practice interface.

The practice system provides the student with a dedicated environment for answering questions and reviewing their performance.

The UI is organized into separate widgets for different areas of the learning experience, including:

- Dashboard
- Library
- Materials
- Practice
- Progress
- Results
- Settings

---

### 📊 Progress Tracking

The application maintains local study information so students can review their performance over time.

The project includes dedicated database repositories and presentation components for:

- Materials
- Questions
- Study sessions
- Results
- Progress information

This allows the application to move beyond simple question generation and provide a persistent study workflow.

---

### 🗂️ Local Study Library

Imported materials are stored and managed locally.

The library allows students to organize their educational documents and access their existing study materials without repeatedly importing the same files.

Materials maintain metadata such as:

- Name
- File path
- File type
- Course
- Processing status
- Page count
- Chunk count

---

### ⚙️ Configurable Application

Core application behavior is centralized through the configuration layer.

The project includes configuration handling for application paths and processing parameters such as document chunk size and chunk overlap.

This makes the processing pipeline easier to tune without scattering configuration values throughout the codebase.

---

### 🎨 Native Desktop Interface

TheLocalTutor is a native desktop application built with **PySide6**.

The presentation layer is organized into reusable widgets, dialogs, workers, and styles rather than placing the entire UI inside a single file.

The application also uses a dedicated Qt stylesheet (`app_style.qss`) for visual customization.

---

### 🔄 Background Workers

Long-running operations such as importing and generating content are separated into worker components.

This allows potentially expensive operations to be performed without unnecessarily blocking the main desktop interface.

The presentation layer includes dedicated workers for:

- Material importing
- Question generation

---

## 🏗️ Architecture

TheLocalTutor follows a layered architecture designed to separate application concerns.

```text
┌──────────────────────────────────────────────┐
│                 Presentation                 │
│                                              │
│  PySide6 UI · Widgets · Dialogs · Workers   │
└──────────────────────┬───────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────┐
│                  Services                    │
│                                              │
│ Material Service · Question Service          │
│ Study Service                                │
└──────────────────────┬───────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────┐
│                   Domain                     │
│                                              │
│ Models · Material Types · Questions          │
│ Study Session Data                           │
└──────────────────────┬───────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────┐
│               Infrastructure                 │
│                                              │
│ PDF/PPTX Parsing · SQLite · Repositories     │
│ Ollama AI Provider                            │
└──────────────────────────────────────────────┘
```

This separation makes individual parts of the system easier to understand, test, replace, and maintain.

---

## 🧩 Project Structure

```text
TheLocalTutor/
│
├── data/
│   ├── generated/
│   └── materials/
│
├── src/
│   └── thelocaltutor/
│       │
│       ├── app.py
│       │
│       ├── core/
│       │   ├── config.py
│       │   ├── exceptions.py
│       │   └── logging_config.py
│       │
│       ├── domain/
│       │   └── models.py
│       │
│       ├── infrastructure/
│       │   │
│       │   ├── ai/
│       │   │   └── ollama_provider.py
│       │   │
│       │   ├── database/
│       │   │   ├── connection.py
│       │   │   ├── schema.py
│       │   │   └── repositories/
│       │   │       ├── material_repo.py
│       │   │       ├── question_repo.py
│       │   │       └── session_repo.py
│       │   │
│       │   └── document/
│       │       ├── base_parser.py
│       │       ├── pdf_parser.py
│       │       └── pptx_parser.py
│       │
│       ├── presentation/
│       │   ├── dialogs/
│       │   │   ├── generate_dialog.py
│       │   │   └── import_dialog.py
│       │   │
│       │   ├── styles/
│       │   │   └── app_style.qss
│       │   │
│       │   ├── widgets/
│       │   │   ├── dashboard_widget.py
│       │   │   ├── library_widget.py
│       │   │   ├── material_widget.py
│       │   │   ├── practice_widget.py
│       │   │   ├── progress_widget.py
│       │   │   ├── results_widget.py
│       │   │   ├── settings_widget.py
│       │   │   └── sidebar.py
│       │   │
│       │   ├── workers/
│       │   │   ├── generate_worker.py
│       │   │   └── import_worker.py
│       │   │
│       │   └── main_window.py
│       │
│       └── services/
│           ├── material_service.py
│           ├── question_service.py
│           └── study_service.py
│
├── pyproject.toml
├── run.bat
├── run.sh
├── README.md
├── LICENSE
└── .gitignore
```

---

# 🔬 How It Works

## 1. Import

The user selects a PDF or PowerPoint presentation.

```text
User
 │
 ▼
Import Dialog
 │
 ▼
Material Service
 │
 ▼
Managed Storage
 │
 ▼
Database Record
```

The material service validates the file extension and currently supports PDF and PPTX documents.

If a filename already exists in the managed materials directory, the application generates an alternative filename rather than overwriting the existing file.

---

## 2. Parse

Once imported, the document is processed using the appropriate parser.

```text
PDF  ─────────► PdfParser
                         │
                         ▼
                    Parsed Pages

PPTX ─────────► PptxParser
                         │
                         ▼
                    Parsed Pages
```

The document infrastructure provides a common parser abstraction while keeping format-specific logic in dedicated implementations.

---

## 3. Chunk

Parsed pages are divided into text chunks.

Conceptually:

```text
Page
 │
 ├── Chunk 1
 │
 ├── Chunk 2
 │
 ├── Chunk 3
 │
 └── ...
```

Chunk size and overlap are configurable through the application's configuration system.

Each chunk retains information such as:

- Material ID
- Page number
- Chunk index
- Text content

This creates a structured representation of the source material that can later be passed into the question-generation pipeline.

---

## 4. Store

The processed material and its chunks are persisted through the database layer.

The project separates database access into repositories, including:

```text
material_repo.py
question_repo.py
session_repo.py
```

This prevents the UI and service layers from having to directly manage database queries.

---

## 5. Generate

When the user requests generated questions, the application communicates with the configured local Ollama model.

```text
Study Material
      │
      ▼
Relevant Content
      │
      ▼
Question Service
      │
      ▼
Ollama Provider
      │
      ▼
Local LLM
      │
      ▼
Generated Questions
```

The AI integration is isolated behind the infrastructure layer, making the application architecture less tightly coupled to the AI provider itself.

---

## 6. Practice

Generated questions are presented through the practice interface.

The student answers questions within the application, after which the result can be recorded as part of a study session.

This creates a complete loop:

```text
Import
   ↓
Process
   ↓
Generate
   ↓
Practice
   ↓
Record Results
   ↓
Track Progress
```

---

# 🛠️ Technology Stack

| Technology | Purpose |
|---|---|
| **Python 3.11+** | Core application language |
| **PySide6** | Native desktop GUI |
| **Ollama** | Local AI inference |
| **PyMuPDF** | PDF parsing |
| **python-pptx** | PowerPoint parsing |
| **SQLite** | Local persistence |
| **Requests** | Communication with the local Ollama service |
| **Setuptools** | Python packaging |
| **pytest** | Testing |
| **pytest-qt** | Qt application testing |
| **Qt Style Sheets (QSS)** | Desktop UI styling |

The package configuration defines Python `>=3.11` and includes the runtime dependencies directly in `pyproject.toml`. Development dependencies include `pytest` and `pytest-qt`.

---

# 💻 Requirements

Before running TheLocalTutor, you need:

### Required

- Python **3.11 or newer**
- Ollama
- At least one Ollama model

For example:

```bash
ollama pull llama3.2
```

Ollama must be running locally when the application needs to generate questions.

---

# 🚀 Installation

## 1. Clone the repository

```bash
git clone https://github.com/onyedikachinzute/TheLocalTutor.git
cd TheLocalTutor
```

---

## 2. Create a virtual environment

### Windows

```bash
python -m venv .venv
.venv\Scripts\activate
```

### Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
```

---

## 3. Install TheLocalTutor

The project uses a modern `pyproject.toml` configuration and can be installed in editable mode:

```bash
pip install -e .
```

For development dependencies:

```bash
pip install -e ".[dev]"
```

---

## 4. Install and configure Ollama

Install Ollama for your operating system, then pull an available model.

For example:

```bash
ollama pull llama3.2
```

Make sure Ollama is running before attempting AI question generation.

---

# ▶️ Running the Application

After installation, the application can be launched using its installed command:

```bash
thelocaltutor
```

Alternatively:

```bash
python -m thelocaltutor.app
```

The repository also contains convenience launch scripts:

### Windows

```bash
run.bat
```

### Linux / macOS

```bash
./run.sh
```

The package entry point is defined as:

```text
thelocaltutor → thelocaltutor.app:main
```

The application initializes logging and the database schema before creating the PySide6 application window.

---

# 📖 Typical Workflow

A typical study session looks like this:

### Step 1 — Add your material

Import a lecture:

```text
Computer Networks.pdf
```

or:

```text
Data Structures.pptx
```

### Step 2 — Process it

TheLocalTutor extracts the document's content and converts it into structured chunks.

### Step 3 — Generate questions

Select the material and use the question-generation workflow.

The configured local Ollama model generates practice questions from the processed content.

### Step 4 — Practice

Open the practice interface and answer the generated questions.

### Step 5 — Review

View your results and track your performance through the application's progress features.

---

# 🔐 Privacy & Offline Design

One of the central design goals of TheLocalTutor is **local-first learning**.

The AI generation pipeline uses Ollama running locally rather than requiring a remote AI API.

This means your lecture materials do not need to be uploaded to an external AI provider simply to generate practice questions.

The application stores its study data locally as well.

### Important distinction

"Offline AI" does not mean that absolutely no internet connection is ever required.

You may need internet access to:

- Install Python packages
- Install Ollama
- Download an Ollama model
- Clone the repository

After the required software and model are installed, the core application can perform its AI workflow through the local Ollama service.

---

# 🧱 Design Principles

The project was built around several software engineering principles.

## Separation of concerns

Different responsibilities live in different layers.

```text
Presentation
     ↓
Services
     ↓
Domain
     ↓
Infrastructure
```

The UI should not need to know how a PDF is parsed or how a database query is constructed.

---

## Repository pattern

Database operations are separated into repositories for different entities.

This creates a cleaner boundary between application logic and persistence.

---

## Service layer

Application-level operations such as material processing and study workflows are handled through dedicated services.

For example:

```text
Material Service
Question Service
Study Service
```

This keeps business logic from becoming tightly coupled to the UI.

---

## Parser abstraction

Document processing is separated into parser implementations.

Currently:

```text
Base Parser
    │
    ├── PDF Parser
    │
    └── PPTX Parser
```

This makes the document-processing system easier to extend with additional formats in the future.

---

## Local AI abstraction

The Ollama integration lives under the infrastructure layer rather than being directly embedded throughout the UI.

This keeps AI-provider-specific code isolated from the rest of the application.

---

# 🧪 Testing

The project is configured to use **pytest** and **pytest-qt** for development and testing.

Test discovery is configured through `pyproject.toml`:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
```

Run the test suite with:

```bash
pytest
```

For more verbose output:

```bash
pytest -v
```

---

# 🧑‍💻 Development

Install the project with development dependencies:

```bash
pip install -e ".[dev]"
```

Then run:

```bash
pytest
```

The source package follows the `src` layout:

```text
src/
└── thelocaltutor/
```

This keeps the importable application package separate from project-level configuration and tooling.

---

# 📦 Packaging

The project uses `pyproject.toml` with Setuptools.

The package configuration defines:

```toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"
```

The package is discovered from:

```text
src/
```

and exposes the following command:

```bash
thelocaltutor
```

The current application version is:

```text
1.0.0
```

---

# 🗺️ Current Architecture at a Glance

```text
                         ┌───────────────────┐
                         │      Student      │
                         └─────────┬─────────┘
                                   │
                                   ▼
                         ┌───────────────────┐
                         │    PySide6 UI     │
                         │                   │
                         │ Dashboard         │
                         │ Library           │
                         │ Materials         │
                         │ Practice          │
                         │ Progress          │
                         │ Results           │
                         │ Settings          │
                         └─────────┬─────────┘
                                   │
                                   ▼
                         ┌───────────────────┐
                         │     Services      │
                         │                   │
                         │ Material          │
                         │ Question          │
                         │ Study             │
                         └───────┬───┬───────┘
                                 │   │
                    ┌────────────┘   └─────────────┐
                    ▼                              ▼
          ┌──────────────────┐           ┌──────────────────┐
          │   Document       │           │    Database      │
          │   Parsers        │           │                  │
          │                  │           │ SQLite           │
          │ PDF              │           │ Repositories     │
          │ PPTX             │           │ Sessions         │
          └────────┬─────────┘           └──────────────────┘
                   │
                   ▼
          ┌──────────────────┐
          │   Text Chunks    │
          └────────┬─────────┘
                   │
                   ▼
          ┌──────────────────┐
          │ Ollama Provider  │
          └────────┬─────────┘
                   │
                   ▼
          ┌──────────────────┐
          │   Local LLM      │
          └────────┬─────────┘
                   │
                   ▼
          ┌──────────────────┐
          │ Generated        │
          │ Questions        │
          └──────────────────┘
```

---

# 📁 Data Organization

The repository contains a local data hierarchy:

```text
data/
├── generated/
└── materials/
```

The application uses these locations as part of its local study-material workflow.

For a clean source repository, generated runtime data and temporary files should remain excluded from version control where appropriate.

---

# 🔮 Future Improvements

The architecture leaves room for several potential improvements.

Possible future directions include:

- Additional document formats
  - `.docx`
  - `.txt`
  - `.md`
- More question types
  - True/False
  - Fill-in-the-blank
  - Short answer
  - Essay
- Improved adaptive question difficulty
- More detailed learning analytics
- Spaced-repetition functionality
- Flashcard generation
- Search across imported materials
- Source/page references for generated questions
- Additional local LLM providers
- Model performance configuration
- Application packaging into standalone executables
- Automated release builds
- Expanded automated test coverage

---

# 🤝 Contributing

Contributions, suggestions, and improvements are welcome.

If you find a bug or have an idea for improving TheLocalTutor:

1. Fork the repository
2. Create a feature branch

```bash
git checkout -b feature/my-feature
```

3. Make your changes
4. Run the tests

```bash
pytest
```

5. Commit your changes

```bash
git commit -m "Add my feature"
```

6. Push the branch

```bash
git push origin feature/my-feature
```

7. Open a Pull Request

---

# 🐛 Issues & Feature Requests

If you encounter a bug or have an idea for a feature, please open an issue in the GitHub repository.

When reporting a bug, include:

- Operating system
- Python version
- Ollama version
- Ollama model
- Steps to reproduce the issue
- Relevant error output

---

# 📄 License

TheLocalTutor is distributed under the **MIT License**.

See [`LICENSE`](LICENSE) for the complete license text.

---

# 👨‍💻 Author

**Onyedikachi Nzute**

Computer Science student and Python developer interested in building practical software, local AI applications, and tools that solve real problems.

GitHub: [@onyedikachinzute](https://github.com/onyedikachinzute)

---

## ⭐ If TheLocalTutor is useful to you

If you find the project interesting, consider giving the repository a ⭐ on GitHub.

**TheLocalTutor — study smarter, keep your data local.**
