
# CAREERİNGO

A hackathon project focused on building career paths with tooling around LLaMA-style language models, GitHub / CV analysis agents, and a React frontend (Student Assistant Interface).

## Table of contents
- Project description and purpose
- Files & features (quick map)
- Installation instructions
- Usage guide (backend & frontend)
- Technologies used
- Security & configuration notes
- Team members
- Contributing
- Troubleshooting
- License & model weights
- Contact

---

## Project description and purpose

CAREERİNGO contains components to:
- Analyze GitHub profiles and repositories with an AI agent (metric extraction, README analysis, issue/pr analysis, code-review heuristics).
- Parse CVs and produce structured career reports (CV parsing + LLM generation).
- Provide a React-based student assistant frontend (Student Assistant Interface).
- Provide utilities and scripts that demonstrate LLM usage locally (LLM wrappers, tokenizers, model generate examples).

---

## Files & features (quick map)

Backend (Python)
- backend/ollamachat2.py — Interactive GitHub profile analyzer (prompts for username; generates textual report).
- backend/ollamachat3.py — More advanced analyzer class GitHubRepoAnalyzer with many helper methods (README analysis, issue communication, PR code-review analysis, scoring, AI deep analysis).
- backend/githubreal.py — Lightweight wrapper / small agent utilities and test code (includes `mainagent` and `minagent2` functions and a small test harness).
- backend/cv_mechanism/converter.py — CV parsing pipeline and `full_stream` function that tokenizes CV text and generates a detailed CV report with the model.
- backend/chat_stage/chat_stage.py — Chat pipeline helpers, PDF extraction utilities, chunking helpers, and FastAPI-related imports.
- backend/... (other helper modules) — check backend/ for scripts & helpers.

Frontend (React / TypeScript)
- frontend/README.md — quick start for the Student Assistant Interface.
- frontend/index.html — app entry.
- frontend/src/components/ — React components such as CVScore.tsx and a CareerTodoList component (Student Assistant UI parts).

Example entrypoints / behaviors found in code
- Running `python backend/ollamachat2.py` starts an interactive prompt asking for a GitHub username and then runs analysis.
- `backend/githubreal.py` contains a test harness under `if __name__ == "__main__":` which calls `mainagent()` with an example GitHub URL — running it will execute the example analysis.
- `backend/cv_mechanism/converter.py` defines `full_stream(link)` which runs tokenizer/model.generate to produce a structured CV report (this function can be invoked programmatically).

---

## Installation instructions

Prerequisites
- Python 3.8+ (3.10+ recommended)
- Node 16+/npm 8+ (for frontend)
- pip
- (Optional, for GPU) CUDA + NVIDIA drivers + cuDNN compatible with your PyTorch install
- Sufficient disk space for model weights and any vector DB indexes (Chroma)

Backend setup (recommended)
1. Clone the repository
   git clone https://github.com/AltanReisoglu/LLAMA-HACKATHON.git
   cd LLAMA-HACKATHON

2. Create and activate a virtual environment
   python -m venv .venv
   # macOS / Linux
   source .venv/bin/activate
   # Windows (PowerShell)
   .venv\Scripts\Activate.ps1

3. Install Python dependencies
   pip install -r requirements.txt

Frontend setup
1. cd frontend
2. npm install
3. npm run dev

---

## Usage guide

Configuration
- Put model weights where the backend scripts expect them, or configure a MODEL_PATH variable in your environment or config file.
- Set secrets and tokens as environment variables (see Security & configuration notes).

GitHub profile / repo analysis
- Interactive profile analyzer:
  1. Ensure `GITHUB_TOKEN` is set in env (recommended).
  2. Run:
     python backend/ollamachat2.py
     - The script will prompt: "🔍 GitHub kullanıcı adını girin:" — enter a username.

- Repository analyzer (programmatic / script test harness):
  1. Configure GITHUB_TOKEN in environment.
  2. Run the test harness:
     python backend/githubreal.py
     - This will run `mainagent()` with the sample GitHub URL present in the file when executed directly.

- There are advanced analyzer classes in backend/ollamachat3.py:
  - GitHubRepoAnalyzer.analyze_repo_comprehensive(owner, repo, use_llm_scoring=False)
  - generate_ai_deep_analysis(metrics)
  - print_analysis_report(metrics, ai_analysis)
  These methods are used in the repo to produce comprehensive repo reports via code.

CV parsing & report generation
- Programmatically call the converter:
  python -c "from backend.cv_mechanism.converter import full_stream; full_stream('path_or_url_to_cv')"
  - `full_stream` reads/parses the CV, calls the tokenizer and model, and prints a structured "Report:".
  - The function uses a tokenizer and a model.generate call with parameters (max_new_tokens, temperature, top_p) — ensure model & tokenizer are configured.

Frontend (Student Assistant Interface)
- From `frontend/`:
  npm i
  npm run dev
- The frontend components referenced include CVScore.tsx (file-input for CV PDF upload) and a CareerTodoList component (career planning UI). The app root is wired through `src/main.tsx` (index.html loads /src/main.tsx).

Running the API / Chat
- The backend contains FastAPI-related imports (fastapi, uvicorn) in several files:
  To run any FastAPI app present in the backend (if there is a server entry):
  uvicorn backend.server:app --host 0.0.0.0 --port 8000
  (Replace backend.server:app with the actual module path exposing the `app` instance.)

Examples and quick commands
- Analyze a GitHub user:
  export GITHUB_TOKEN="your_token_here"
  python backend/ollamachat2.py
- Run the GitHub repo test harness:
  python backend/githubreal.py
- Generate a CV report:
  python -c "from backend.cv_mechanism.converter import full_stream; full_stream('/path/to/cv.pdf')"
- Start frontend dev server:
  cd frontend && npm run dev

---

## Technologies used

- Python 3.8+
- PyTorch / Transformers (tokenizer + model.generate usage)
- LangChain / LangChain community integrations (llms, embeddings, vectorstores)
- Ollama / Ollama LLM integration (langchain_ollama, OllamaLLM)
- Chroma / ChromaDB for vector store
- FastAPI + Uvicorn for HTTP API
- React + TypeScript for frontend (Vite or similar bundler)
- Streamlit / Gradio (mentioned in earlier README templates as possible demo UIs)
- Additional libs: pandas, PyPDF2, dotenv, pydantic

---

## Security & configuration notes (important)

- Remove any hard-coded secrets from the repository. The code contains places where a GitHub token variable was present inside files. Do NOT keep secrets in source files; use environment variables:
  export GITHUB_TOKEN="ghp_..."  # set locally or in CI secrets

- If you find hard-coded tokens in files (search for `GITHUB_TOKEN` in backend/), replace them and rotate any leaked tokens immediately.

- When running LLM models, ensure you comply with the model's licensing and distribution terms. Model checkpoints are NOT included in this repo.

- For deployment, ensure API endpoints are authenticated and rate-limited to avoid exposing heavy compute backends.

---

## Team members

- Altan Reisoglu — Backend, RAG, Frontend implementation
- Taha Emre Pamukçu — API connections, Tool programming
- Ardıl Deniz Sustam — Frontend, Data collection
- Furkan Ahi — Tool programming, Agent deployment, Frontend

---


## Troubleshooting

- Rate limit errors when calling GitHub APIs: set GITHUB_TOKEN env var and ensure it has the correct scopes.
- Model load errors: check MODEL_PATH, tokenizer compatibility, and GPU/CUDA versions.
- Out of memory: use smaller models, enable 8-bit quantization libraries, or run on CPU with smaller batch sizes.
- Frontend build errors: ensure Node and npm versions match expectations (check package.json).



