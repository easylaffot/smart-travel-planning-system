# Smart Travel Planning System

A phased CrewAI project that will coordinate specialist agents to research, price, validate, revise, and present personalized travel plans.

## Current status

Phase 1: foundation and customer-request validation.

## Codespaces setup

Run all commands from the project root.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
cp .env.example .env
python -m scripts.verify_environment
python -m pytest
```

Do not commit `.env`. Put the Ollama API key only in `.env` or the deployment platform's secret manager.

## Run the Phase 1 validation demo

```bash
python -m smart_travel_planner.main
```

## Phase plan

1. Foundation and validation
2. External APIs and custom tools
3. CrewAI agents and tasks
4. Integrated workflow and budget revision
5. Professional Streamlit frontend
6. Testing, documentation, security checks, and deployment
