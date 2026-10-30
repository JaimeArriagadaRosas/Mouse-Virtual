<div align="center">

![Mouse Virtual](assets/banner.svg)

# Mouse Virtual

**GrabaciÃ³n, secuencias y automatizaciÃ³n local de mouse en Windows.**

![Windows](https://img.shields.io/badge/Windows-10%2F11-blue) ![Python](https://img.shields.io/badge/Python-3.12-3776AB) ![PySide6](https://img.shields.io/badge/GUI-PySide6-20A18C) ![Estado](https://img.shields.io/badge/Estado-Experimental-orange)

</div>

## Â¿QuÃ© es?

**Mouse Virtual** es una aplicaciÃ³n de escritorio para Windows que permite grabar clics, organizar secuencias con pausas, guardarlas localmente y reproducirlas con diferentes mecanismos de entrada. Incluye herramientas de simulaciÃ³n, vista previa del cursor, control de repeticiones y registros para diagnÃ³stico.

El cursor virtual es una **representaciÃ³n visual**: no equivale a un segundo dispositivo fÃ­sico ni garantiza compatibilidad con juegos.

## Funcionalidades

- **Clicker:** intervalo configurable, botones de mouse, clic simple/doble y nÃºmero de repeticiones.
- **Grabador:** hook de Windows que registra los clics de la ventana destino y los intervalos entre acciones.
- **Secuencias:** editor y almacenamiento de pasos en JSON, con nombres y repeticiones finitas o continuas.
- **Reproductor:** ejecuciÃ³n cancelable, contador y seguimiento de acciones.
- **Mouse virtual visual:** indicador grÃ¡fico integrado, sin superposiciÃ³n global sobre las otras ventanas.
- **Coordenadas:** posiciones relativas a la ventana cliente y metadatos de geometrÃ­a para grabaciones recientes.
- **DiagnÃ³stico:** logs JSONL y prueba de recepciÃ³n Win32 en ventana aislada.

## Arquitectura â€” Modular Single App

![Arquitectura de Mouse Virtual](assets/architecture.svg)

Una sola aplicaciÃ³n Windows, organizada en paquetes funcionales dentro de `src/mouse_virtual/`. **No es un monorepositorio**: las carpetas de pruebas, herramientas y documentaciÃ³n viven fuera del paquete distribuible.

| Carpeta | Responsabilidad |
| --- | --- |
| `src/mouse_virtual/app/` | Arranque, ventana Qt, navegaciÃ³n y composiciÃ³n |
| `src/mouse_virtual/modules/clicker/` | Clics temporizados |
| `src/mouse_virtual/modules/keyboard/` | Entrada de teclado |
| `src/mouse_virtual/modules/recording/` | GrabaciÃ³n y controles de captura |
| `src/mouse_virtual/modules/sequences/` | Modelos, persistencia y ediciÃ³n de secuencias |
| `src/mouse_virtual/modules/playback/` | ReproducciÃ³n y diagnÃ³sticos |
| `src/mouse_virtual/modules/automation/` | SelecciÃ³n de ventanas y panel de automatizaciÃ³n |
| `src/mouse_virtual/modules/virtual_cursor/` | Vista previa interna del cursor |
| `src/mouse_virtual/infrastructure/` | Adaptadores Win32, geometrÃ­a, configuraciÃ³n y logs |
| `src/mouse_virtual/resources/` | Hoja de estilos Qt |
| `tests/` | Pruebas unitarias, de integraciÃ³n y GUI |
| `scripts/`, `packaging/`, `docs/` | Laboratorio, distribuciÃ³n y documentaciÃ³n |

El archivo `main.py` de la raÃ­z es Ãºnicamente un lanzador de compatibilidad. MÃ¡s informaciÃ³n en [arquitectura y normas de dependencia](docs/architecture/README.md).

## Modos de entrada

| Modo | QuÃ© hace | Restricciones |
| --- | --- | --- |
| **SimulaciÃ³n** | Recorre pasos y posiciones sin enviar clics | No interactÃºa con aplicaciones |
| **Win32 dirigido** | EnvÃ­a mensajes de mouse a un HWND sin mover el cursor fÃ­sico | Un mensaje enviado **no implica un clic recibido** |
| **Entrada global** | Emite entrada del mouse del sistema y puede mover el cursor fÃ­sico | Puede interferir con el trabajo; requiere foco y confirmaciÃ³n |

La recepciÃ³n por la aplicaciÃ³n destino siempre debe comprobarse por separado. El contador informa sobre acciones procesadas por el reproductor, no sobre acciones reconocidas por otro programa.

## Compatibilidad

- **Windows:** arquitectura centrada en Win32, probada principalmente en Windows 11; pensada para Windows 10/11 de 64 bits.
- **Ventanas clÃ¡sicas:** mensajes Win32 aceptados por una ventana receptora de laboratorio: **18 de 18 eventos**.
- **Roblox:** **no se ha confirmado que procese clics en segundo plano**. Durante pruebas reales se emitieron mensajes sin reacciÃ³n observable.
- **Otros motores de juego y aplicaciones con entrada exclusiva:** compatibilidad no confirmada.
- **Linux/macOS:** no compatibles con el adaptador actual.

La aplicaciÃ³n no implementa tÃ©cnicas para eludir protecciones o controles de integridad de programas de terceros.

## TecnologÃ­as

Python 3.12, PySide6/Qt, ctypes, Win32 API, JSON/JSONL, pytest y PyInstaller para generar distribuciones Windows.

## InstalaciÃ³n

Se requiere Windows, Python 3.12 y PowerShell.

~~~powershell
git clone https://github.com/JaimeArriagadaRosas/Mouse-Virtual.git
cd Mouse-Virtual
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
~~~

DespuÃ©s de configurar el entorno tambiÃ©n puedes utilizar **run.bat**.

## Uso bÃ¡sico

1. Abre la pestaÃ±a **AutomatizaciÃ³n** y selecciona la ventana destino.
2. Inicia **Grabar (F9)** y realiza los clics de la secuencia en la ventana seleccionada.
3. Presiona **F9** para finalizar; F10 permite pausar o reanudar la grabaciÃ³n.
4. Guarda y selecciona tu secuencia; revisa sus pasos y coordenadas.
5. Ejecuta primero en **SimulaciÃ³n** y verifica que los pasos sean correctos.
6. Utiliza Win32 dirigido solamente con aplicaciones compatibles y comprueba la recepciÃ³n real.
7. Para detener la reproducciÃ³n utiliza el botÃ³n Detener o **F7**.

**Atajos:** F6 iniciar; F7 detener; F8 alternar reproducciÃ³n; F9 grabar/finalizar; F10 pausa de grabaciÃ³n; Ctrl+Shift+F12 parada de emergencia. Algunos dependen del foco y de las restricciones de la aplicaciÃ³n destino.

## Almacenamiento

- Secuencias: %LOCALAPPDATA%\MouseVirtual\sequences
- Logs: %LOCALAPPDATA%\MouseVirtual\logs
- ConfiguraciÃ³n: %LOCALAPPDATA%\MouseVirtual\settings.json

Los archivos locales del usuario no se incluyen en este repositorio.

## Pruebas

Las pruebas estÃ¡n separadas en `tests/unit`, `tests/integration`, `tests/gui` y `tests/labs`; consulta la [guÃ­a de pruebas](docs/testing/README.md) para decidir dÃ³nde aÃ±adir cada escenario.

~~~powershell
.\.venv\Scripts\python.exe -m pytest -q tests
.\.venv\Scripts\python.exe scripts/input_receiver_lab.py
~~~

La baterÃ­a de referencia del 30/10/2026 consta de **71 pruebas automatizadas aprobadas**. La prueba de recepciÃ³n Win32 confirmÃ³ 18/18 mensajes en una ventana aislada; esto **no valida la entrada en Roblox**.

Prueba de interfaz aislada:

~~~powershell
$env:QT_QPA_PLATFORM = 'offscreen'
.\.venv\Scripts\python.exe scripts/gui_e2e_isolated.py
Remove-Item Env:QT_QPA_PLATFORM
~~~

## CompilaciÃ³n

PyInstaller es una dependencia de compilaciÃ³n opcional:

~~~powershell
.\.venv\Scripts\python.exe -m pip install pyinstaller
.\.venv\Scripts\python.exe -m PyInstaller --noconfirm packaging/MouseVirtual.spec
~~~

Los archivos generados quedan en **dist/MouseVirtual** y se excluyen de Git. La aplicaciÃ³n requiere la carpeta completa de distribuciÃ³n y no Ãºnicamente el ejecutable.

## Control de navegador para agentes (versiÃ³n inicial)

El paquete incorpora un adaptador opcional de **Playwright/Chromium** que opera en una sesiÃ³n separada del mouse y teclado del usuario. Puede descubrir campos mediante roles y etiquetas, escribir texto, activar botones y leer el resultado. Su primer escenario de integraciÃ³n utiliza una pÃ¡gina local que busca Â«perritosÂ», sin acceso al navegador personal.

Para instalar la dependencia opcional:

~~~powershell
.\.venv\Scripts\python.exe -m pip install -e ".[browser]"
.\.venv\Scripts\python.exe -m playwright install chromium
~~~

En un sitio de laboratorio con un campo de bÃºsqueda accesible, se puede usar el CLI:

~~~powershell
.\.venv\Scripts\python.exe -m mouse_virtual.modules.agent_control.cli --url http://127.0.0.1:8000 --query perritos --allowed-host 127.0.0.1
~~~

**Importante:** la ejecuciÃ³n CLI sigue limitada a hosts permitidos; no implementa aÃºn integraciÃ³n MCP, UI Automation de escritorio ni operaciÃ³n en cualquier navegador del usuario. No se incluye el entorno Playwright/Chromium en el ejecutable principal.

Se incorporÃ³ un cursor virtual SVG negro de elaboraciÃ³n propia; este cursor sigue siendo solo una indicaciÃ³n visual. Las mediciones de temporizador estÃ¡n en [el informe de rendimiento](docs/testing/performance.md).

## Estado del desarrollo

**Experimental.** Funcionales: captura, persistencia, interfaz, simulaciÃ³n y envÃ­o de mensajes Win32. Pendientes: calibraciÃ³n en diferentes configuraciones de monitores, pruebas adicionales de GUI y verificaciÃ³n de compatibilidad real con aplicaciones que utilizan entrada exclusiva.

Consulta el [documento de pendientes](docs/roadmap/README.md) para el estudio de Roblox y mejoras previstas. El proyecto **no** incluye ejecutables, archivos ni herramientas de ingenierÃ­a inversa de Roblox.

## Licencia y contribuciones

**CÃ³digo fuente pÃºblico con derechos reservados.** No es una licencia de software libre ni de cÃ³digo abierto bajo OSI. Consulta [LICENSE](LICENSE) para conocer los permisos limitados de evaluaciÃ³n y la necesidad de autorizaciÃ³n para redistribuir o utilizar el proyecto comercialmente.

Las contribuciones mediante issues y pull requests son bienvenidas bajo las condiciones de [CONTRIBUTING.md](CONTRIBUTING.md). La titularidad original del proyecto corresponde a su autor y los colaboradores conservan su propia autorÃ­a segÃºn los tÃ©rminos descritos.

## Autor

[Jaime Arriagada Rosas](https://github.com/JaimeArriagadaRosas). Los SVG incluidos son recursos originales del proyecto.

