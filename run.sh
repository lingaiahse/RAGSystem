#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"

usage() {
  cat <<EOF
Usage: run.sh <command> [args]

Commands:
  help              Show this help
  docker-up         Build and run services with docker-compose
  docker-down       Stop and remove docker-compose services
  setup             Create .env files from examples if missing
  backend-dev       Prepare venv, install deps and run backend (uvicorn)
  frontend-dev      Install node deps and run Next.js dev server
  ingest <pdf> <source> <department> <location> <role_level>
                    Ingest a PDF into the in-memory vector store (for quick testing)

Examples:
  ./run.sh docker-up
  ./run.sh backend-dev
  ./run.sh ingest ./policies/holiday.pdf "Holiday Policy" HR US L2
EOF
}

cmd=${1:-help}

case "$cmd" in
  help)
    usage
    ;;

  docker-up)
    echo "Building and starting docker-compose services..."
    docker-compose up --build
    ;;

  docker-down)
    echo "Stopping docker-compose services..."
    docker-compose down --volumes
    ;;

  setup)
    echo "Creating .env files from examples if they don't exist..."
    if [ -f "$BACKEND_DIR/.env" ]; then
      echo "Backend .env already exists"
    else
      cp "$BACKEND_DIR/.env.example" "$BACKEND_DIR/.env" && echo "Created backend/.env"
    fi
    if [ -f "$FRONTEND_DIR/.env" ]; then
      echo "Frontend .env already exists"
    else
      cp "$FRONTEND_DIR/.env.example" "$FRONTEND_DIR/.env" && echo "Created frontend/.env"
    fi
    ;;

  backend-dev)
    echo "Starting backend in dev mode..."
    pushd "$BACKEND_DIR" >/dev/null
    python -m venv .venv || true
    # shellcheck disable=SC1091
    source .venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    popd >/dev/null
    ;;

  frontend-dev)
    echo "Starting frontend in dev mode..."
    pushd "$FRONTEND_DIR" >/dev/null
    if ! command -v npm >/dev/null 2>&1; then
      echo "npm not found. Please install Node.js/npm to run the frontend."
      exit 2
    fi
    npm install
    npm run dev
    popd >/dev/null
    ;;

  ingest)
    if [ $# -lt 6 ]; then
      echo "ingest requires 5 args: <pdf> <source> <department> <location> <role_level>"
      exit 2
    fi
    pdf_path=$2
    source_name=$3
    department=$4
    location=$5
    role_level=$6
    if [ ! -f "$pdf_path" ]; then
      echo "PDF not found: $pdf_path"
      exit 3
    fi
    echo "Ingesting $pdf_path (source=$source_name, department=$department, location=$location, role_level=$role_level)"
    pushd "$BACKEND_DIR" >/dev/null
    # Use python -c to call the ingest function
    python - <<PY
import sys
from app.ingest import ingest_pdf
res = ingest_pdf(r"$pdf_path", r"$source_name", r"$department", r"$location", r"$role_level")
print('Ingest result:', res)
PY
    popd >/dev/null
    ;;

  *)
    echo "Unknown command: $cmd"
    usage
    exit 1
    ;;
esac
