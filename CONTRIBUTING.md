# Contribuir a Mouse Virtual

Gracias por tu interés en mejorar el proyecto. **Mouse Virtual es desarrollado y mantenido principalmente por Jaime Andrés Arriagada Rosas**. Las contribuciones son bienvenidas, pero el proyecto **no es software de código abierto bajo una licencia OSI**.

## Antes de comenzar

1. Lee [LICENSE](LICENSE) y [docs/architecture/README.md](docs/architecture/README.md).
2. Abre un issue con el error o mejora que propones. En cambios grandes, acuerda primero el alcance.
3. Trabaja en una rama propia y mantén los commits pequeños y descriptivos.
4. Ejecuta las pruebas de unidad, integración y GUI aislada.
5. Abre un pull request describiendo el problema, la solución, los riesgos y las pruebas.

## Reglas técnicas

- Mantener arquitectura Modular Single App; un solo paquete instalable.
- Preferir archivos con menos de 300 líneas; si exceden, documentar el motivo.
- Separar lógica de negocio, interfaz Qt y adaptadores Win32.
- No agregar dependencias a servicios externos ni automatizaciones invasivas sin revisión.
- No presentar los mensajes publicados como clics confirmados por otros programas.
- No subir datos personales, tokens, ejecutables de terceros, carpetas .venv, logs de usuario o binarios de Roblox/REA.
- Agregar pruebas para cambios de comportamiento y respetar las secuencias existentes.
- El proyecto no promueve saltarse protecciones ni sistemas de seguridad de otras aplicaciones.

## Autoría y licencia de contribuciones

Conservas la autoría de cualquier código original que aportes; el proyecto seguirá reconociendo tu contribución cuando corresponda. Al enviar un pull request aceptas la licencia de aportaciones indicada en [LICENSE](LICENSE), que autoriza al mantenedor a incorporar, adaptar y distribuir tus cambios como parte de Mouse Virtual. No envíes código de terceros sin derechos suficientes.

**No está permitida la redistribución del proyecto como otro producto sin autorización expresa**; la disponibilidad pública del repositorio no concede ese permiso.

## Pruebas

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[test]"
.\.venv\Scripts\python.exe -m pytest -q tests
```

Para pruebas de GUI, utiliza el modo Qt offscreen; para el adaptador Win32, las pruebas están limitadas al receptor interno.
