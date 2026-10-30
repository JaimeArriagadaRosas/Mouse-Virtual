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
- **Pendiente:** consolidación de rutas del clicker y mixins, temporización del motor de reproducción bajo carga, interfaz GUI de agentes, UI Automation para escribir en otras aplicaciones Windows, protocolo MCP, pruebas de DPI y Roblox.
- **Limitación:** el módulo de agentes ejecuta su CLI desde el código fuente; la aplicación gráfica no lo integra todavía.

Detalles en [alcance de ejecución](EXECUTION_20261030.md) y [rendimiento](../testing/performance.md).

- **Nuevo diagnóstico aprobado:** 1000 clics dirigidos a receptor Win32 (2000 mensajes de botón), más 18 eventos de control; cursor físico sin cambios. No refleja CPS real.
