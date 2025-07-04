#!/bin/bash

# 🚀 Script de arranque Agent Zero
set -e

# Cargar variables de entorno
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
else
    echo "❌ Archivo .env no encontrado"
    exit 1
fi

# Activar entorno virtual
source .venv/bin/activate

# Lanzar RFC listener en segundo plano
echo "🧠 Iniciando job_loop (RFC listener)..."
nohup python agent_zero/loop/job_loop.py --port $RFC_PORT > logs/job_loop.log 2>&1 &

# Lanzar misión
MISSION_ID="ETH-REC-1798534"
echo "🎯 Iniciando misión $MISSION_ID..."
python run_ui.py --mission $MISSION_ID --headless --log-level info
