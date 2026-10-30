# Windows UI Automation (primera versión)

Adaptador opcional en `infrastructure/windows/accessibility.py`, construido con pywinauto/COM UI Automation.

- Conexión estricta por identificador HWND de una ventana válida y no minimizada.
- Localización de controles por AutomationId o nombre accesible y tipo Edit.
- Rechaza coincidencias ausentes o ambiguas; no selecciona controles arbitrarios.
- Escritura por UI Automation ValuePattern SetValue y lectura de confirmación, **sin SendInput ni teclado global**.
- Algunos controles no implementan ValuePattern y deben devolver error; no se fuerza una escritura global como alternativa.
- No ejecuta operaciones sobre aplicaciones externas de forma automática, ni es una API remota.
- La integración con AgentExecutor/CLI y un ensayo con ventana UIA real siguen pendientes; pruebas actuales emplean dobles controlados.

Dependencia opcional: `pip install -e ".[desktop]"`.
