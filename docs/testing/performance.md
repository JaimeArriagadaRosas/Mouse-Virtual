# Diagnósticos de rendimiento — 2026-10-30

## Naturaleza de las pruebas

No se enviaron clics a otras aplicaciones durante estos benchmarks.

**Benchmark de operaciones en memoria:** scripts/benchmark_clicker.py. 100, 1.000 y 10.000 pasos validados y contabilizados, sin temporizador ni API Windows. Evalúa carga de modelo, no CPS efectivos.

**Benchmark de temporizador Qt:** scripts/benchmark_qt_timer.py. PreciseTimer y 100 eventos de QCoreApplication por intervalo, sin emisión de entrada. Es una muestra aislada del temporizador, no una garantía de precisión ni una medición de rendimiento del motor global.

| Solicitado | Media observada | P95 observado | Máximo observado |
|---|---|---|---|
| 1 ms | 1,1337 ms | 1,5019 ms | 12,045 ms |
| 5 ms | 4,9952 ms | 5,5547 ms | 5,6222 ms |
| 10 ms | 10,0085 ms | 10,5482 ms | 10,770 ms |
| 50 ms | 50,0861 ms | 62,2695 ms | 63,6048 ms |

## Decisión

Mantener por ahora el intervalo mínimo de 50 ms en la interfaz. Antes de permitir 1, 5 o 10 ms hay que medir el **reproductor real**, la recepción por ventana de laboratorio, deriva bajo carga de UI, cancelación y consumo CPU. La copia del AutoClicker de referencia contiene campos de milisegundos pero no demuestra su límite mínimo real.

## Pruebas futuras

- 1.000 mensajes en receptor Win32 controlado, cuantificando ACK y duplicaciones.
- 1.000 operaciones bajo distintos intervalos reales, perfiles de CPU y memoria.
- Duración prolongada, cierre, pérdida de foco y cambio de tamaño.
- Nunca usar Roblox como banco de carga.

## Receptor Win32: 1.000 clics confirmados

Se agregó la prueba repetible scripts/input_receiver_lab.py --stress-clicks 1000. Se recibieron 2018 mensajes en total: 18 controles iniciales más 2000 transiciones del botón izquierdo (1000 down/up), todos en las coordenadas (45,55). No se llama al API global de movimiento de cursor en esta modalidad; el valor observado del puntero puede cambiar por uso simultáneo del usuario. Esta medición **no** certifica una tasa por segundo ni compatibilidad con juegos o aplicaciones externas.

## Presupuesto de clics y estabilidad de ejecución

- Se agregó `ClickBudget` independiente de Qt; limita la cantidad emitida incluso en clic doble y cuenta exclusivamente acciones que pasaron por el adaptador.
- El programador usa actualmente `QTimer.PreciseTimer`; `ScheduleMetrics` mide la diferencia entre el instante observado y el tiempo ideal según el intervalo. La cola de eventos de Qt, la carga del sistema y los adaptadores afectan la precisión real.
- `CLICKER_STEP` y `CLICKER_SCHEDULE` se registran para diagnóstico. Ni estos registros ni el contador prueban la recepción en aplicaciones externas.
- La prueba GUI verifica modo simulado sin eventos de OS y el límite impar de 5 clics, con conteo de llamadas [2, 2, 1].
