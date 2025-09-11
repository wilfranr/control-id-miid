#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de prueba de carga masiva para ControlId.
Procesa 2000 usuarios desde Excel, los busca en MiID, los crea en ControlId,
les asigna imagen desde carpeta local y les asigna grupo_usuario.

CREDENCIALES HARDCODEADAS - NO USAR EN PRODUCCIÓN
"""

import pandas as pd
import mysql.connector
import pyodbc
import requests
import json
import logging
import time
import threading
import psutil
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('carga_masiva.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# =============================================================================
# CLASE DE MONITOREO DE TIEMPO Y RENDIMIENTO
# =============================================================================

class MonitorTiempo:
    """Monitor de tiempo y rendimiento para la carga masiva."""
    
    def __init__(self, total_usuarios: int):
        self.total_usuarios = total_usuarios
        self.inicio_proceso = None
        self.inicio_usuario = None
        self.tiempos_usuarios = []
        self.usuarios_procesados = 0
        self.usuarios_exitosos = 0
        self.usuarios_actualizados = 0
        self.usuarios_errores = 0
        self.monitor_activo = False
        self.thread_monitor = None
        
    def iniciar_proceso(self):
        """Iniciar el monitoreo del proceso completo."""
        self.inicio_proceso = time.time()
        self.monitor_activo = True
        self.thread_monitor = threading.Thread(target=self._monitor_continuo, daemon=True)
        self.thread_monitor.start()
        logger.info("Monitor de tiempo iniciado")
        
    def iniciar_usuario(self, indice: int, documento: str):
        """Iniciar el monitoreo de un usuario individual."""
        self.inicio_usuario = time.time()
        
    def finalizar_usuario(self, exito: bool, actualizado: bool = False):
        """Finalizar el monitoreo de un usuario individual."""
        if self.inicio_usuario:
            tiempo_usuario = time.time() - self.inicio_usuario
            self.tiempos_usuarios.append(tiempo_usuario)
            self.usuarios_procesados += 1
            
            if exito:
                self.usuarios_exitosos += 1
                if actualizado:
                    self.usuarios_actualizados += 1
            else:
                self.usuarios_errores += 1
                
    def _monitor_continuo(self):
        """Monitor continuo que muestra estadísticas cada 30 segundos."""
        while self.monitor_activo:
            time.sleep(30)  # Mostrar cada 30 segundos
            if self.usuarios_procesados > 0:
                self._mostrar_estadisticas_intermedias()
                
    def _mostrar_estadisticas_intermedias(self):
        """Mostrar estadísticas intermedias del proceso."""
        if not self.inicio_proceso:
            return
            
        tiempo_transcurrido = time.time() - self.inicio_proceso
        tiempo_por_usuario = sum(self.tiempos_usuarios) / len(self.tiempos_usuarios) if self.tiempos_usuarios else 0
        usuarios_restantes = self.total_usuarios - self.usuarios_procesados
        tiempo_estimado_restante = usuarios_restantes * tiempo_por_usuario
        
        logger.info("=" * 80)
        logger.info("ESTADISTICAS INTERMEDIAS")
        logger.info("=" * 80)
        logger.info(f"Tiempo transcurrido: {self._formatear_tiempo(tiempo_transcurrido)}")
        logger.info(f"Usuarios procesados: {self.usuarios_procesados}/{self.total_usuarios} ({self.usuarios_procesados/self.total_usuarios*100:.1f}%)")
        logger.info(f"Exitosos: {self.usuarios_exitosos}")
        logger.info(f"Actualizados: {self.usuarios_actualizados}")
        logger.info(f"Errores: {self.usuarios_errores}")
        logger.info(f"Velocidad promedio: {tiempo_por_usuario:.2f}s por usuario")
        logger.info(f"Tiempo estimado restante: {self._formatear_tiempo(tiempo_estimado_restante)}")
        logger.info(f"Hora estimada de finalizacion: {self._calcular_hora_fin()}")
        logger.info("=" * 80)
        
    def finalizar_proceso(self):
        """Finalizar el monitoreo del proceso completo."""
        self.monitor_activo = False
        if self.thread_monitor:
            self.thread_monitor.join(timeout=1)
            
    def obtener_estadisticas_finales(self) -> Dict[str, Any]:
        """Obtener estadísticas finales del proceso."""
        if not self.inicio_proceso:
            return {}
            
        tiempo_total = time.time() - self.inicio_proceso
        tiempo_promedio = sum(self.tiempos_usuarios) / len(self.tiempos_usuarios) if self.tiempos_usuarios else 0
        tiempo_minimo = min(self.tiempos_usuarios) if self.tiempos_usuarios else 0
        tiempo_maximo = max(self.tiempos_usuarios) if self.tiempos_usuarios else 0
        
        # Obtener información del sistema
        cpu_percent = psutil.cpu_percent(interval=1)
        memoria = psutil.virtual_memory()
        
        return {
            "tiempo_total_segundos": tiempo_total,
            "tiempo_total_formateado": self._formatear_tiempo(tiempo_total),
            "tiempo_promedio_por_usuario": tiempo_promedio,
            "tiempo_minimo_usuario": tiempo_minimo,
            "tiempo_maximo_usuario": tiempo_maximo,
            "usuarios_procesados": self.usuarios_procesados,
            "usuarios_exitosos": self.usuarios_exitosos,
            "usuarios_actualizados": self.usuarios_actualizados,
            "usuarios_errores": self.usuarios_errores,
            "porcentaje_exito": (self.usuarios_exitosos / self.usuarios_procesados * 100) if self.usuarios_procesados > 0 else 0,
            "velocidad_usuarios_por_minuto": (self.usuarios_procesados / tiempo_total * 60) if tiempo_total > 0 else 0,
            "cpu_uso_promedio": cpu_percent,
            "memoria_uso_mb": memoria.used / 1024 / 1024,
            "memoria_total_mb": memoria.total / 1024 / 1024
        }
        
    def _formatear_tiempo(self, segundos: float) -> str:
        """Formatear tiempo en formato legible."""
        if segundos < 60:
            return f"{segundos:.1f} segundos"
        elif segundos < 3600:
            minutos = int(segundos // 60)
            segs = int(segundos % 60)
            return f"{minutos}m {segs}s"
        else:
            horas = int(segundos // 3600)
            minutos = int((segundos % 3600) // 60)
            return f"{horas}h {minutos}m"
            
    def _calcular_hora_fin(self) -> str:
        """Calcular hora estimada de finalización."""
        if not self.inicio_proceso or self.usuarios_procesados == 0:
            return "N/A"
            
        tiempo_transcurrido = time.time() - self.inicio_proceso
        tiempo_por_usuario = sum(self.tiempos_usuarios) / len(self.tiempos_usuarios)
        usuarios_restantes = self.total_usuarios - self.usuarios_procesados
        tiempo_estimado_restante = usuarios_restantes * tiempo_por_usuario
        
        hora_fin = datetime.now() + timedelta(seconds=tiempo_estimado_restante)
        return hora_fin.strftime("%H:%M:%S")

# =============================================================================
# CONFIGURACIÓN HARDCODEADA - MODIFICAR SEGÚN NECESIDADES
# =============================================================================

# Configuración MiID (MySQL)
MIID_CONFIG = {
    "host": "miidsqlprod.mysql.database.azure.com",
    "port": 3306,
    "user": "Wilfran.Rivera",
    "password": "zi4i1WFBpRX8*Bytte",
    "database": "miidcore"
}

# Configuración Azure SQL (BykeeperDesarrollo)
AZURE_CONFIG = {
    "servidor": "inspruebas.database.windows.net",
    "base_datos": "ByKeeper_Desarrollo",
    "usuario": "MonitorOp",
    "contraseña": "zi3i1WFBpRX8*Bytte",
    "stored_procedure": "dbo.GetMatchIDImgFaceByCASBid",
    "business_context": "MatchId"
}

# Configuración ControlId
CONTROL_ID_CONFIG = {
    "base_url": "http://192.168.3.37",
    "login": "admin",
    "password": "admin"
}

# Configuración de carpetas
CARPETAS_CONFIG = {
    "carpeta_imagenes": r"C:\Users\wilfran.rivera\Downloads\Imagenes Facial MiID",  # Carpeta con las 2000 imágenes
    "carpeta_local_temp": r"C:\temp\Imagenes_Pro",
    "extension_imagen": ".jpg"
}

# Configuración del proceso
PROCESO_CONFIG = {
    "archivo_excel": "tests/clientes.xlsx",
    "columna_documentos": "Clientes",
    "grupo_usuario_id": 1002,
    "delay_entre_usuarios": 0.2,  # Segundos de espera entre usuarios
    "max_reintentos": 3,
    "timeout_requests": 30
}

# =============================================================================
# FUNCIONES DE CONEXIÓN
# =============================================================================

def conectar_miid() -> Optional[mysql.connector.connection.MySQLConnection]:
    """Conectar a MiID MySQL."""
    try:
        logger.info("Conectando a MiID...")
        conexion = mysql.connector.connect(**MIID_CONFIG)
        logger.info("Conexión a MiID establecida")
        return conexion
    except Exception as e:
        logger.error(f"Error al conectar a MiID: {e}")
        return None

def conectar_azure() -> Optional[pyodbc.Connection]:
    """Conectar a Azure SQL."""
    try:
        logger.info("Conectando a Azure SQL...")
        connection_string = (
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={AZURE_CONFIG['servidor']};"
            f"DATABASE={AZURE_CONFIG['base_datos']};"
            f"UID={AZURE_CONFIG['usuario']};"
            f"PWD={AZURE_CONFIG['contraseña']};"
            f"Encrypt=yes;"
            f"TrustServerCertificate=no;"
        )
        conexion = pyodbc.connect(connection_string)
        logger.info("Conexión a Azure SQL establecida")
        return conexion
    except Exception as e:
        logger.error(f"Error al conectar a Azure SQL: {e}")
        return None

def obtener_sesion_controlid() -> Optional[str]:
    """Obtener sesión de ControlId."""
    try:
        logger.info("Obteniendo sesión de ControlId...")
        url = f"{CONTROL_ID_CONFIG['base_url']}/login.fcgi"
        payload = {
            "login": CONTROL_ID_CONFIG['login'],
            "password": CONTROL_ID_CONFIG['password']
        }
        headers = {"Content-Type": "application/json"}
        
        response = requests.post(url, json=payload, headers=headers, timeout=PROCESO_CONFIG['timeout_requests'])
        response.raise_for_status()
        
        response_data = response.json()
        if 'session' in response_data:
            session = response_data['session']
            logger.info("Sesión de ControlId obtenida")
            return session
        else:
            logger.error("No se encontró sesión en la respuesta")
            return None
            
    except Exception as e:
        logger.error(f"Error al obtener sesión de ControlId: {e}")
        return None

# =============================================================================
# FUNCIONES DE BÚSQUEDA Y PROCESAMIENTO
# =============================================================================

def buscar_usuario_miid(conexion_miid: mysql.connector.connection.MySQLConnection, documento: str) -> Optional[Dict[str, Any]]:
    """Buscar usuario en MiID por documento."""
    try:
        cursor = conexion_miid.cursor()
        
        query = """
        SELECT
            lpe.LP_ID,
            p.PER_DOCUMENT_NUMBER,
            COALESCE(
                NULLIF(TRIM(CONCAT(
                    COALESCE(p.PER_FIRST_NAME, ''), 
                    ' ', 
                    COALESCE(p.PER_LAST_NAME, '')
                )), ''), 
                CONCAT('Usuario_', p.PER_DOCUMENT_NUMBER)
            ) AS NOMBRE_COMPLETO,
            lpe.LP_CREATION_DATE,
            lpe.LP_STATUS_PROCESS
        FROM log_process_enroll lpe
        INNER JOIN person p ON lpe.PER_ID = p.PER_ID
        WHERE p.PER_DOCUMENT_NUMBER = %s
        ORDER BY lpe.LP_CREATION_DATE DESC
        LIMIT 1
        """
        
        cursor.execute(query, (documento,))
        usuario = cursor.fetchone()
        
        if usuario:
            (lp_id, doc_num, nombre_completo, creation_date, status_process) = usuario
            
            return {
                'lpid': lp_id,
                'documento': doc_num,
                'nombre': nombre_completo,
                'fecha_creacion': creation_date,
                'estado': status_process
            }
        else:
            return None
            
    except Exception as e:
        logger.error(f"Error al buscar usuario en MiID: {e}")
        return None
    finally:
        if 'cursor' in locals():
            cursor.close()

def buscar_usuario_controlid(session: str, documento: str) -> Optional[Dict[str, Any]]:
    """Buscar usuario en ControlId por documento."""
    try:
        url = f"{CONTROL_ID_CONFIG['base_url']}/load_objects.fcgi"
        params = {'session': session}
        payload = {"object": "users"}
        headers = {"Content-Type": "application/json"}
        
        response = requests.post(url, params=params, headers=headers, json=payload, timeout=PROCESO_CONFIG['timeout_requests'])
        response.raise_for_status()
        
        response_data = response.json()
        
        # Buscar usuario por registration
        if 'users' in response_data and isinstance(response_data['users'], list):
            for usuario in response_data['users']:
                if usuario.get('registration') == documento:
                    return usuario
        elif 'data' in response_data and isinstance(response_data['data'], list):
            for usuario in response_data['data']:
                if usuario.get('registration') == documento:
                    return usuario
        
        return None
        
    except Exception as e:
        logger.error(f"Error al buscar usuario en ControlId: {e}")
        return None

def crear_usuario_controlid(session: str, nombre: str, documento: str) -> Optional[str]:
    """Crear usuario en ControlId."""
    try:
        url = f"{CONTROL_ID_CONFIG['base_url']}/create_objects.fcgi"
        params = {'session': session}
        payload = {
            "object": "users",
            "values": [
                {
                    "name": nombre,
                    "registration": documento,
                    "password": "",
                    "salt": ""
                }
            ]
        }
        headers = {"Content-Type": "application/json"}
        
        response = requests.post(url, params=params, headers=headers, json=payload, timeout=PROCESO_CONFIG['timeout_requests'])
        
        # Log detallado de la respuesta para debugging
        logger.info(f"Respuesta de creación de usuario - Status: {response.status_code}")
        logger.info(f"Respuesta de creación de usuario - Headers: {dict(response.headers)}")
        logger.info(f"Respuesta de creación de usuario - Content: {response.text}")
        
        # Si no es 200, detener el proceso para revisar
        if response.status_code != 200:
            logger.error(f"ERROR CRÍTICO: La creación de usuario falló con status {response.status_code}")
            logger.error(f"Respuesta completa: {response.text}")
            logger.error("DETENIENDO EL PROCESO PARA REVISAR EL CASO ESPECÍFICO")
            raise Exception(f"Error en creación de usuario: Status {response.status_code}")
        
        response.raise_for_status()
        
        response_data = response.json()
        
        # Extraer ID del usuario creado
        user_id = None
        if 'id' in response_data:
            user_id = response_data['id']
        elif 'ids' in response_data and isinstance(response_data['ids'], list) and len(response_data['ids']) > 0:
            user_id = response_data['ids'][0]
        elif 'data' in response_data and 'id' in response_data['data']:
            user_id = response_data['data']['id']
        
        if user_id:
            logger.info(f"Usuario creado con ID: {user_id}")
        else:
            logger.error("No se encontró ID de usuario en la respuesta")
            logger.error(f"Respuesta completa: {response_data}")
            logger.error("DETENIENDO EL PROCESO PARA REVISAR EL CASO ESPECÍFICO")
            raise Exception("No se pudo obtener ID de usuario creado")
        
        return str(user_id) if user_id else None
        
    except Exception as e:
        logger.error(f"Error al crear usuario en ControlId: {e}")
        return None

def asignar_grupo_usuario(session: str, user_id: str, group_id: int = 1002) -> bool:
    """Asignar grupo a usuario en ControlId."""
    try:
        url = f"{CONTROL_ID_CONFIG['base_url']}/create_objects.fcgi"
        params = {'session': session}
        payload = {
            "object": "user_groups",
            "values": [
                {
                    "user_id": int(user_id),
                    "group_id": int(group_id)
                }
            ]
        }
        headers = {"Content-Type": "application/json"}
        
        response = requests.post(url, params=params, headers=headers, json=payload, timeout=PROCESO_CONFIG['timeout_requests'])
        
        # Algunos equipos devuelven 409/400 si ya existe; lo tratamos como éxito
        if response.status_code >= 200 and response.status_code < 300:
            return True
        
        try:
            data = response.json()
        except Exception:
            data = {"raw": response.text}
        
        # Si ya existe la relación, considerarlo éxito
        if response.status_code in (400, 409) and isinstance(data, dict) and (
            'exists' in str(data).lower() or 'duplicate' in str(data).lower()
        ):
            return True
        
        response.raise_for_status()
        return True
        
    except Exception as e:
        logger.error(f"Error al asignar grupo al usuario: {e}")
        return False

def buscar_imagen_local(documento: str) -> Optional[Path]:
    """Buscar imagen en la carpeta local."""
    try:
        carpeta_imagenes = Path(CARPETAS_CONFIG['carpeta_imagenes'])
        extension = CARPETAS_CONFIG['extension_imagen']
        
        # Buscar archivo con el número de documento
        posibles_nombres = [
            f"{documento}{extension}",
            f"{documento}.jpg",
            f"{documento}.jpeg",
            f"{documento}.png"
        ]
        
        for nombre in posibles_nombres:
            ruta_imagen = carpeta_imagenes / nombre
            if ruta_imagen.exists():
                return ruta_imagen
        
        return None
        
    except Exception as e:
        logger.error(f"Error al buscar imagen local: {e}")
        return None

def modificar_usuario_controlid(session: str, user_id: str, nombre: str, documento: str) -> bool:
    """Modificar usuario existente en ControlId."""
    try:
        url = f"{CONTROL_ID_CONFIG['base_url']}/create_or_modify_objects.fcgi"
        params = {'session': session}
        payload = {
            "object": "users",
            "values": [
                {
                    "id": int(user_id),
                    "name": nombre,
                    "registration": documento,
                    "password": "",
                    "salt": ""
                }
            ]
        }
        headers = {"Content-Type": "application/json"}
        
        response = requests.post(url, params=params, headers=headers, json=payload, timeout=PROCESO_CONFIG['timeout_requests'])
        response.raise_for_status()
        
        return True
        
    except Exception as e:
        logger.error(f"Error al modificar usuario en ControlId: {e}")
        return False

def asignar_imagen_usuario(session: str, user_id: str, ruta_imagen: Path) -> bool:
    """Asignar imagen a usuario en ControlId."""
    try:
        url = f"{CONTROL_ID_CONFIG['base_url']}/user_set_image.fcgi"
        params = {
            'user_id': user_id,
            'match': '1',
            'timestamp': str(int(ruta_imagen.stat().st_mtime)),
            'session': session
        }
        headers = {'Content-Type': 'application/octet-stream'}
        
        # Leer la imagen como datos binarios
        with open(ruta_imagen, 'rb') as image_file:
            image_data = image_file.read()
        
        response = requests.post(url, params=params, headers=headers, data=image_data, timeout=PROCESO_CONFIG['timeout_requests'])
        
        # Log detallado de la respuesta para debugging
        logger.info(f"Respuesta de asignación de imagen - Status: {response.status_code}")
        logger.info(f"Respuesta de asignación de imagen - Headers: {dict(response.headers)}")
        logger.info(f"Respuesta de asignación de imagen - Content: {response.text[:500]}...")
        
        # Si no es 200, detener el proceso para revisar
        if response.status_code != 200:
            logger.error(f"ERROR CRÍTICO: La asignación de imagen falló con status {response.status_code}")
            logger.error(f"Respuesta completa: {response.text}")
            logger.error("DETENIENDO EL PROCESO PARA REVISAR EL CASO ESPECÍFICO")
            raise Exception(f"Error en asignación de imagen: Status {response.status_code}")
        
        response.raise_for_status()
        
        # Verificar si la respuesta indica éxito real
        try:
            response_data = response.json()
            if 'success' in response_data and not response_data['success']:
                if 'errors' in response_data:
                    for error in response_data['errors']:
                        if error.get('code') == 3 and 'Face exists' in error.get('message', ''):
                            logger.warning(f"Cara ya existe - Usuario duplicado: {error.get('info', {}).get('match_user_id', 'desconocido')}")
                            return False
                        else:
                            logger.warning(f"Error en asignación de imagen: {error.get('message', 'Error desconocido')}")
                            return False
                else:
                    logger.warning("Asignación de imagen falló sin detalles específicos")
                    return False
        except Exception as e:
            logger.warning(f"Error al procesar respuesta de imagen: {e}")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"Error al asignar imagen: {e}")
        return False

# =============================================================================
# FUNCIÓN PRINCIPAL DE PROCESAMIENTO
# =============================================================================

def procesar_usuario_completo(session: str, conexion_miid: mysql.connector.connection.MySQLConnection, 
                            documento: str, indice: int, total: int) -> Dict[str, Any]:
    """Procesar un usuario completo: buscar en MiID, crear en ControlId, asignar imagen y grupo."""
    
    resultado = {
        'documento': documento,
        'indice': indice,
        'exito': False,
        'errores': [],
        'user_id': None,
        'imagen_asignada': False,
        'grupo_asignado': False,
        'actualizado': False
    }
    
    try:
        logger.info(f"[{indice}/{total}] Procesando documento: {documento}")
        
        # Paso 1: Buscar usuario en MiID
        usuario_miid = buscar_usuario_miid(conexion_miid, documento)
        if not usuario_miid:
            resultado['errores'].append("Usuario no encontrado en MiID")
            return resultado
        
        logger.info(f"[{indice}/{total}] Usuario encontrado en MiID: {usuario_miid['nombre']}")
        
        # Paso 2: Verificar si ya existe en ControlId
        usuario_controlid = buscar_usuario_controlid(session, documento)
        
        if usuario_controlid:
            logger.info(f"[{indice}/{total}] Usuario ya existe en ControlId: ID {usuario_controlid['id']}")
            user_id = str(usuario_controlid['id'])
            
            # Verificar si los datos son diferentes y necesitan actualización
            nombre_actual_controlid = usuario_controlid.get('name', '').strip()
            nombre_nuevo_miid = usuario_miid['nombre'].strip()
            
            if nombre_actual_controlid != nombre_nuevo_miid:
                logger.info(f"[{indice}/{total}] Datos diferentes detectados:")
                logger.info(f"[{indice}/{total}]   ControlId actual: '{nombre_actual_controlid}'")
                logger.info(f"[{indice}/{total}]   MiID nuevo: '{nombre_nuevo_miid}'")
                logger.info(f"[{indice}/{total}] Actualizando datos del usuario...")
                
                if modificar_usuario_controlid(session, user_id, nombre_nuevo_miid, documento):
                    logger.info(f"[{indice}/{total}] Usuario actualizado exitosamente")
                    resultado['actualizado'] = True
                else:
                    logger.warning(f"[{indice}/{total}] Error al actualizar usuario, pero continuando...")
                    resultado['errores'].append("Error al actualizar datos del usuario")
            else:
                logger.info(f"[{indice}/{total}] Datos del usuario ya están actualizados")
        else:
            # Paso 3: Crear usuario en ControlId
            logger.info(f"[{indice}/{total}] Creando usuario en ControlId...")
            user_id = crear_usuario_controlid(session, usuario_miid['nombre'], documento)
            
            if not user_id:
                resultado['errores'].append("Error al crear usuario en ControlId")
                return resultado
            
            logger.info(f"[{indice}/{total}] Usuario creado en ControlId: ID {user_id}")
        
        resultado['user_id'] = user_id
        
        # Paso 4: Buscar y asignar imagen
        ruta_imagen = buscar_imagen_local(documento)
        if ruta_imagen:
            logger.info(f"[{indice}/{total}] Imagen encontrada: {ruta_imagen.name}")
            
            imagen_resultado = asignar_imagen_usuario(session, user_id, ruta_imagen)
            if imagen_resultado:
                resultado['imagen_asignada'] = True
                logger.info(f"[{indice}/{total}] Imagen asignada exitosamente")
            else:
                resultado['imagen_asignada'] = False
                resultado['errores'].append("Imagen rechazada (cara duplicada o error)")
        else:
            logger.warning(f"[{indice}/{total}] No se encontró imagen para documento: {documento}")
            resultado['errores'].append("Imagen no encontrada")
        
        # Paso 5: Asignar grupo
        if asignar_grupo_usuario(session, user_id, PROCESO_CONFIG['grupo_usuario_id']):
            resultado['grupo_asignado'] = True
            logger.info(f"[{indice}/{total}] Grupo asignado exitosamente")
        else:
            resultado['errores'].append("Error al asignar grupo")
        
        # Si llegamos aquí sin errores críticos, consideramos éxito
        if not resultado['errores'] or len(resultado['errores']) <= 1:  # Permitir 1 error no crítico
            resultado['exito'] = True
        
        logger.info(f"[{indice}/{total}] Procesamiento completado: {'ÉXITO' if resultado['exito'] else 'CON ERRORES'}")
        
    except Exception as e:
        error_msg = f"Error inesperado: {str(e)}"
        logger.error(f"[{indice}/{total}] {error_msg}")
        resultado['errores'].append(error_msg)
    
    return resultado

# =============================================================================
# FUNCIÓN PRINCIPAL
# =============================================================================

def main():
    """Función principal del script de carga masiva."""
    
    logger.info("=" * 80)
    logger.info("INICIANDO PRUEBA DE CARGA MASIVA")
    logger.info("=" * 80)
    logger.info(f"Archivo Excel: {PROCESO_CONFIG['archivo_excel']}")
    logger.info(f"Carpeta de imágenes: {CARPETAS_CONFIG['carpeta_imagenes']}")
    logger.info(f"Grupo de usuario: {PROCESO_CONFIG['grupo_usuario_id']}")
    logger.info("=" * 80)
    
    # Verificar que el archivo Excel existe
    archivo_excel = Path(PROCESO_CONFIG['archivo_excel'])
    if not archivo_excel.exists():
        logger.error(f"Archivo Excel no encontrado: {archivo_excel}")
        return False
    
    # Cargar datos del Excel
    try:
        logger.info("Cargando datos del Excel...")
        df = pd.read_excel(archivo_excel)
        documentos = df[PROCESO_CONFIG['columna_documentos']].astype(str).tolist()
        total_documentos = len(documentos)
        logger.info(f"Total de documentos a procesar: {total_documentos}")
    except Exception as e:
        logger.error(f"Error al cargar Excel: {e}")
        return False
    
    # Conectar a las bases de datos
    logger.info("Estableciendo conexiones...")
    conexion_miid = conectar_miid()
    if not conexion_miid:
        logger.error("No se pudo conectar a MiID")
        return False
    
    session_controlid = obtener_sesion_controlid()
    if not session_controlid:
        logger.error("No se pudo obtener sesión de ControlId")
        conexion_miid.close()
        return False
    
    logger.info("Conexiones establecidas correctamente")
    
    # Inicializar monitor de tiempo
    monitor = MonitorTiempo(total_documentos)
    monitor.iniciar_proceso()
    
    # Estadísticas del proceso
    estadisticas = {
        'total_documentos_excel': total_documentos,
        'total_procesados': 0,
        'exitosos': 0,
        'con_errores': 0,
        'no_encontrados_miid': 0,
        'errores_creacion': 0,
        'imagenes_asignadas': 0,
        'imagenes_rechazadas_cara_duplicada': 0,
        'grupos_asignados': 0,
        'usuarios_actualizados': 0
    }
    
    # Lista para guardar resultados detallados
    resultados_detallados = []
    
    try:
        # Procesar cada documento
        for i, documento in enumerate(documentos, 1):
            logger.info(f"\n--- Procesando {i}/{total_documentos} ---")
            
            # Iniciar monitoreo del usuario
            monitor.iniciar_usuario(i, documento)
            
            # Procesar usuario
            try:
                resultado = procesar_usuario_completo(session_controlid, conexion_miid, documento, i, total_documentos)
                resultados_detallados.append(resultado)
            except Exception as e:
                logger.error(f"ERROR CRÍTICO en procesamiento de usuario {documento}: {e}")
                logger.error("DETENIENDO EL PROCESO COMPLETO")
                break
            
            # Finalizar monitoreo del usuario
            monitor.finalizar_usuario(resultado['exito'], resultado.get('actualizado', False))
            
            # Actualizar estadísticas
            if resultado['exito']:
                estadisticas['exitosos'] += 1
            else:
                estadisticas['con_errores'] += 1
                
                if "Usuario no encontrado en MiID" in resultado['errores']:
                    estadisticas['no_encontrados_miid'] += 1
                if "Error al crear usuario en ControlId" in resultado['errores']:
                    estadisticas['errores_creacion'] += 1
            
            if resultado['imagen_asignada']:
                estadisticas['imagenes_asignadas'] += 1
            elif resultado.get('errores') and any('cara duplicada' in error for error in resultado['errores']):
                estadisticas['imagenes_rechazadas_cara_duplicada'] += 1
            if resultado['grupo_asignado']:
                estadisticas['grupos_asignados'] += 1
            if resultado.get('actualizado', False):
                estadisticas['usuarios_actualizados'] += 1
            
            # Mostrar progreso cada 50 usuarios
            if i % 50 == 0:
                logger.info(f"\n--- PROGRESO: {i}/{total_documentos} ---")
                logger.info(f"Exitosos: {estadisticas['exitosos']}")
                logger.info(f"Con errores: {estadisticas['con_errores']}")
                logger.info(f"Imágenes asignadas: {estadisticas['imagenes_asignadas']}")
                logger.info(f"Imágenes rechazadas (cara duplicada): {estadisticas['imagenes_rechazadas_cara_duplicada']}")
                logger.info(f"Grupos asignados: {estadisticas['grupos_asignados']}")
            
            # Delay entre usuarios
            if i < total_documentos:
                time.sleep(PROCESO_CONFIG['delay_entre_usuarios'])
    
    except KeyboardInterrupt:
        logger.warning("Proceso interrumpido por el usuario")
    except Exception as e:
        logger.error(f"Error inesperado en el proceso principal: {e}")
    finally:
        # Cerrar conexiones
        try:
            conexion_miid.close()
            logger.info("Conexión a MiID cerrada")
        except:
            pass
    
    # Finalizar monitor de tiempo
    monitor.finalizar_proceso()
    
    # Obtener estadísticas de tiempo
    stats_tiempo = monitor.obtener_estadisticas_finales()
    
    # Mostrar estadísticas finales
    logger.info("\n" + "=" * 80)
    logger.info("ESTADÍSTICAS FINALES")
    logger.info("=" * 80)
    
    # Estadísticas de tiempo
    if stats_tiempo:
        logger.info("TIEMPO Y RENDIMIENTO")
        logger.info("-" * 40)
        logger.info(f"Tiempo total: {stats_tiempo['tiempo_total_formateado']}")
        logger.info(f"Tiempo promedio por usuario: {stats_tiempo['tiempo_promedio_por_usuario']:.2f}s")
        logger.info(f"Tiempo minimo usuario: {stats_tiempo['tiempo_minimo_usuario']:.2f}s")
        logger.info(f"Tiempo maximo usuario: {stats_tiempo['tiempo_maximo_usuario']:.2f}s")
        logger.info(f"Velocidad: {stats_tiempo['velocidad_usuarios_por_minuto']:.1f} usuarios/min")
        logger.info(f"CPU promedio: {stats_tiempo['cpu_uso_promedio']:.1f}%")
        logger.info(f"Memoria usada: {stats_tiempo['memoria_uso_mb']:.1f} MB / {stats_tiempo['memoria_total_mb']:.1f} MB")
        logger.info("")
    
    # Estadísticas de procesamiento
    logger.info("PROCESAMIENTO")
    logger.info("-" * 40)
    logger.info(f"Total procesados: {estadisticas['total_procesados']}")
    logger.info(f"Exitosos: {estadisticas['exitosos']} ({estadisticas['exitosos']/estadisticas['total_procesados']*100:.1f}%)")
    logger.info(f"Con errores: {estadisticas['con_errores']} ({estadisticas['con_errores']/estadisticas['total_procesados']*100:.1f}%)")
    logger.info(f"No encontrados en MiID: {estadisticas['no_encontrados_miid']}")
    logger.info(f"Errores de creación: {estadisticas['errores_creacion']}")
    logger.info(f"Imágenes asignadas: {estadisticas['imagenes_asignadas']}")
    logger.info(f"Imágenes rechazadas (cara duplicada): {estadisticas['imagenes_rechazadas_cara_duplicada']}")
    logger.info(f"Grupos asignados: {estadisticas['grupos_asignados']}")
    logger.info(f"Usuarios actualizados: {estadisticas['usuarios_actualizados']}")
    logger.info("=" * 80)
    
    # Guardar resultados detallados en JSON
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archivo_resultados = f"resultados_carga_masiva_{timestamp}.json"
        
        with open(archivo_resultados, 'w', encoding='utf-8') as f:
            json.dump({
                'estadisticas': estadisticas,
                'estadisticas_tiempo': stats_tiempo,
                'resultados_detallados': resultados_detallados,
                'configuracion': {
                    'archivo_excel': str(archivo_excel),
                    'carpeta_imagenes': CARPETAS_CONFIG['carpeta_imagenes'],
                    'grupo_usuario_id': PROCESO_CONFIG['grupo_usuario_id']
                }
            }, f, indent=2, default=str, ensure_ascii=False)
        
        logger.info(f"Resultados detallados guardados en: {archivo_resultados}")
    except Exception as e:
        logger.error(f"Error al guardar resultados: {e}")
    
    return estadisticas['exitosos'] > 0

if __name__ == "__main__":
    logger.info("Script de carga masiva iniciado")
    logger.info("IMPORTANTE: Revisar y modificar las credenciales hardcodeadas antes de ejecutar")
    
    # Preguntar confirmación antes de ejecutar
    respuesta = input("\n¿Desea continuar con la carga masiva? (sí/no): ").lower().strip()
    if respuesta in ['sí', 'si', 'yes', 'y', 's']:
        success = main()
        if success:
            print("\n[ÉXITO] Proceso de carga masiva completado")
        else:
            print("\n[ERROR] El proceso de carga masiva falló")
    else:
        print("Proceso cancelado por el usuario")
