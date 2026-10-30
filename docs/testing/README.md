# Estrategia de pruebas

La división por tipo de prueba ocurre **fuera del paquete de aplicación**. Todo el código distribuible está en `src/mouse_virtual`, mientras que los test y scripts no se empaquetan en el ejecutable.

| Ubicación | Qué se prueba | Ejemplos |
|---|---|---|
| `tests/unit/` | Reglas puras, validación, transformaciones y límites de arquitectura | `Plan.validate`, geometría, imports |
| `tests/integration/` | Colaboración entre módulos y recursos Windows controlados | Persistencia de JSON, ciclo de grabación, receptor Win32 aislado |
| `tests/gui/` | Estados y contratos de interfaz Qt | Contadores, cierre, progreso, señales y controles |
| `tests/labs/` | Experimentos reproducibles que quizá aún no sean pruebas de regresión | Hipótesis de coordenadas, hipótesis de recepción |
| `scripts/` | Ejecutables de laboratorio, smoke y diagnóstico, invocados manualmente o por tests | `input_receiver_lab.py`, `gui_e2e_isolated.py` |

## Reglas

1. Los tests no deben interactuar con una partida real de Roblox ni con compras. El receptor Win32 es de laboratorio.
2. Las pruebas unitarias no requieren Qt ni el sistema operativo Windows, salvo que el comportamiento específico lo demande.
3. Los tests de integración Windows solo deben tocar ventanas creadas por el propio test.
4. Los tests GUI que lo permitan usan `QT_QPA_PLATFORM=offscreen`. El test que necesita un HWND de Windows debe ejecutarse **sin** esa variable.
5. Los fixtures y datasets pequeños que ayuden a reproducir resultados pueden ir en `tests/fixtures/`. Los datos de usuario, binarios de terceros y secretos no se versionan.
6. Toda nueva funcionalidad debería aportar tests y, si corresponde, ajustar documentación y ejemplos.

## Ejecutar

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests
.\.venv\Scripts\python.exe scripts/ui_smoke.py

$env:QT_QPA_PLATFORM = 'offscreen'
.\.venv\Scripts\python.exe scripts/gui_e2e_isolated.py
Remove-Item Env:QT_QPA_PLATFORM
```

La batería de regresión actual cuenta con 24 pruebas automatizadas. Si se agregan tests de Windows que requieren una ventana real, es importante no forzar `offscreen` globalmente para toda la ejecución.
