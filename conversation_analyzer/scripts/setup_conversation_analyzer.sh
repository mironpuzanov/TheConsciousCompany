#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
VENV_DIR="${ROOT_DIR}/venv"

PYTORCH_WHEEL_INDEX="https://download.pytorch.org/whl/cpu"

echo ">> Root directory: ${ROOT_DIR}"

if [[ ! -d "${VENV_DIR}" ]]; then
  echo ">> Creating venv at ${VENV_DIR}"
  python3 -m venv "${VENV_DIR}"
fi

echo ">> Activating venv"
# shellcheck disable=SC1090
source "${VENV_DIR}/bin/activate"

echo ">> Upgrading pip"
pip install --upgrade pip

echo ">> Installing PyTorch (CPU/MPS wheel)"
pip install "torch==2.6.0" --extra-index-url "${PYTORCH_WHEEL_INDEX}"

echo ">> Installing core dependencies"
pip install \
  "transformers>=4.57" \
  accelerate \
  sentencepiece \
  datasets \
  sentence-transformers \
  spacy \
  umap-learn \
  hdbscan \
  bertopic \
  duckdb \
  fastapi \
  uvicorn \
  openai \
  rich \
  python-dotenv \
  joblib \
  redis \
  typer

echo ">> Installing optional extras (TensorFlow for TF-only checkpoints)"
pip install "tensorflow-macos==2.15.0"

echo ">> Setting default environment variables"
if ! grep -q "PYTORCH_ENABLE_MPS_FALLBACK" "${VENV_DIR}/bin/activate"; then
  cat <<'EOF' >> "${VENV_DIR}/bin/activate"
export PYTORCH_ENABLE_MPS_FALLBACK=1
EOF
fi

echo ""
echo "Setup complete. Next steps:"
echo "1. cp conversation_analyzer/env.example .env && fill in OPENAI_API_KEY / HF_TOKEN."
echo "2. source venv/bin/activate"
echo "3. python conversation_analyzer/scripts/warmup_models.py"

