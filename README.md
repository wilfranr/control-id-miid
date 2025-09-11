# ControlId - Sistema Integrado con GUI

Sistema completo para la gestión de usuarios en ControlId con interfaz gráfica moderna, integración con MiID y manejo automático de imágenes.

## Características Principales

- **Interfaz Gráfica Moderna**: GUI intuitiva con CustomTkinter
- **Sincronización Automática**: Procesamiento cada 5 segundos
- **Gestión Inteligente de Usuarios**: Crear/modificar usuarios automáticamente
- **Manejo de Imágenes**: Descarga y asignación automática de fotos
- **Búsqueda Avanzada**: Por número de documento
- **Logs en Tiempo Real**: Monitoreo completo del proceso

## Estructura del Proyecto

### Archivos Principales

- `control_id_gui_final.py` - **Aplicación principal con GUI**
- `config.py` - Configuración centralizada del sistema
- `flujo_usuario_inteligente.py` - Lógica de procesamiento inteligente
- `GetUserMiID.py` - Conexión y consultas a MiID
- `GetUserByDocument.py` - Búsqueda de usuarios por documento
- `download_image_to_sql_temp.py` - Descarga de imágenes desde Azure

## Instalación

### Requisitos

- Python 3.7+
- Dependencias: Cree un archivo llamado `requirements.txt` en la raíz del proyecto y agregue las dependencias allí. Luego ejecute:

  ```bash
  pip install -r requirements.txt
  ```

### Configuración

#### Método 1: Interfaz Gráfica (Recomendado)

1. Ejecutar la aplicación: `python control_id_gui_final.py`
2. Hacer clic en el botón **"Config"** en la parte inferior
3. Modificar los parámetros en las pestañas correspondientes:
   - **MiID**: Configuración de MySQL
   - **Azure**: Configuración de Azure SQL
   - **ControlId**: Configuración del servidor ControlId
   - **Carpetas**: Rutas y extensiones de archivos
4. Hacer clic en **"Guardar Configuración"**

#### Método 2: Archivo de Configuración

Editar `config.py` manualmente con las credenciales correctas:

```python
# MiID (MySQL)
MIID_CONFIG = {
    "host": "miidsqldev.mysql.database.azure.com",
    "port": 3306,
    "user": "usuario",
    "password": "contraseña",
    "database": "miidcore"
}

# BykeeperDesarrollo (Azure SQL)
AZURE_CONFIG = {
    "servidor": "servidor.database.windows.net",
    "base_datos": "ByKeeper_Desarrollo",
    "usuario": "usuario",
    "contraseña": "contraseña",
    "stored_procedure": "dbo.GetMatchIDImgFaceByCASBid",
    "business_context": "MatchId"
}

# ControlId
CONTROL_ID_CONFIG = {
    "base_url": "http://192.168.5.8",
    "login": "admin",
    "password": "admin"
}
```

## Uso

### Ejecutar la Aplicación

```bash
python control_id_gui_final.py
```

### Funcionalidades de la GUI

1. **Sincronización Automática**

   - Ejecuta el proceso cada 5 segundos
   - Detecta nuevos usuarios automáticamente
   - Actualiza imágenes existentes

2. **Gestión de Usuarios**

   - Cargar último usuario de MiID
   - Buscar por número de documento
   - Visualizar información completa del usuario

3. **Manejo de Imágenes**

   - Descarga automática desde Azure Blob Storage
   - Asignación a usuarios en ControlId
   - Visualización en la interfaz

4. **Configuración Avanzada**

   - Ventana modal de configuración
   - Modificar parámetros sin tocar código
   - Pestañas organizadas por servicio
   - Guardar configuración automáticamente

5. **Monitoreo**

   - Logs en tiempo real
   - Estado de conexiones
   - Progreso de operaciones

## Construir Ejecutable (Windows)

Hay dos opciones de build. Ambos scripts crean una carpeta `dist/ControlIdGUI` con el ejecutable y dependencias.

- PowerShell:

  ```powershell
  # build en carpeta (recomendado para incluir config externo)
  ./build_exe.ps1

  # build onefile (ejecutable único)
  ./build_exe.ps1 -OneFile
  ```

- CMD (.bat):

  ```bat
  :: build en carpeta
  build_exe.bat

  :: build onefile
  build_exe.bat --onefile
  ```

Notas:
- Si existe `config.py` en la raíz al momento del build, se incluye junto al ejecutable. Alternativamente, puede distribuirse `config.py` junto al `.exe` y será cargado por la app.
- Recursos como `assets/images/logo.png` se incluyen automáticamente en el build.
- Para ejecutar en cualquier PC, copie el contenido de `dist/ControlIdGUI` (o el `.exe` si usó onefile).

## Flujo del Sistema

1. **Conexión**: Establece conexión con ControlId
2. **Sincronización**: Monitorea MiID cada 5 segundos
3. **Detección**: Identifica usuarios nuevos o actualizados
4. **Procesamiento**:
   - Descarga imagen desde BykeeperDesarrollo
   - Busca usuario en ControlId
   - Crea o modifica usuario según corresponda
   - Asigna imagen al usuario
5. **Visualización**: Muestra información en la GUI

## Funcionalidades Avanzadas

### Procesamiento Inteligente

- **Búsqueda por Documento**: Encuentra usuarios existentes
- **Creación/Modificación**: Maneja automáticamente ambos casos
- **Validación de Imágenes**: Verifica calidad y disponibilidad

### Interfaz de Usuario

- **Diseño Responsivo**: Adaptable a diferentes tamaños
- **Tema Oscuro**: Interfaz moderna y profesional
- **Logs Integrados**: Monitoreo en tiempo real
- **Controles Intuitivos**: Fácil de usar

## Monitoreo y Logs

El sistema genera logs detallados que incluyen:

- Estado de conexiones a bases de datos
- Progreso de descarga de imágenes
- Resultados de operaciones en ControlId
- Errores y excepciones
- Estadísticas de procesamiento

## Solución de Problemas

### Problemas Comunes

1. **Error de Conexión**: Verificar credenciales en `config.py`
2. **Imagen No Carga**: Verificar conectividad con Azure
3. **Usuario No Crea**: Verificar permisos en ControlId

### Logs de Debug

Los logs se muestran en tiempo real en la GUI y también se pueden exportar para análisis.

## Notas Importantes

- El sistema está diseñado para funcionar 24/7
- Las imágenes se procesan automáticamente
- Se mantiene un registro completo de todas las operaciones
- La interfaz es completamente funcional sin necesidad de comandos

## Estado del Proyecto

**COMPLETAMENTE FUNCIONAL**

- GUI moderna y responsive
- Sincronización automática
- Manejo completo de imágenes
- Logs en tiempo real
- Procesamiento inteligente de usuarios

---

**Desarrollado para ControlId - Sistema de Gestión de Usuarios**

