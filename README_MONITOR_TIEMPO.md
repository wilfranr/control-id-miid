# Monitor de Tiempo - Carga Masiva ControlId

Este documento explica cómo usar las herramientas de medición de tiempo para la carga masiva de usuarios.

## Herramientas Disponibles

### 1. **Script de Carga Masiva con Monitor Integrado**
- **Archivo**: `test_carga_masiva.py`
- **Descripción**: Script principal con monitor de tiempo integrado
- **Características**:
  - Medición de tiempo total y por usuario
  - Estadísticas en tiempo real cada 30 segundos
  - Cálculo de velocidad de procesamiento
  - Monitoreo de CPU y memoria
  - Estimación de tiempo restante

### 2. **Monitor de Tiempo en Tiempo Real**
- **Archivo**: `monitor_tiempo.py`
- **Descripción**: Monitor independiente que se ejecuta en paralelo
- **Uso**: Ejecutar en una terminal separada mientras corre la carga masiva

### 3. **Script de Prueba del Monitor**
- **Archivo**: `test_monitor_tiempo.py`
- **Descripción**: Prueba el funcionamiento del monitor con datos simulados

## Como Usar

### Opción 1: Solo Carga Masiva (Recomendado)
```bash
# Ejecutar solo el script principal
python test_carga_masiva.py
```

**Características**:
- Monitor integrado que muestra estadísticas cada 30 segundos
- Estadísticas finales detalladas al terminar
- Archivo JSON con todos los datos de tiempo y rendimiento

### Opción 2: Carga Masiva + Monitor Externo
```bash
# Terminal 1: Ejecutar carga masiva
python test_carga_masiva.py

# Terminal 2: Ejecutar monitor externo (opcional)
python monitor_tiempo.py
```

**Características**:
- Monitor integrado en el script principal
- Monitor externo con actualización cada 5 segundos
- Vista en tiempo real del progreso

## Estadísticas que se Miden

### Tiempo
- **Tiempo total** del proceso completo
- **Tiempo promedio** por usuario
- **Tiempo mínimo** y **máximo** por usuario
- **Tiempo estimado restante** (basado en velocidad actual)
- **Hora estimada de finalización**

### Progreso
- **Usuarios procesados** vs total
- **Porcentaje de progreso**
- **Usuarios exitosos** vs con errores
- **Usuarios actualizados** (datos modificados)
- **Velocidad** (usuarios por minuto)

### Sistema
- **Uso de CPU** (porcentaje)
- **Uso de memoria** (MB y porcentaje)
- **Uso de disco** (GB y porcentaje)

## Archivos Generados

### 1. **Archivo de Log Principal**
- **Nombre**: `carga_masiva.log`
- **Contenido**: Log detallado de todo el proceso
- **Formato**: Timestamp - Nivel - Mensaje

### 2. **Archivo de Resultados JSON**
- **Nombre**: `resultados_carga_masiva_YYYYMMDD_HHMMSS.json`
- **Contenido**:
  ```json
  {
    "estadisticas": {
      "total": 2000,
      "exitosos": 1950,
      "con_errores": 50,
      "usuarios_actualizados": 300
    },
    "estadisticas_tiempo": {
      "tiempo_total_segundos": 1200.5,
      "tiempo_total_formateado": "20m 0s",
      "tiempo_promedio_por_usuario": 0.6,
      "velocidad_usuarios_por_minuto": 100.0,
      "cpu_uso_promedio": 45.2,
      "memoria_uso_mb": 512.3
    },
    "resultados_detallados": [...],
    "configuracion": {...}
  }
  ```

## Estimaciones de Tiempo

### Basado en Pruebas Realizadas:
- **Tiempo promedio por usuario**: ~0.6-0.8 segundos
- **Velocidad estimada**: ~75-100 usuarios/minuto
- **Tiempo total estimado para 2000 usuarios**: ~20-25 minutos

### Factores que Afectan el Tiempo:
1. **Conexión a MiID**: Velocidad de consultas SQL
2. **Conexión a ControlId**: Latencia de API
3. **Procesamiento de imágenes**: Tamaño y formato de archivos
4. **Red**: Estabilidad de conexiones
5. **Sistema**: CPU y memoria disponibles

## Configuracion Avanzada

### Modificar Intervalo de Estadísticas Intermedias
En `test_carga_masiva.py`, línea 83:
```python
time.sleep(30)  # Cambiar a 60 para cada minuto
```

### Modificar Intervalo del Monitor Externo
En `monitor_tiempo.py`, línea 120:
```python
time.sleep(5)  # Cambiar a 10 para cada 10 segundos
```

## Solucion de Problemas

### Error: "ModuleNotFoundError: No module named 'psutil'"
```bash
pip install psutil
```

### El monitor no muestra estadísticas
- Verificar que el archivo `carga_masiva.log` existe
- Verificar que el proceso de carga masiva está ejecutándose
- Verificar permisos de lectura del archivo de log

### Estadísticas incorrectas
- Verificar que el formato del log no ha cambiado
- Verificar que el monitor está leyendo el archivo correcto
- Reiniciar el monitor si es necesario

## Interpretacion de Resultados

### Tiempo por Usuario
- **< 0.5s**: Excelente rendimiento
- **0.5-1.0s**: Buen rendimiento
- **1.0-2.0s**: Rendimiento aceptable
- **> 2.0s**: Posibles problemas de red o sistema

### Velocidad de Procesamiento
- **> 100 usuarios/min**: Excelente
- **75-100 usuarios/min**: Bueno
- **50-75 usuarios/min**: Aceptable
- **< 50 usuarios/min**: Revisar configuración

### Uso de Recursos
- **CPU < 50%**: Sistema cómodo
- **CPU 50-80%**: Sistema trabajando
- **CPU > 80%**: Posible cuello de botella
- **Memoria > 80%**: Posible problema de memoria

## Recomendaciones

1. **Ejecutar en horario de menor tráfico** para mejor rendimiento
2. **Monitorear el sistema** durante la ejecución
3. **Tener respaldo** de la base de datos antes de ejecutar
4. **Revisar logs** después de la ejecución
5. **Verificar resultados** en ControlId después de completar

## Soporte

Si encuentras problemas con el monitor de tiempo:
1. Revisar los logs generados
2. Verificar que todas las dependencias estén instaladas
3. Probar con el script de prueba (`test_monitor_tiempo.py`)
4. Verificar permisos de archivos y carpetas
