#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de prueba con pocos usuarios para validar el proceso antes de la carga masiva.
Procesa solo los primeros 5 usuarios del Excel para verificar que todo funciona correctamente.
"""

import pandas as pd
import mysql.connector
import pyodbc
import requests
import json
import logging
import time
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_pequeno.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

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
    "servidor": "servidor.database.windows.net",
    "base_datos": "ByKeeper_Desarrollo",
    "usuario": "usuario_azure",
    "contraseña": "contraseña_azure",
    "stored_procedure": "dbo.GetMatchIDImgFaceByCASBid",
    "business_context": "Bytte"
}

# Configuración ControlId
CONTROL_ID_CONFIG = {
    "base_url": "http://192.168.3.37",
    "login": "admin",
    "password": "admin"
}

# Configuración de carpetas
CARPETAS_CONFIG = {
    "carpeta_imagenes": r"C:\Users\wilfran.rivera\Downloads\Imagenes Facial MiID",
    "carpeta_local_temp": r"C:\temp\Imagenes_Pro",
    "extension_imagen": ".jpg"
}

# Configuración del proceso (solo 5 usuarios para prueba)
PROCESO_CONFIG = {
    "archivo_excel": "tests/clientes.xlsx",
    "columna_documentos": "Clientes",
    "grupo_usuario_id": 1002,
    "delay_entre_usuarios": 1.0,  # 1 segundo entre usuarios para prueba
    "max_reintentos": 3,
    "timeout_requests": 30,
    "max_usuarios_prueba": 5  # Solo procesar 5 usuarios
}

# =============================================================================
# FUNCIONES DE CONEXIÓN (iguales que el script principal)
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
# FUNCIONES DE BÚSQUEDA Y PROCESAMIENTO (iguales que el script principal)
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
        
        # Log detallado de la respuesta
        logger.info(f"Respuesta de creación de usuario - Status: {response.status_code}")
        logger.info(f"Respuesta de creación de usuario - Headers: {dict(response.headers)}")
        logger.info(f"Respuesta de creación de usuario - Content: {response.text}")
        
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
        
        # Log de la respuesta para debugging
        logger.info(f"Respuesta de asignación de imagen - Status: {response.status_code}")
        logger.info(f"Respuesta de asignación de imagen - Headers: {dict(response.headers)}")
        logger.info(f"Respuesta de asignación de imagen - Content: {response.text[:500]}...")
        
        response.raise_for_status()
        
        return True
        
    except Exception as e:
        logger.error(f"Error al asignar imagen: {e}")
        return False

# =============================================================================
# FUNCIÓN PRINCIPAL DE PRUEBA
# =============================================================================

def main():
    """Función principal del script de prueba."""
    
    logger.info("=" * 80)
    logger.info("INICIANDO PRUEBA CON POCOS USUARIOS")
    logger.info("=" * 80)
    logger.info(f"Archivo Excel: {PROCESO_CONFIG['archivo_excel']}")
    logger.info(f"Carpeta de imágenes: {CARPETAS_CONFIG['carpeta_imagenes']}")
    logger.info(f"Grupo de usuario: {PROCESO_CONFIG['grupo_usuario_id']}")
    logger.info(f"Máximo usuarios a procesar: {PROCESO_CONFIG['max_usuarios_prueba']}")
    logger.info("=" * 80)
    
    # Verificar que el archivo Excel existe
    archivo_excel = Path(PROCESO_CONFIG['archivo_excel'])
    if not archivo_excel.exists():
        logger.error(f"Archivo Excel no encontrado: {archivo_excel}")
        return False
    
    # Cargar datos del Excel (solo los primeros usuarios)
    try:
        logger.info("Cargando datos del Excel...")
        df = pd.read_excel(archivo_excel)
        documentos = df[PROCESO_CONFIG['columna_documentos']].astype(str).tolist()
        # Tomar solo los primeros usuarios para la prueba
        documentos = documentos[:PROCESO_CONFIG['max_usuarios_prueba']]
        total_documentos = len(documentos)
        logger.info(f"Documentos a procesar en esta prueba: {total_documentos}")
        logger.info(f"Documentos: {documentos}")
    except Exception as e:
        logger.error(f"Error al cargar Excel: {e}")
        return False
    
    # Verificar carpeta de imágenes
    carpeta_imagenes = Path(CARPETAS_CONFIG['carpeta_imagenes'])
    if not carpeta_imagenes.exists():
        logger.error(f"Carpeta de imágenes no encontrada: {carpeta_imagenes}")
        return False
    
    logger.info(f"Carpeta de imágenes encontrada: {carpeta_imagenes}")
    
    # Listar algunas imágenes disponibles para verificar
    try:
        imagenes_disponibles = list(carpeta_imagenes.glob("*.jpg"))[:10]  # Primeras 10 imágenes
        logger.info(f"Ejemplos de imágenes disponibles: {[img.name for img in imagenes_disponibles]}")
    except Exception as e:
        logger.warning(f"No se pudieron listar imágenes: {e}")
    
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
    
    # Estadísticas del proceso
    estadisticas = {
        'total': total_documentos,
        'exitosos': 0,
        'con_errores': 0,
        'no_encontrados_miid': 0,
        'errores_creacion': 0,
        'imagenes_asignadas': 0,
        'grupos_asignados': 0,
        'usuarios_actualizados': 0
    }
    
    # Lista para guardar resultados detallados
    resultados_detallados = []
    
    try:
        # Procesar cada documento
        for i, documento in enumerate(documentos, 1):
            logger.info(f"\n--- Procesando {i}/{total_documentos} ---")
            
            # Procesar usuario (usando la misma función del script principal)
            resultado = procesar_usuario_completo(session_controlid, conexion_miid, documento, i, total_documentos)
            resultados_detallados.append(resultado)
            
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
            if resultado['grupo_asignado']:
                estadisticas['grupos_asignados'] += 1
            if resultado.get('actualizado', False):
                estadisticas['usuarios_actualizados'] += 1
            
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
    
    # Mostrar estadísticas finales
    logger.info("\n" + "=" * 80)
    logger.info("ESTADÍSTICAS DE LA PRUEBA")
    logger.info("=" * 80)
    logger.info(f"Total procesados: {estadisticas['total']}")
    logger.info(f"Exitosos: {estadisticas['exitosos']} ({estadisticas['exitosos']/estadisticas['total']*100:.1f}%)")
    logger.info(f"Con errores: {estadisticas['con_errores']} ({estadisticas['con_errores']/estadisticas['total']*100:.1f}%)")
    logger.info(f"No encontrados en MiID: {estadisticas['no_encontrados_miid']}")
    logger.info(f"Errores de creación: {estadisticas['errores_creacion']}")
    logger.info(f"Imágenes asignadas: {estadisticas['imagenes_asignadas']}")
    logger.info(f"Grupos asignados: {estadisticas['grupos_asignados']}")
    logger.info(f"Usuarios actualizados: {estadisticas['usuarios_actualizados']}")
    logger.info("=" * 80)
    
    # Mostrar resultados detallados
    logger.info("\nRESULTADOS DETALLADOS:")
    for resultado in resultados_detallados:
        status = "✅ ÉXITO" if resultado['exito'] else "❌ ERROR"
        actualizado = " (ACTUALIZADO)" if resultado.get('actualizado', False) else ""
        logger.info(f"  {resultado['documento']}: {status}{actualizado}")
        if resultado['errores']:
            for error in resultado['errores']:
                logger.info(f"    - {error}")
    
    # Guardar resultados detallados en JSON
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archivo_resultados = f"resultados_prueba_{timestamp}.json"
        
        with open(archivo_resultados, 'w', encoding='utf-8') as f:
            json.dump({
                'estadisticas': estadisticas,
                'resultados_detallados': resultados_detallados,
                'configuracion': {
                    'archivo_excel': str(archivo_excel),
                    'carpeta_imagenes': CARPETAS_CONFIG['carpeta_imagenes'],
                    'grupo_usuario_id': PROCESO_CONFIG['grupo_usuario_id'],
                    'max_usuarios_prueba': PROCESO_CONFIG['max_usuarios_prueba']
                }
            }, f, indent=2, default=str, ensure_ascii=False)
        
        logger.info(f"Resultados detallados guardados en: {archivo_resultados}")
    except Exception as e:
        logger.error(f"Error al guardar resultados: {e}")
    
    return estadisticas['exitosos'] > 0

# Función para procesar usuario (copiada del script principal)
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
            
            if asignar_imagen_usuario(session, user_id, ruta_imagen):
                resultado['imagen_asignada'] = True
                logger.info(f"[{indice}/{total}] Imagen asignada exitosamente")
            else:
                resultado['errores'].append("Error al asignar imagen")
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

if __name__ == "__main__":
    logger.info("Script de prueba iniciado")
    logger.info("IMPORTANTE: Revisar y modificar las credenciales hardcodeadas antes de ejecutar")
    
    # Preguntar confirmación antes de ejecutar
    respuesta = input("\n¿Desea continuar con la prueba con pocos usuarios? (sí/no): ").lower().strip()
    if respuesta in ['sí', 'si', 'yes', 'y', 's']:
        success = main()
        if success:
            print("\n[ÉXITO] Prueba completada exitosamente")
            print("Si la prueba fue exitosa, puedes proceder con la carga masiva completa")
        else:
            print("\n[ERROR] La prueba falló. Revisar logs y configuración")
    else:
        print("Prueba cancelada por el usuario")
