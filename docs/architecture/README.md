# Modular Single App — Arquitectura

La aplicación es un único programa Windows, desplegado como una unidad. **No es un monorepo**. El directorio `src/mouse_virtual` representa el paquete instalable y no un segundo proyecto.

## Estructura

- `app/`: bootstrap y composición de ventanas Qt.
- `modules/`: clicker, teclado, grabación, secuencias, reproducción, automatización y cursor virtual.
- `infrastructure/`: llamadas Win32, geometría y servicios técnicos.
- `resources/`: QSS y recursos incluidos en la compilación.
- `tests/`: pruebas externas al paquete.
- `scripts/`: comprobaciones manuales y bancadas de laboratorio.
- `docs/`: arquitectura, historial, investigación y roadmap.

## Direccionalidad

Interfaz Qt -> funcionalidades -> infraestructura. Evitar referencias de vuelta desde la infraestructura a la interfaz. Componentes visuales se comunicarán mediante señales o coordinadores en vez de acceso indiscriminado al host.

## Estado de migración y deuda

La primera migración reorganiza el código sin reemplazar su comportamiento. La clase principal se separa por capacidades en mixins. Estos mixins y el uso de `setup_automation_page(host)` **continúan temporalmente acoplados a la ventana principal**, y deben desacoplarse en una etapa posterior. No confundir separación física de archivos con desacoplamiento completo.

El límite de 300 líneas es una alerta para revisar responsabilidades, no una regla absoluta.

## Tests: ubicación y alcance

- `tests/unit`: validación, modelos, coordenadas y lógica pura.
- `tests/integration`: módulos cooperando y receptor Win32 propio.
- `tests/gui`: widgets Qt con `QT_QPA_PLATFORM=offscreen`.
- `tests/labs`: experimentos aislados, no pruebas sobre Roblox.
- `scripts`: ejecutables de prueba y herramientas operativas.

Las secuencias y logs de usuario se guardan fuera del repositorio, bajo `%LOCALAPPDATA%\MouseVirtual`. Los tests no deben contaminar esa ubicación cuando sea posible.
