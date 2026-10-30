# Actualización del grabador (29-10-2026)

## Flujo de prueba
1. Abrir Roblox o una aplicación de prueba.
2. En la pestaña Automatización: **Actualizar ventanas** y elegir la ventana o usar **Seleccionar ventana activa**. Confirmar que PID, clase y tamaño sean correctos.
3. Pulsar **Grabar F9**. Se inicia un hook de mouse del sistema.
4. Cambiar a la aplicación seleccionada y realizar clics manuales. Solo se graban pulsaciones de botón hechas con el proceso de destino en primer plano (por PID); se ignoran eventos inyectados.
5. Pulsar **F9** para detener. **F10** pausa/reanuda el almacenamiento.
6. Transferir a **Secuencias** y guardar el JSON.
7. Para reproducir, escoger modo Win32, seleccionar ventana destino y activar desde Secuencias con F6.

## Advertencias
- Esta versión registra clics izquierdo/derecho/central y pausas entre ellos; no graba teclas, scroll ni trayectorias del cursor en la tabla, aunque el hook identifica wheel para expansión posterior.
- Las teclas F9/F10 se detectan por lectura periódica de estado del teclado; pueden no funcionar cuando un juego captura completamente la entrada o si hay diferencias de integridad.
- La grabación usa coordenadas cliente de la ventana que tenga foco. Si Roblox expone ventana padre sin area cliente, la reproducción podría ser incompatible.
- Win32 PostMessage no es equivalente a entrada Raw Input. La recepción en Roblox no está confirmada; no hacer secuencias con compras de valor real durante pruebas.
- Nunca se capturan teclas de texto ni contraseñas. Los datos de clic se mantienen en RAM hasta guardar manualmente el JSON. El hook no bloquea el mouse físico.
- El contador muestra mensajes emitidos, no clics recibidos.
- Se mantiene Ctrl+Shift+F12 para detener reproducción y el botón Detener para las tareas; detén la grabación con F9.

## Pruebas
- pytest: 6 pruebas, incluyendo ciclo inicio/parada del hook.
- Smoke GUI: arranque de las cinco pestañas.
- Prueba real con Roblox en segundo plano: pendiente, no afirmar compatibilidad.
