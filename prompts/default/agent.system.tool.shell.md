<!--
  FICHERO: agent.system.tool.shell.md
  DESCRIPCIÓN: Proporciona acceso directo al shell del host sin sandbox.
  IMPACTO: Habilita ejecución de comandos con privilegios, usado por Agent Zero.
-->

### TOOL_SHELL

**Descripción breve:**  
Ejecuta comandos de shell en el host (no aislado). Soporta operaciones con privilegios mediante `sudo -n`.

**Guía de uso interno:**  
1. Recibe un string con el comando completo.  
2. Valor de retorno: salida estándar + código de retorno.  
3. Si la orden falla (código ≠ 0) debe devolverse la salida de error.  
4. No se permiten prompts interactivos; use banderas `-n` o equivalentes.

**Seguridad:**  
* Solo accesible para roles de confianza (main-agent, ops-agent).  
* Registra cada invocación en `logs/tool_shell.log`.  

**Ejemplo (no se ejecuta automático):**  
`du -sh /opt; sudo -n systemctl restart postgresql`
