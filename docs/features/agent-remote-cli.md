# CLI remoto del agente (sin GUI)

El punto de entrada `python -m mouse_virtual.modules.agent_control.remote_cli` permite que una herramienta remota ejecute operaciones locales sin abrir la GUI de Mouse Virtual.

## Descubrimiento y alcance

```powershell
.\.venv\Scripts\python.exe -m mouse_virtual.modules.agent_control.remote_cli windows
.\.venv\Scripts\python.exe -m mouse_virtual.modules.agent_control.remote_cli inspect --hwnd 123456 --authorize-hwnd 123456
```

El HWND es ilustrativo: obtener uno existente mediante `windows`. El indicador `--authorize-hwnd` debe coincidir con el objetivo que el usuario autorizó para esa ejecución. Es una declaración explícita de alcance, **no una autenticación independiente**: la herramienta remota también debe actuar bajo permisos legítimos.

## Plan de varias acciones

Guardar como archivo JSON (sin credenciales):

```json
{
  "steps": [
    {"action":"desktop.fill","auto_id":"QApplication.QWidget.search_input","text":"perritos"},
    {"action":"desktop.invoke","auto_id":"QApplication.QWidget.search_button","control_type":"Button"},
    {"action":"desktop.wait_text","auto_id":"QApplication.QWidget.search_result","control_type":"Text","text":"Resultados de perritos"}
  ]
}
```

Ejecutar:

```powershell
.\.venv\Scripts\python.exe -m mouse_virtual.modules.agent_control.remote_cli run --hwnd 123456 --authorize-hwnd 123456 --plan ".\plan.json"
```

## Medidas y límites

- Máximo 20 pasos y archivo de plan menor de 20 KB; se rechazan acciones ajenas al contrato y campos adicionales.
- Antes de cada paso se comprueba identidad HWND/PID/clase, validez y estado no minimizado mediante DesktopScope.
- El resultado de `desktop.fill` comunica verificación y longitud, no el texto escrito. Las lecturas explícitas `desktop.read_control` pueden devolver datos del control; no emplearlas sobre información sensible.
- `desktop.wait_text` verifica una cadena esperada durante hasta 3 segundos sin introducir teclado ni mouse global.
- Se ejecuta desde un proceso CLI distinto, que una conexión remota puede terminar si excede su tiempo límite; el CLI no arranca servidor de red.
- La interfaz gráfica mantiene sus funciones independientes. No se resolvió aquí su bloqueo síncrono en UIA.
- Se probó un plan real sobre la ventana de laboratorio Qt. Las operaciones sobre otros programas dependen de su compatibilidad UIA y de la autorización correspondiente.
