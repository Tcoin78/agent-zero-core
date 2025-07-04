#!/usr/bin/env python3
import sys
import yaml
from pathlib import Path

from agents.agent_decider import AgentDecider
from agents.agent_executor import AgentExecutor

def load_mission_config(mission_id: str) -> dict:
    prompt_path = Path.home() / f"agent-zero-missions/{mission_id}/{mission_id}.prompt.yaml"
    if not prompt_path.exists():
        print(f"❌ No se encontró el archivo de misión: {prompt_path}")
        sys.exit(1)

    with open(prompt_path, "r") as f:
        config = yaml.safe_load(f)

    print(f"🧠 Misión cargada: {mission_id}")
    return config

def main():
    mission_id = "ETH-REC-1798534"
    config = load_mission_config(mission_id)

    # 1. Decisión
    decider = AgentDecider(number=mission_id, config=config)
    decider_output = decider.run(config)

    # 2. Ejecución
    executor = AgentExecutor(number=mission_id, config=config)
    result = executor.run(decider_output)

    # 3. Mostrar salida
    print("✅ Resultado de la ejecución:")
    print(result["stdout"])
    if result["stderr"]:
        print("⚠️ Error:", result["stderr"])

if __name__ == "__main__":
    main()
