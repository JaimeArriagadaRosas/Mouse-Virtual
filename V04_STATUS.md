# Mouse Virtual v0.4 - Secuencias persistentes

## Implementado
- Archivo individual JSON por secuencia: %LOCALAPPDATA%\\MouseVirtual\\sequences.
- Fin de grabación F9 guarda automáticamente una nueva secuencia con nombre Secuencia N.
- Secuencia seleccionable en Automatización y Secuencias, se puede renombrar, duplicar, eliminar y guardar los cambios de la tabla.
- Repetir indefinidamente por defecto (repeat=0 interno) o número definido por el usuario.
- Reproductor acepta repeat=0 hasta que se pulse Detener (F7 o control de emergencia).
- Automatización usa la secuencia seleccionada, no la última memoria de la grabadora.
- Se incrementó tamaño inicial de ventana a 1180x760, se redujo texto redundante y se agruparon botones de actualización.
- Copias de seguridad pre-v0.4 en backups.

## Criterios y limitaciones
- Se verificó la persistencia mediante pruebas de ciclo completo de almacén y 8 tests pytest aprobados.
- La inicialización de la GUI se validó sin pantalla.
- La grabación real en Roblox y la recepción de eventos por Roblox siguen pendientes.
- La secuencia de clics actualmente NO captura movimiento/drag ni teclado.
- Los eventos de reproducción Win32 son emitidos, no necesariamente recibidos.
- Evitar usar compras con dinero real o Robux durante pruebas.
- Para reconocer una grabación nueva hay que finalizarla con F9 y revisar el selector.
