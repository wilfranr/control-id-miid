# Script de Carga Masiva - ControlId

Este script está diseñado para procesar 2000 usuarios desde un archivo Excel, buscarlos en MiID, crearlos en ControlId, asignarles imágenes desde una carpeta local y asignarles un grupo de usuario.

## ⚠️ IMPORTANTE - CONFIGURACIÓN REQUERIDA

**ANTES DE EJECUTAR EL SCRIPT, DEBES MODIFICAR LAS CREDENCIALES HARDCODEADAS:**

1. Abre el archivo `test_carga_masiva.py`
2. Busca la sección "CONFIGURACIÓN HARDCODEADA"
3. Actualiza las siguientes configuraciones:

### Configuración MiID (MySQL)
```python
MIID_CONFIG = {
    "host": "tu-host-miid.com",
    "port": 3306,
    "user": "tu_usuario_miid",
    "password": "tu_contraseña_miid",
    "database": "miidcore"
}
```

### Configuración Azure SQL (BykeeperDesarrollo)
```python
AZURE_CONFIG = {
    "servidor": "tu-servidor.database.windows.net",
    "base_datos": "ByKeeper_Desarrollo",
    "usuario": "tu_usuario_azure",
    "contraseña": "tu_contraseña_azure",
    "stored_procedure": "dbo.GetMatchIDImgFaceByCASBid",
    "business_context": "Bytte"
}
```

### Configuración ControlId
```python
CONTROL_ID_CONFIG = {
    "base_url": "http://tu-servidor-controlid.com",
    "login": "tu_usuario_controlid",
    "password": "tu_contraseña_controlid"
}
```

## Estructura de Archivos Requerida

```
ControlId/
├── test_carga_masiva.py          # Script principal
├── tests/
│   └── clientes.xlsx             # Archivo con 2000 números de documento
└── C:\Users\wilfran.rivera\Downloads\Imagenes Facial MiID\
    ├── 1107008460.jpg           # Imágenes renombradas con números de documento
    ├── 1233188921.jpg
    ├── 1003157606.jpg
    └── ... (2000 imágenes en total)
```

## Flujo del Proceso

Para cada documento del Excel, el script:

1. **Busca en MiID**: Obtiene datos del usuario (nombre, LPID, etc.)
2. **Verifica en ControlId**: Si el usuario ya existe
3. **Crea/Actualiza en ControlId**: Crea nuevo usuario o actualiza existente
4. **Busca imagen local**: Busca la imagen correspondiente en la carpeta
5. **Asigna imagen**: Sube la imagen al usuario en ControlId
6. **Asigna grupo**: Asigna el grupo de usuario (ID: 1002)

## Instalación de Dependencias

```bash
pip install pandas mysql-connector-python pyodbc requests openpyxl
```

## Ejecución del Script

```bash
python test_carga_masiva.py
```

El script pedirá confirmación antes de ejecutar:
```
¿Desea continuar con la carga masiva? (sí/no):
```

## Configuración del Proceso

Puedes modificar estos parámetros en el script:

```python
PROCESO_CONFIG = {
    "archivo_excel": "tests/clientes.xlsx",
    "columna_documentos": "Clientes",
    "grupo_usuario_id": 1002,              # ID del grupo a asignar
    "delay_entre_usuarios": 0.5,           # Segundos de espera entre usuarios
    "max_reintentos": 3,                   # Reintentos en caso de error
    "timeout_requests": 30                 # Timeout para requests HTTP
}
```

## Logs y Resultados

### Archivo de Log
- `carga_masiva.log`: Log detallado del proceso

### Archivo de Resultados
- `resultados_carga_masiva_YYYYMMDD_HHMMSS.json`: Resultados detallados en JSON

### Estadísticas Mostradas
- Total procesados
- Exitosos vs Con errores
- No encontrados en MiID
- Errores de creación
- Imágenes asignadas
- Grupos asignados

## Ejemplo de Salida

```
[INFO] [1/2000] Procesando documento: 1107008460
[INFO] [1/2000] Usuario encontrado en MiID: Usuario_1107008460
[INFO] [1/2000] Creando usuario en ControlId...
[INFO] [1/2000] Usuario creado en ControlId: ID 12345
[INFO] [1/2000] Imagen encontrada: 1107008460.jpg
[INFO] [1/2000] Imagen asignada exitosamente
[INFO] [1/2000] Grupo asignado exitosamente
[INFO] [1/2000] Procesamiento completado: ÉXITO
```

## Manejo de Errores

El script maneja los siguientes tipos de errores:

- **Usuario no encontrado en MiID**: Se registra pero continúa
- **Error de conexión**: Se registra y continúa con el siguiente
- **Imagen no encontrada**: Se registra pero continúa
- **Error de creación en ControlId**: Se registra y continúa

## Interrupción del Proceso

- Presiona `Ctrl+C` para interrumpir el proceso
- Los resultados hasta el momento se guardarán automáticamente

## Verificación Post-Proceso

Después de ejecutar el script, puedes verificar:

1. **En ControlId**: Que los usuarios fueron creados correctamente
2. **Imágenes**: Que las imágenes fueron asignadas
3. **Grupos**: Que los usuarios tienen el grupo 1002 asignado
4. **Logs**: Revisar el archivo de log para errores específicos

## Notas Importantes

- ⚠️ **NO EJECUTAR EN PRODUCCIÓN** sin verificar las credenciales
- El script está diseñado para ser robusto y continuar aunque algunos usuarios fallen
- Se recomienda hacer una prueba con pocos usuarios primero
- El proceso puede tomar varias horas para 2000 usuarios (dependiendo del delay configurado)

## Solución de Problemas

### Error de conexión a MiID
- Verificar credenciales de MySQL
- Verificar que el servidor esté accesible

### Error de conexión a ControlId
- Verificar URL base y credenciales
- Verificar que el servidor esté accesible

### Imágenes no encontradas
- Verificar que las imágenes estén en la carpeta correcta
- Verificar que los nombres coincidan con los números de documento
- Verificar extensiones de archivo (.jpg, .jpeg, .png)

### Error de permisos
- Ejecutar como administrador si es necesario
- Verificar permisos de escritura en las carpetas
