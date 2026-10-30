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
