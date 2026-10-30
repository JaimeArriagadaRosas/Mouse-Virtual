Mouse Virtual v0.7 — Geometría de cliente, monitores y preview

IMPLEMENTADO
- Registro de tamaño de área cliente y topología de monitores al guardar una nueva secuencia.
- Transformación normalizada (client-space) cuando cambia tamaño del destino; reubicación de ventana no cambia coordenadas relativas.
- Verificación de rango, errores explícitos ante destino inválido; log por paso del estado geométrico.
- Grabación usa coordenadas de la ventana seleccionada, no de cualquier otra ventana enfocada del mismo proceso.
- Preview de cursor integrado en la pestaña Automatización, nunca por encima de ChatGPT o el escritorio.
- Modos: Simulación (ningún clic), Win32 dirigido (emisión sin confirmación), Entrada global (mouse físico, confirmación y exigencia de foco).
- Las grabaciones antiguas sin geometría no se reescalan automáticamente porque no existe referencia fiable. Regrabar en la nueva versión es recomendable para cambios de resolución.
- Las secuencias existentes permanecen intactas.

VALIDACIÓN
- 19 pruebas pytest aprobadas, incluyendo transformación 2 pantallas -> 1, eventos fuera de rango, persistencia de geometría, modo simulación y escalado Win32.
- Prueba integral del contador por GUI aislada: 20 eventos.
- Aún no existe verificación directa de recepción por Roblox. PostMessageW aceptado NO equivale a click procesado.
- El render gráfico es representación visual y NO un dispositivo de mouse independiente.

RUTAS
- Secuencias: %LOCALAPPDATA%\MouseVirtual\sequences
- Logs: %LOCALAPPDATA%\MouseVirtual\logs
- Copia de respaldo: backups\before_v07_geometry
