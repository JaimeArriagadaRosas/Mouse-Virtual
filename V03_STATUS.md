# Mouse Virtual v0.3 — observabilidad y control
Fecha: 2026-10-29

## Implementado
- F9 inicia grabación de mouse de la aplicación seleccionada y oculta la interfaz.
- F9 durante grabación detiene, restaura la interfaz y transfiere eventos al editor de secuencias.
- F10 pausa/reanuda la captura; el grabador evita acumular pausas en el intervalo posterior.
- Reproductor de secuencias en hilo separado del bucle de interfaz; se puede cancelar durante la espera.
- Logs JSONL por sesión en %LOCALAPPDATA%\\MouseVirtual\\logs.
- Bandeja de Windows con acciones Mostrar, Detener reproducción, Detener grabación y Salir.
- Reloj de ejecución congelado al detenerse.
- Copias del codigo previo en backups.

## Diagnostico
Se registran RECORD_START / RECORD_END / INPUT_RECORDED / RECORD_PAUSE_TOGGLE, GUI_START, PLAYBACK_START, STEP_DISPATCHED, PLAYBACK_END, STOP_REQUESTED, APP_EXIT. La información puede identificar que comandos se enviaron y su temporización, NO confirmar recepción por juegos.

## Limitaciones
- El grabador v0.3 registra clics y tiempos: no hay captura de arrastre completo ni teclado global.
- F9/F10 se detectan por consulta del estado de Windows (no RegisterHotKey); deben validarse con Roblox real.
- Reproducción de secuencias usa mensajes Win32, que Roblox puede ignorar; no hay garantía de ejecución con juego desenfocado o minimizado.
- No hay video en directo de la ventana del juego. La bandeja y el contador muestran observabilidad operativa.
- Si F9 no es detectable mientras Roblox tiene foco, analizar registro de teclas o un método alternativo permitido.
- Evitar secuencias de compras con dinero/Robux durante diagnóstico.

## Validado
- 6 pruebas automatizadas previas aprobadas.
- Ventana PySide6 arranca con cinco pestañas.
- Reproductor cancela un paso con espera de 2 segundos, sin esperar que finalice la espera.
- Reproductor completa 5 clics dirigidos sobre una ventana de prueba y registra sus pasos.
- No se ha efectuado prueba física de recepción del juego Roblox.
