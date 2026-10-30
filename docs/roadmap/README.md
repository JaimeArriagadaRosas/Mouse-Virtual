# Pendientes de desarrollo

## Compatibilidad de Roblox en segundo plano (investigación pausada)

**No resuelto:** el reproductor publica mensajes Win32, pero no se ha demostrado recepción de clics por Roblox cuando está desenfocado. El contador muestra acciones enviadas, no clics ejecutados.

Se verificó con una ventana Win32 aislada que el adaptador entrega 18 de 18 mensajes sin mover el mouse físico. El análisis estático local mediante REA 6.8.0 sobre una copia de Roblox examinó importaciones, exportaciones y configuraciones de carga, pero no permitió identificar el método de entrada real. No se incluyen archivos de Roblox ni de REA en este repositorio.

**Pendiente:** estudiar compatibilidad de mecanismos de entrada sin modificar ni eludir protecciones del juego, y documentar una verificación observable de recepción.

## Otros pendientes

- Mejorar la recalibración de coordenadas cuando cambian monitor, DPI o tamaño de ventana.
- Unificar rutas de ejecución antiguas y verificar la vista previa integrada en todos los modos.
- Completar pruebas de botón central, controles de grabación y cierre seguro.
- Ampliar pruebas de interfaz en Windows y revisar empaquetado PyInstaller.

## Ampliación P0-P5 (2026-10-30)

- **Hecho:** botón central en planes JSON, cursor SVG negro, benchmark de 100/1000/10000 acciones simuladas, temporizador Qt medido, CLI de navegador local, pruebas de búsqueda con Chromium real y lista blanca de hosts.
- **Completado en segunda etapa:** las secuencias grabadas y editadas comparten ahora `_begin_sequence`, con validación uniforme de modo, destino y geometría. Dos pruebas GUI de regresión cubren ejecución y destino ausente.
- **Pendiente:** consolidación del clicker repetitivo, temporizador y mixins, temporización del motor de reproducción bajo carga, interfaz GUI de agentes, UI Automation para escribir en otras aplicaciones Windows, protocolo MCP, pruebas de DPI y Roblox.
- **Limitación:** el módulo de agentes ejecuta su CLI desde el código fuente; la aplicación gráfica no lo integra todavía.

Detalles en [alcance de ejecución](EXECUTION_20261030.md) y [rendimiento](../testing/performance.md).

- **Nuevo diagnóstico aprobado:** 1000 clics dirigidos a receptor Win32 (2000 mensajes de botón), más 18 eventos de control; cursor físico sin cambios. No refleja CPS real.

## Clicker: ejecución controlada (segunda etapa, continuación)

- **Implementado:** ClickBudget y ScheduleMetrics en modules/clicker/scheduler.py; límite de acciones exacto, sin sobrepasar cantidades impares con clic doble, Qt PreciseTimer, métricas de desviación registradas como CLICKER_SCHEDULE y modo de simulación sin Win32.
- **Validación:** 40 pruebas pytest, smoke de cinco vistas y prueba GUI E2E.
- **Pendiente:** sacar el temporizador de ejecución del hilo de interfaz si las mediciones bajo carga lo justifican; medir frecuencia y recepción en el motor efectivo, así como CPU, memoria, cancelación y cambio de ventanas.
- **No se cambió** el mínimo de 50 ms. El rendimiento real de la aplicación destino no está demostrado.

## Hilo independiente de clicker — desarrollo experimental

- Nuevo módulo `src/mouse_virtual/modules/clicker/worker.py`: `ClickWorker` ejecuta el reloj monotónico en hilo propio, permite límite finito o ilimitado, grupo simple/doble, interrupción durante espera y errores de adaptador.
- La función de envío se inyecta (no incluye acoplamiento con Qt ni llamadas globales). Las pruebas usan exclusivamente callbacks simulados.
- **Todavía no está conectado al botón Iniciar de la GUI.** El clicker de escritorio conserva Qt PreciseTimer hasta que exista una cola de eventos segura entre hilos, se congele el destino al comenzar y se prueben controles, cancelación, métricas y no interferencia.
- Validación: 43 pruebas pytest aprobadas (3 pruebas nuevas del worker); GUI E2E aprobada. No se cambió mínimo de 50 ms.

## Integración gráfica del ClickWorker

- **Implementado:** el clicker de la GUI usa ClickWorker en hilo independiente y cola de eventos SimpleQueue. Solo el hilo de Qt actualiza widgets y registra eventos visuales.
- **Seguridad:** configuración de destino/botón/coordenadas capturada al inicio, cancelación del worker en Detener y cierre, descarte de eventos de ejecuciones anteriores.
- **Validación:** 45 pruebas pytest, incluida cancelación antes del primer clic y eventos atrasados. Smoke de 5 pestañas y GUI E2E aprobados.
- **Pendiente:** perfiles prolongados bajo carga real, interferencia con aplicaciones externas, control de cambios de foco en modo global, y mejorar la separación de mixins. El intervalo mínimo sigue siendo 50 ms.

## Seguridad del modo global y diagnóstico real de scheduling

- Se comprueba el PID de la ventana que recibe el foco antes del inicio del clicker global y antes de cada envío; si cambia, se aborta sin enviar nuevos clics. Las pruebas de transición de foco sustituyen las API de entrada con dobles y no mueven el puntero físico. La validación por PID no sustituye una política estricta por HWND, pendiente.
- Se añadió `scripts/benchmark_click_worker.py`, que mide el hilo ejecutor sin entrada real. Resultado reproducible y límites en `docs/testing/performance.md`.
- 47 pruebas automatizadas aprobadas. Pendientes: seguridad de foco HWND estricto, ensayos de carga prolongada, escenarios de monitor, integración UI Automation y desacoplamiento de mixins.

## Protección HWND exacta y pruebas de geometría

- Implementado `infrastructure/windows/focus_guard.py`: comprobación de ventana foreground exacta, PID, validez y estado minimizado antes de cada grupo de entrada global. La comprobación por PID únicamente era insuficiente para procesos con varias ventanas.
- 5 tests de guardia, 2 tests de carga/cancelación y geometría; **54 tests aprobados** en total.
- Carga: se verificó la cancelación antes de emitir entradas sobre un presupuesto de 10.000 clics. **No** equivale a ejecutar 10.000 clics reales ni prueba estabilidad prolongada.
- Geometría: límites de transformación de 1920x1080 a 1280x720 y detección de dimensiones inválidas.
- Pendientes: DPI real y múltiples monitores físicos, carreras de foco durante `SendInput`, más ensayos prolongados y el adaptador UI Automation.
