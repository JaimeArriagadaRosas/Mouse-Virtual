# Diagnóstico de recepción de entrada — 30 octubre 2026

## Prueba aislada
`input_receiver_lab.py` crea una ventana Win32 oculta y usa el motor real `post_click`, sin mover el puntero físico.
Resultado: 18/18 mensajes recibidos; 3 pares abajo/arriba para cada botón izquierdo/derecho/central; coordenadas 45,55 correctas. Mouse físico sin cambios. No se interactuó con Roblox.
Comando: `.venv\Scripts\python.exe input_receiver_lab.py`

## Roblox: evidencia de la sesión real
- Secuencia 4: 41 pasos de clic registrados.
- PLAYBACK_START: 2026-10-30 09:30:59, ventana clase WINDOWSCLIENT, área cliente 1920x991.
- 83 STEP_DISPATCHED, todos POSTED_UNCONFIRMED; ninguna confirmación de consumo o acciones dentro del juego.
- Foreground distinto del proceso de Roblox durante reproducción. Geometría comparada: same.
- PLAYBACK_END: cancelled.
- No asumir recepción; no asumir que el motor está averiado únicamente por este caso.

## Diagnóstico
PostMessageW solo informa que el mensaje se agregó a la cola correspondiente. Es distinto de una entrada física/Raw Input. Algunos motores de juego no procesan esos mensajes en la forma esperada.
La prueba aislada confirma que el mecanismo funciona con un receptor Win32 preparado para ello; la compatibilidad de Roblox desenfocado sigue sin demostrarse.

## Próximas validaciones controladas
1. Comparar una ventana Win32 de prueba con ventana de juego y registrar diferencias de entrada.
2. Visualizar salida de simulación independiente en la interfaz sin overlays globales.
3. Nunca lanzar pruebas con compras reales ni entradas globales sin intervención del usuario.
