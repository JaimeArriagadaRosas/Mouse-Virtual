# Pestaña existente — cursor y escritura independientes

## Qué resuelve

Este adaptador permite seleccionar **una pestaña del Chrome que ya utiliza el usuario** y dirigirle movimientos, clics, texto, navegación y adjuntos de video. La pestaña permanece en su ventana y perfil existentes; el motor no crea perfiles nuevos ni mueve el cursor físico de Windows.

La vía de control es una extensión de Chrome MV3 que usa la API `chrome.debugger` y el protocolo CDP `Input.*`. El servicio Python solo escucha en `127.0.0.1:8765` y exige una clave aleatoria de 256 bits. No se transfieren cookies y no se activa ninguna API de mouse global.

**Permiso importante:** el permiso `debugger` concede amplias capacidades sobre la pestaña seleccionada y Chrome muestra una advertencia visible al habilitarlo. Instalar y conectar la extensión requiere una autorización inicial explícita del usuario; esta conexión no puede establecerse silenciosamente en su navegador.

## Primera conexión (una sola vez por instalación de Chrome)

1. Instalar la opción local `pip install -e ".[existing-tab]"` si todavía no está disponible.
2. Abrir **Mouse Virtual → Pestaña existente** y pulsar **Iniciar puente local**.
3. En el Chrome que ya está abierto, entrar a `chrome://extensions/`, activar *Modo de desarrollador* y pulsar *Cargar descomprimida*. Elegir la carpeta de instalación local (fuera del repositorio):
   `%LOCALAPPDATA%\MouseVirtual\existing-tab\extension`. La aplicación coloca allí una copia genérica al iniciar el puente, sin rutas de otros proyectos.
4. Abrir en la pestaña preparada una web HTTP o HTTPS de destino. La extensión no puede depurar algunas páginas internas `chrome://`.
5. Pulsar el icono de **Mouse Virtual · Existing Tab**, pegar el código local copiado desde la aplicación y seleccionar **Controlar esta pestaña**.
6. Cerrar el panel de la extensión; la pestaña queda enlazada. Desde la app se puede usar **Estado**, **Mover**, **Clic**, **Escribir**, **Ir a URL**, **Inspeccionar**, **Clic por selector**, **Llenar campo** y **Adjuntar video**.

No se requiere iniciar sesión de nuevo ni abrir otro perfil. La extensión trabaja con la sesión del Chrome existente. Solo queda conectado el identificador de la pestaña que autorizó el usuario.

## Seguridad

- No usar los métodos heredados de UI Automation Invoke sobre un Chrome en segundo plano: se demostró que pueden activar la ventana. El método quedó bloqueado en esa situación.
- El servidor local solo admite conexiones de una extensión `chrome-extension://...` autenticada y comandos locales autenticados con la misma clave.
- Para URL se exigen dominios explícitamente autorizados por solicitud.
- La carga de archivos se limita a extensiones de video y directorios previamente permitidos.
- No se ejecuta JavaScript arbitrario recibido por la conexión. La extensión solo ejecuta un conjunto fijo de acciones CDP, y sus expresiones internas de inspección y cursor no leen cookies ni contraseñas.
- Los planes, capturas, claves, extensión instalada y datos de aplicaciones se guardan **fuera del repositorio Git**, en el directorio local `%LOCALAPPDATA%\MouseVirtual\existing-tab`.
- En caso de fallo o resultado incierto no se reintenta una mutación automáticamente.
- Si el usuario abre Chrome DevTools para la misma pestaña, Chrome puede desconectar temporalmente el depurador de la extensión.

## Línea de comandos

Se puede utilizar sin abrir la UI, desde un terminal local, guardando la clave **fuera del repositorio**:

```powershell
python -m mouse_virtual.modules.agent_control.tab_bridge serve --token-file "$env:LOCALAPPDATA\MouseVirtual\existing-tab\pairing.key"
```

En otro proceso se escribe un plan JSON (una lista de acciones) en una ruta privada. Por ejemplo:

```json
[
  {"action":"status"},
  {"action":"move","x":180,"y":230},
  {"action":"dom.fill","selector":"#search","text":"consulta de prueba"},
  {"action":"dom.click","selector":"#go"}
]
```

```powershell
python -m mouse_virtual.modules.agent_control.tab_bridge run `
  --token-file "$env:LOCALAPPDATA\MouseVirtual\existing-tab\pairing.key" `
  --plan "D:\PrivateActions\steps.json" `
  --allow-writes
```

Para navegar agregue `--allow-host ejemplo.com`; para archivos adjuntos, `--allow-file-root D:\VideosAprobados`. No se puede usar una página de destino con cookies de una sesión diferente a la del Chrome donde se instaló la extensión.

## Pruebas disponibles

- Tests unitarios de tokens, orígenes, acciones, permisos, sitios y archivos autorizados.
- Prueba del puente con una extensión simulada, incluyendo rechazo de clave incorrecta y orígenes no autorizados.
- Prueba real de Chromium MV3 en segundo plano con una página HTTP local: `inspect`, `move`, `dom.fill`, `dom.click` y captura PNG vía CDP; se confirmó que la pestaña controlada seguía inactiva.
- Capturas: la acción `screenshot` en la aplicación guarda un PNG de la pestaña en el directorio local privado, sin traerla al frente.
- Prueba Qt con `QT_QPA_PLATFORM=offscreen`, sin abrir ninguna ventana visible.

## Limitaciones

No instala extensiones sin la intervención inicial del usuario. Algunos sitios pueden denegar depuración o requerir confirmaciones adicionales; tampoco se intenta evadir verificaciones. Aunque el navegador puede permanecer detrás de otra ventana y no recibe entradas globales, Chrome conserva la facultad de mostrar avisos de seguridad propios.

## Conexión automática y recuperación (rama experimental)

Tras el primer emparejamiento, la extensión almacena la clave **solo en el
almacenamiento local de Chrome de esa extensión**, nunca en Git. Al reiniciar
el service worker o el navegador, intenta recuperar la pestaña autorizada.

- Reintenta conexión al puente local con espera exponencial acotada.
- Un aviso periódico de Chrome revisa el estado cada minuto.
- El puente contesta los mensajes de actividad para evitar desconexiones
  por inactividad en Manifest V3.
- Ninguna acción de escritura fallida se reintenta automáticamente.
- Si la pestaña original se cierra, sigue otra pestaña **inactiva** del mismo
  sitio únicamente cuando haya una coincidencia única. Ante ambigüedad, no
  controla otra pestaña sin selección explícita.
- Desde el panel se puede cambiar a otra pestaña del mismo navegador sin
  volver a introducir la clave, siempre que el destino esté inactivo y
  autorizado por la lista de hosts del programa local.
- El usuario puede desactivar el seguimiento, comprobar conexión o revocar
  el emparejamiento desde la extensión.
- La aplicación Mouse Virtual arranca/reutiliza el puente local al iniciarse
  y lo supervisa cada seis segundos mientras permanezca abierta.

**Actualización del desarrollo:** al cambiar el código de una extensión
descomprimida, Chrome exige pulsar una vez «Recargar» en chrome://extensions
para cargar la nueva versión. Este paso es diferente de autorizar cada
pestaña; después de actualizar y emparejar una vez, no debería ser necesario
repetir el código en cada corte de conexión. Chrome puede mostrar su aviso
normal de depuración, que no se intenta ocultar.

Si el usuario revoca la conexión de Chrome o abre DevTools sobre la misma
pestaña y reemplaza al depurador, la extensión respeta esa decisión y no
vuelve a conectarse silenciosamente.
