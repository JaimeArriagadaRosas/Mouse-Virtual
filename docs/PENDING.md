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
