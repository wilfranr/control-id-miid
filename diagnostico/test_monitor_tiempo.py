#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de prueba para verificar el monitor de tiempo.
Simula el procesamiento de usuarios para probar las estadísticas.
"""

import time
import logging
from datetime import datetime
from test_carga_masiva import MonitorTiempo

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_monitor.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def simular_procesamiento(monitor, total_usuarios=10):
    """Simular el procesamiento de usuarios."""
    logger.info(f"Iniciando simulación de {total_usuarios} usuarios")
    
    for i in range(1, total_usuarios + 1):
        documento = f"1234567{i:02d}"
        
        # Iniciar usuario
        monitor.iniciar_usuario(i, documento)
        logger.info(f"Procesando usuario {i}/{total_usuarios}: {documento}")
        
        # Simular tiempo de procesamiento variable
        tiempo_procesamiento = 0.5 + (i % 3) * 0.3  # 0.5 a 1.1 segundos
        time.sleep(tiempo_procesamiento)
        
        # Simular éxito/error (90% éxito)
        exito = i % 10 != 0
        actualizado = exito and (i % 3 == 0)  # 1/3 de los exitosos son actualizados
        
        # Finalizar usuario
        monitor.finalizar_usuario(exito, actualizado)
        
        if exito:
            logger.info(f"Usuario {i} procesado exitosamente" + (" (ACTUALIZADO)" if actualizado else ""))
        else:
            logger.info(f"Usuario {i} fallo")
        
        # Pausa entre usuarios
        time.sleep(0.1)

def main():
    """Función principal de prueba."""
    logger.info("=" * 60)
    logger.info("PRUEBA DEL MONITOR DE TIEMPO")
    logger.info("=" * 60)
    
    total_usuarios = 15
    monitor = MonitorTiempo(total_usuarios)
    
    # Iniciar monitor
    monitor.iniciar_proceso()
    
    try:
        # Simular procesamiento
        simular_procesamiento(monitor, total_usuarios)
        
    finally:
        # Finalizar monitor
        monitor.finalizar_proceso()
        
        # Mostrar estadísticas finales
        stats = monitor.obtener_estadisticas_finales()
        
        logger.info("\n" + "=" * 60)
        logger.info("ESTADÍSTICAS DE PRUEBA")
        logger.info("=" * 60)
        
        if stats:
            logger.info(f"Tiempo total: {stats['tiempo_total_formateado']}")
            logger.info(f"Tiempo promedio por usuario: {stats['tiempo_promedio_por_usuario']:.2f}s")
            logger.info(f"Usuarios procesados: {stats['usuarios_procesados']}")
            logger.info(f"Exitosos: {stats['usuarios_exitosos']}")
            logger.info(f"Actualizados: {stats['usuarios_actualizados']}")
            logger.info(f"Errores: {stats['usuarios_errores']}")
            logger.info(f"Porcentaje de exito: {stats['porcentaje_exito']:.1f}%")
            logger.info(f"Velocidad: {stats['velocidad_usuarios_por_minuto']:.1f} usuarios/min")
            logger.info(f"CPU: {stats['cpu_uso_promedio']:.1f}%")
            logger.info(f"Memoria: {stats['memoria_uso_mb']:.0f}MB / {stats['memoria_total_mb']:.0f}MB")
        
        logger.info("=" * 60)
        logger.info("Prueba del monitor completada")

if __name__ == "__main__":
    main()
