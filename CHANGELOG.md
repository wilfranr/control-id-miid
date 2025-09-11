# Changelog

Todas las modificaciones relevantes de este proyecto serán documentadas en este archivo.

## [1.2.0] - 2025-09-11
### Añadido
- Empaquetado para Windows con PyInstaller: ejecutable en carpeta y onefile.
- Scripts de build: `build_exe.ps1` y `build_exe.bat`.
- Archivo `.spec` con recursos y `hiddenimports`.
- Dependencia `pyodbc` para Azure SQL.

### Notas de distribución
- Onefile: `dist/ControlIdGUI.exe` (recomendado para compartir).
- Carpeta: `dist/ControlIdGUI/` (incluye recursos y `config.py`).
- Requiere ODBC Driver 17/18 para SQL Server en el equipo destino.

## [1.1.0] - 2025-09-11
### Añadido
- Modal de pruebas de conexión en Config con logs en tiempo real.
- Prechequeo de conexiones (MiID, Azure, ControlId) al iniciar la aplicación.
- Actualización del estado global: muestra "Conectado" solo si todas las conexiones están OK; abre modal con logs si alguna falla.
- Logs de resumen al inicio por servicio: `[MiID] OK/FALLÓ`, `[Azure] OK/FALLÓ`, `[ControlId] OK/FALLÓ`.

### Cambiado
- Botón "Probar Conexiones" ahora abre el modal y ejecuta pruebas en hilo sin bloquear la UI.
- Eliminado popup de éxito al inicio cuando todo está OK (se mantiene el estado visual y log).

### Interno
- Nueva clase `ModalPruebasConexiones` en `control_id_gui_final.py`.

## [1.0.0] - 2025-09-01
- Versión inicial con GUI principal, sincronización automática y manejo de imágenes.
