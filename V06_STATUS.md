Mouse Virtual v0.6 - Estado de implementación (29-10-2026)

AUDITORÍA
- Secuencia encontrada: Secuencia 1, 36 pasos, JSON persistente.
- Log reciente: 36 INPUT_RECORDED, 1 SEQUENCE_SAVED, 108 STEP_DISPATCHED, reproducción cancelada.
- Hubo dos grabaciones con 0 eventos en otra sesión; no se debe atribuir causalidad sin examinar el foco y el proceso.
- No se eliminó la secuencia existente.

CAMBIOS
- Reescritura completa del stylesheet QSS, que anteriormente tenía texto inválido entre reglas.
- Tarjetas, botón primario azul, detención rosada, panel oscuro y campos uniformes; áreas con scroll en pantallas pequeñas.
- Motor de reproducción produce metadatos para el cursor por acción; la interfaz actualiza la posición en su propio hilo.
- Logs estructurados: TARGET_CHECK, STEP_DISPATCHED con foco, posición, estado de minimización y POSTED_UNCONFIRMED.
- El contador de progreso infinito muestra ∞, en lugar de None.
- Grabador: diagnósticos de eventos observados, capturados, descartados por foco, inyectados, pausa y desbordamiento.
- La grabación vacía advierte que no detectó clics del destino; la grabación no vacía se guarda.

PRUEBAS
- 11 tests automatizados aprobados, incluidos eventos de reproducción, detención infinita y contadores de grabación.
- Layout smoke: 5 pestañas, selector y tabla correctamente inicializados.
- No se han ejecutado clics reales contra Roblox durante el proceso remoto.
- El envío por PostMessageW significa mensaje enviado a Windows; NO garantiza que el juego lo haya procesado.
- Un cursor renderizado es visual y no constituye un dispositivo físico independiente de entrada.

PENDIENTES
- Validación visual manual comparando captura real con la maqueta.
- Diagnóstico en Roblox con foco y sin foco; solo una prueba real puede comprobar la recepción.
- Vista previa capturada del juego en tiempo real, si el sistema lo permite.
