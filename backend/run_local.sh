#!/usr/bin/env bash
set -e

echo "[ainoa] creating venv .venv if not exists"
python3 -m venv .venv || true

echo "[ainoa] activating venv"
source .venv/bin/activate

echo "[ainoa] installing requirements"
pip install --upgrade pip
pip install -r requirements.txt

echo "[ainoa] starting backend at http://localhost:8000 ..."
uvicorn main:app --reload
