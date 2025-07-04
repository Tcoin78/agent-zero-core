from langchain.tools import Tool
from .code_execution_tool import execute_command

def run_shell_tool(command: str) -> str:
    try:
        result = execute_command("localhost", command)
        output = result["stdout"]
        if result["stderr"]:
            output += f"\n[stderr]: {result['stderr']}"
        return output.strip()
    except Exception as e:
        return f"[💥 Exception] {str(e)}"

tools = [
    Tool(
        name="code_execution_tool",
        func=run_shell_tool,
        description="Ejecuta comandos locales como ls, df -h, etc."
    ),
]
