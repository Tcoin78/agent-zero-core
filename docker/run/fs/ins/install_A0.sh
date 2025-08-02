#!/usr/bin/env bash
set -euo pipefail

BRANCH=${1:-main}
REPO_DIR="/git/agent-zero"
GIT_REPO="https://github.com/Tcoin78/agent-zero-core.git"

echo "🔧 Cloning agent-zero ➜ branch ${BRANCH}"
rm -rf "${REPO_DIR}"
git clone --branch "${BRANCH}" "${GIT_REPO}" "${REPO_DIR}"

echo "🐍 (Re)creating venv by nuking old and making fresh"
rm -rf /opt/venv
python3 -m venv /opt/venv
source /opt/venv/bin/activate

VENV_PYTHON="/opt/venv/bin/python"
VENV_PIP="/opt/venv/bin/pip"

echo "📦 Forcing fresh pip/setuptools/wheel install"
$VENV_PIP install --upgrade --force-reinstall pip setuptools wheel

echo "📥 Installing requirements"
$VENV_PIP install --no-cache-dir -r "${REPO_DIR}/requirements.txt"

echo "▶️ Running Playwright installer (stub)"
bash /ins/install_playwright.sh "${BRANCH}"

echo "⚙️ Preloading models"
$VENV_PYTHON "${REPO_DIR}/preload.py" --dockerized=true

echo "✅ install_A0.sh completed successfully!"
