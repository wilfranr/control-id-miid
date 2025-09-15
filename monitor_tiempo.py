#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Monitor de tiempo en tiempo real para la carga masiva.
Ejecutar en una terminal separada para monitorear el progreso.
"""

import time
import psutil
import os
from datetime import datetime, timedelta
from pathlib import Path

def leer_archivo_log():
    """Leer el archivo de log para obtener información del progreso."""
    archivo_log = "carga_masiva.log"
    if not os.path.exists(archivo_log):
        return None, None, None
    
    try:
        with open(archivo_log, 'r', encoding='utf-8') as f:
            lineas = f.readlines()
        
        # Buscar información de progreso
        usuarios_procesados = 0
        usuarios_exitosos = 0
        usuarios_actualizados = 0
        usuarios_errores = 0
        
        for linea in lineas:
            if "Procesando" in linea and "/" in linea:
                try:
                    # Extraer número de usuario procesado
                    partes = linea.split("Procesando ")[1].split("/")[0]
                    usuarios_procesados = int(partes)
                except:
                    pass
            elif "✅ ÉXITO" in linea:
                usuarios_exitosos += 1
            elif "❌ ERROR" in linea:
                usuarios_errores += 1
            elif "(ACTUALIZADO)" in linea:
                usuarios_actualizados += 1
        
        return usuarios_procesados, usuarios_exitosos, usuarios_actualizados, usuarios_errores
    except:
        return None, None, None, None

def obtener_info_sistema():
    """Obtener información del sistema."""
    cpu_percent = psutil.cpu_percent(interval=1)
    memoria = psutil.virtual_memory()
    disco = psutil.disk_usage('/')
    
    return {
        'cpu': cpu_percent,
        'memoria_uso': memoria.used / 1024 / 1024,  # MB
        'memoria_total': memoria.total / 1024 / 1024,  # MB
        'memoria_porcentaje': memoria.percent,
        'disco_uso': disco.used / 1024 / 1024 / 1024,  # GB
        'disco_total': disco.total / 1024 / 1024 / 1024,  # GB
        'disco_porcentaje': (disco.used / disco.total) * 100
    }

def formatear_tiempo(segundos):
    """Formatear tiempo en formato legible."""
    if segundos < 60:
        return f"{segundos:.1f}s"
    elif segundos < 3600:
        minutos = int(segundos // 60)
        segs = int(segundos % 60)
        return f"{minutos}m {segs}s"
    else:
        horas = int(segundos // 3600)
        minutos = int((segundos % 3600) // 60)
        return f"{horas}h {minutos}m"

def main():
    """Función principal del monitor."""
    print("MONITOR DE TIEMPO - CARGA MASIVA")
    print("=" * 60)
    print("Presiona Ctrl+C para salir")
    print("=" * 60)
    
    inicio_monitor = time.time()
    total_usuarios = 2000  # Total esperado
    
    try:
        while True:
            # Limpiar pantalla (funciona en Windows y Linux)
            os.system('cls' if os.name == 'nt' else 'clear')
            
            print("MONITOR DE TIEMPO - CARGA MASIVA")
            print("=" * 60)
            print(f"Hora actual: {datetime.now().strftime('%H:%M:%S')}")
            print(f"Monitor activo: {formatear_tiempo(time.time() - inicio_monitor)}")
            print()
            
            # Leer progreso del log
            usuarios_procesados, exitosos, actualizados, errores = leer_archivo_log()
            
            if usuarios_procesados is not None:
                print("PROGRESO")
                print("-" * 30)
                print(f"Usuarios procesados: {usuarios_procesados}/{total_usuarios}")
                print(f"Progreso: {(usuarios_procesados/total_usuarios)*100:.1f}%")
                print(f"Exitosos: {exitosos}")
                print(f"Actualizados: {actualizados}")
                print(f"Errores: {errores}")
                
                if usuarios_procesados > 0:
                    # Calcular tiempo estimado
                    tiempo_transcurrido = time.time() - inicio_monitor
                    tiempo_por_usuario = tiempo_transcurrido / usuarios_procesados
                    usuarios_restantes = total_usuarios - usuarios_procesados
                    tiempo_estimado = usuarios_restantes * tiempo_por_usuario
                    
                    print()
                    print("TIEMPO")
                    print("-" * 30)
                    print(f"Tiempo transcurrido: {formatear_tiempo(tiempo_transcurrido)}")
                    print(f"Tiempo por usuario: {tiempo_por_usuario:.2f}s")
                    print(f"Tiempo estimado restante: {formatear_tiempo(tiempo_estimado)}")
                    
                    hora_fin = datetime.now() + timedelta(seconds=tiempo_estimado)
                    print(f"Hora estimada de fin: {hora_fin.strftime('%H:%M:%S')}")
                    
                    # Velocidad
                    velocidad = usuarios_procesados / (tiempo_transcurrido / 60)  # usuarios por minuto
                    print(f"Velocidad: {velocidad:.1f} usuarios/min")
            else:
                print("Esperando inicio del proceso...")
                print("Verificando archivo de log: carga_masiva.log")
            
            print()
            
            # Información del sistema
            info_sistema = obtener_info_sistema()
            print("SISTEMA")
            print("-" * 30)
            print(f"CPU: {info_sistema['cpu']:.1f}%")
            print(f"Memoria: {info_sistema['memoria_uso']:.0f}MB / {info_sistema['memoria_total']:.0f}MB ({info_sistema['memoria_porcentaje']:.1f}%)")
            print(f"Disco: {info_sistema['disco_uso']:.1f}GB / {info_sistema['disco_total']:.1f}GB ({info_sistema['disco_porcentaje']:.1f}%)")
            
            print()
            print("=" * 60)
            print("Actualizando cada 5 segundos... (Ctrl+C para salir)")
            
            time.sleep(5)
            
    except KeyboardInterrupt:
        print("\n\nMonitor detenido por el usuario")
        print("Gracias por usar el monitor de tiempo!")

if __name__ == "__main__":
    main()
