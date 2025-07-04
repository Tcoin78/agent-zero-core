import subprocess
import os

def is_localhost(host):
    return host in ("localhost", "127.0.0.1", "::1") or host == os.uname()[1]

def execute_command(host, command, user=None):
    """
    Ejecuta un comando en la máquina local o remota según el host.
    """
    if is_localhost(host):
        print(f"🔧 Ejecutando localmente: {command}")
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "exit_code": result.returncode,
        }
    else:
        # Requiere que SSH esté configurado si es remoto
        ssh_target = f"{user}@{host}" if user else host
        print(f"🔐 Ejecutando vía SSH en {ssh_target}: {command}")
        ssh_command = f"ssh {ssh_target} '{command}'"
        result = subprocess.run(ssh_command, shell=True, capture_output=True, text=True)
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "exit_code": result.returncode,
        }
