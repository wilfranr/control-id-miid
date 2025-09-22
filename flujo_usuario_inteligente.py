#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script que implementa el flujo inteligente de usuarios:
1. Buscar usuario por registration (número de documento)
2. Si existe: modificar usuario existente
3. Si no existe: crear nuevo usuario
"""

import requests
import time
import json
import logging
import configparser
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from GetUserMiID import obtener_ultimo_usuario_midd

# --- Nuevo sistema de configuración --- #

_config = None
_active_env_config = None

def _get_base_path() -> str:
    """Obtiene la ruta base, ya sea para un script o un ejecutable de PyInstaller."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.realpath(__file__))

def load_config() -> Tuple[configparser.ConfigParser, Dict[str, Any]]:
    """Carga config.ini y devuelve el parser y la configuración del entorno activo."""
    global _config, _active_env_config
    if _config and _active_env_config:
        return _config, _active_env_config

    base_path = _get_base_path()
    config_path = os.path.join(base_path, 'config.ini')
    
    config = configparser.ConfigParser()
    config.read(config_path, encoding='utf-8')
    
    active_env_name = config.get('Service', 'ActiveEnv', fallback='PROD').upper()
    
    if active_env_name not in config:
        raise ValueError(f"La sección del entorno '[{active_env_name}]' no se encuentra en config.ini")

    env_config = {}
    for key, value in config.items(active_env_name):
        # Convertir claves como 'miid.host' en un diccionario anidado
        parts = key.split('.', 1)
        if len(parts) == 2:
            section, option = parts
            if section not in env_config:
                env_config[section] = {}
            env_config[section][option] = value
        else:
            env_config[key] = value
    
    _config = config
    _active_env_config = env_config
    return _config, _active_env_config

# Inicializar la configuración al importar el módulo
# load_config() -> Se llamará explícitamente desde el servicio

# --- Fin del nuevo sistema de configuración ---

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def _get_control_id_config() -> Dict[str, Any]:
    """Devuelve la configuración de ControlId del entorno activo."""
    _, env_config = load_config()
    config = env_config.get('control_id', {})
    # Asegurar valores por defecto
    config.setdefault('base_url', '')
    config.setdefault('login', '')
    config.setdefault('password', '')
    config.setdefault('default_group_id', 2)
    return config


def buscar_usuario_por_registration(session: str, registration: str) -> Optional[Dict[str, Any]]:
    """
    Busca un usuario por su número de documento (registration).
    
    Args:
        session: Token de sesión
        registration: Número de documento a buscar
        
    Returns:
        Diccionario con datos del usuario si existe, None si no existe
    """
    try:
        logger.info(f"Buscando usuario con documento: {registration}")
        
        cfg = _get_control_id_config()
        url = f"{cfg['base_url']}/load_objects.fcgi"
        params = {'session': session}
        payload = {
            "object": "users"
        }
        headers = {"Content-Type": "application/json"}
        
        logger.info(f"[ControlId] load_objects -> base_url={cfg['base_url']}")
        response = requests.post(url, params=params, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        
        # Parsear respuesta
        response_data = response.json()
        logger.info(f"Respuesta de búsqueda: {response_data}")
        
        # Buscar usuario por registration
        if 'users' in response_data and isinstance(response_data['users'], list):
            for usuario in response_data['users']:
                if usuario.get('registration') == registration:
                    logger.info(f"Usuario encontrado: ID={usuario.get('id')}, Nombre={usuario.get('name')}")
                    return usuario
        elif 'data' in response_data and isinstance(response_data['data'], list):
            for usuario in response_data['data']:
                if usuario.get('registration') == registration:
                    logger.info(f"Usuario encontrado: ID={usuario.get('id')}, Nombre={usuario.get('name')}")
                    return usuario
        
        logger.info("Usuario no encontrado")
        return None
        
    except requests.RequestException as e:
        logger.error(f"Error al buscar usuario: {e}")
        return None
    except Exception as e:
        logger.error(f"Error inesperado al buscar usuario: {e}")
        return None

def crear_usuario_nuevo(session: str, nombre: str, documento: str) -> Optional[str]:
    """
    Crea un nuevo usuario en ControlId.
    
    Args:
        session: Token de sesión
        nombre: Nombre del usuario
        documento: Número de documento
        
    Returns:
        ID del usuario creado o None si falla
    """
    try:
        logger.info(f"Creando nuevo usuario: {nombre} ({documento})")
        
        cfg = _get_control_id_config()
        url = f"{cfg['base_url']}/create_objects.fcgi"
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
        
        logger.info(f"[ControlId] create_objects -> base_url={cfg['base_url']}")
        response = requests.post(url, params=params, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        
        response_data = response.json()
        logger.info(f"Respuesta de creación: {response_data}")
        
        # Extraer ID del usuario creado
        user_id = None
        if 'id' in response_data:
            user_id = response_data['id']
        elif 'ids' in response_data and isinstance(response_data['ids'], list) and len(response_data['ids']) > 0:
            user_id = response_data['ids'][0]
        elif 'data' in response_data and 'id' in response_data['data']:
            user_id = response_data['data']['id']
        
        if user_id:
            logger.info(f"Usuario creado exitosamente con ID: {user_id}")
            return str(user_id)
        else:
            logger.error(f"No se encontró ID en la respuesta: {response_data}")
            return None
            
    except requests.RequestException as e:
        logger.error(f"Error al crear usuario: {e}")
        return None

def crear_grupo_para_usuario(session: str, user_id: str, group_id: int = 2) -> bool:
    """
    Crea la relación user_groups para asignar un grupo fijo al usuario.

    Args:
        session: Token de sesión
        user_id: ID del usuario
        group_id: ID del grupo (Definido desde el config)

    Returns:
        True si se creó correctamente o ya existía; False si falla.
    """
    try:
        # Verificar si ya existe la relación
        try:
            cfg = _get_control_id_config()
            url_check = f"{cfg['base_url']}/load_objects.fcgi"
            params_check = {'session': session}
            payload_check = {"object": "user_groups"}
            headers_check = {"Content-Type": "application/json"}
            resp_check = requests.post(
                url_check, params=params_check, headers=headers_check, json=payload_check, timeout=30
            )
            resp_check.raise_for_status()
            data_check = resp_check.json()
            lista = []
            if isinstance(data_check, dict):
                if 'user_groups' in data_check and isinstance(data_check['user_groups'], list):
                    lista = data_check['user_groups']
                elif 'data' in data_check and isinstance(data_check['data'], list):
                    lista = data_check['data']
            for item in lista:
                if int(item.get('user_id', -1)) == int(user_id) and int(item.get('group_id', -1)) == int(group_id):
                    logger.info("Relación user_groups ya existe; no se crea nuevamente")
                    return True
        except Exception as _e:
            # Si falla la verificación, continuamos con creación tentativa
            logger.warning(f"No se pudo verificar existencia de user_groups, se intentará crear: {_e}")

        logger.info(f"Asignando grupo {group_id} al usuario ID {user_id}")

        url = f"{cfg['base_url']}/create_objects.fcgi"
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

        logger.info(f"[ControlId] user_groups.create -> base_url={cfg['base_url']}")
        response = requests.post(url, params=params, headers=headers, json=payload, timeout=30)
        # Algunos equipos devuelven 409/400 si ya existe; lo tratamos como éxito idempotente
        if response.status_code >= 200 and response.status_code < 300:
            logger.info("Grupo asignado correctamente")
            return True

        try:
            data = response.json()
        except Exception:
            data = {"raw": response.text}

        # Si ya existe la relación, considerarlo éxito idempotente
        if response.status_code in (400, 409) and isinstance(data, dict) and (
            'exists' in str(data).lower() or 'duplicate' in str(data).lower()
        ):
            logger.info("Relación user_groups ya existía; continuando")
            return True

        response.raise_for_status()
        logger.info("Grupo asignado correctamente")
        return True

    except requests.RequestException as e:
        logger.error(f"Error al asignar grupo al usuario: {e}")
        return False
    except Exception as e:
        logger.error(f"Error inesperado al asignar grupo: {e}")
        return False
    except Exception as e:
        logger.error(f"Error inesperado al crear usuario: {e}")
        return None

def modificar_usuario_existente(session: str, user_id: str, nombre: str, documento: str) -> bool:
    """
    Modifica un usuario existente en ControlId.
    
    Args:
        session: Token de sesión
        user_id: ID del usuario a modificar
        nombre: Nuevo nombre del usuario
        documento: Número de documento
        
    Returns:
        True si se modificó correctamente, False si falla
    """
    try:
        logger.info(f"Modificando usuario ID {user_id}: {nombre} ({documento})")
        
        cfg = _get_control_id_config()
        url = f"{cfg['base_url']}/create_or_modify_objects.fcgi"
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
        
        logger.info(f"[ControlId] create_or_modify -> base_url={cfg['base_url']}")
        response = requests.post(url, params=params, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        
        response_data = response.json()
        logger.info(f"Respuesta de modificación: {response_data}")
        
        logger.info("Usuario modificado exitosamente")
        return True
        
    except requests.RequestException as e:
        logger.error(f"Error al modificar usuario: {e}")
        return False
    except Exception as e:
        logger.error(f"Error inesperado al modificar usuario: {e}")
        return False

def asignar_imagen_usuario(session: str, user_id: str, ruta_imagen: str) -> bool:
    """
    Asigna una imagen a un usuario en ControlId usando el endpoint correcto.
    
    Args:
        session: Token de sesión
        user_id: ID del usuario
        ruta_imagen: Ruta de la imagen a asignar
        
    Returns:
        True si se asignó correctamente, False si falla.
    """
    try:
        logger.info(f"Asignando imagen al usuario ID: {user_id}")
        
        # Usar el endpoint correcto según la documentación
        cfg = _get_control_id_config()
        url = f"{cfg['base_url']}/user_set_image.fcgi"
        
        # Generar timestamp actual
        timestamp = str(int(time.time()))
        
        params = {
            'session': session,
            'user_id': user_id,
            'timestamp': timestamp
        }
        headers = {'Content-Type': 'application/octet-stream'}
        
        # Leer la imagen como datos binarios
        with open(ruta_imagen, 'rb') as image_file:
            image_data = image_file.read()
        
        logger.info(f"Enviando imagen {Path(ruta_imagen).name} para usuario ID {user_id}")
        logger.info(f"Tamaño de imagen: {len(image_data)} bytes")
        logger.info(f"Timestamp: {timestamp}")
        
        logger.info(f"[ControlId] user_set_image -> base_url={cfg['base_url']}")
        response = requests.post(url, params=params, headers=headers, data=image_data, timeout=30)
        
        # Log de la respuesta para debugging
        logger.info(f"Respuesta de asignación de imagen - Status: {response.status_code}")
        
        # El endpoint no devuelve cuerpo de respuesta según la documentación
        if response.status_code == 200:
            logger.info("Imagen asignada exitosamente (sin respuesta del servidor)")
            return True
        else:
            logger.error(f"Error en asignación de imagen - Status: {response.status_code}")
            if response.text:
                logger.error(f"Respuesta del servidor: {response.text}")
            return False
        
    except requests.RequestException as e:
        logger.error(f"Error al asignar imagen: {e}")
        return False
    except Exception as e:
        logger.error(f"Error inesperado al asignar imagen: {e}")
        return False

def procesar_usuario_inteligente(session: str, nombre: str, documento: str) -> Optional[str]:
    """
    Procesa un usuario de manera inteligente: busca si existe, si no existe lo crea,
    si existe lo modifica.
    
    Args:
        session: Token de sesión
        nombre: Nombre del usuario
        documento: Número de documento
        
    Returns:
        ID del usuario (creado o modificado) o None si falla
    """
    try:
        # Validar parámetros de entrada
        if not nombre or not nombre.strip():
            logger.error(f"Nombre de usuario inválido o vacío: '{nombre}'")
            return None
        
        if not documento or not documento.strip():
            logger.error(f"Documento de usuario inválido o vacío: '{documento}'")
            return None
        
        logger.info(f"Procesando usuario: '{nombre}' ({documento})")
        
        # Paso 1: Buscar usuario existente
        usuario_existente = buscar_usuario_por_registration(session, documento)
        
        if usuario_existente:
            # Usuario existe: modificar
            logger.info("Usuario existe, procediendo a modificar...")
            user_id = usuario_existente.get('id')
            if modificar_usuario_existente(session, str(user_id), nombre, documento):
                logger.info(f"Usuario modificado exitosamente. ID: {user_id}")
                # Asegurar asignación de grupo por defecto
                cfg_ci = _get_control_id_config()
                _gid = int((cfg_ci or {}).get('default_group_id', 2))
                if not crear_grupo_para_usuario(session, str(user_id), _gid):
                    logger.warning("No se pudo asignar el grupo al usuario modificado")
                return str(user_id)
            else:
                logger.error("Error al modificar usuario existente")
                return None
        else:
            # Usuario no existe: crear
            logger.info("Usuario no existe, procediendo a crear...")
            user_id = crear_usuario_nuevo(session, nombre, documento)
            if user_id:
                logger.info(f"Usuario creado exitosamente. ID: {user_id}")
                # Asignar grupo por defecto al usuario recién creado
                cfg_ci = _get_control_id_config()
                _gid = int((cfg_ci or {}).get('default_group_id', 2))
                if not crear_grupo_para_usuario(session, user_id, _gid):
                    logger.warning("No se pudo asignar el grupo al nuevo usuario")
                return user_id
            else:
                logger.error("Error al crear nuevo usuario")
                return None
                
    except Exception as e:
        logger.error(f"Error en el procesamiento inteligente: {e}")
        return None

def procesar_usuario_con_imagen(session: str, nombre: str, documento: str, ruta_imagen: str) -> Optional[str]:
    """
    Procesa un usuario de manera inteligente y le asigna una imagen.
    
    Args:
        session: Token de sesión
        nombre: Nombre del usuario
        documento: Número de documento
        ruta_imagen: Ruta de la imagen a asignar
        
    Returns:
        ID del usuario (creado o modificado) o None si falla
    """
    try:
        logger.info(f"Procesando usuario con imagen: {nombre} ({documento})")
        
        # Paso 1: Procesar usuario (crear o modificar)
        user_id = procesar_usuario_inteligente(session, nombre, documento)
        
        if not user_id:
            logger.error("Error al procesar usuario")
            return None
        
        # Paso 2: Asignar imagen
        if asignar_imagen_usuario(session, user_id, ruta_imagen):
            logger.info(f"Usuario procesado y imagen asignada exitosamente. ID: {user_id}")
            return user_id
        else:
            logger.error("Error al asignar imagen al usuario")
            return None
            
    except Exception as e:
        logger.error(f"Error en el procesamiento con imagen: {e}")
        return None

def obtener_sesion():
    """
    Obtiene una sesión válida de ControlId.
    """
    try:
        logger.info("Obteniendo sesión de ControlId...")
        
        cfg = _get_control_id_config()
        url = f"{cfg['base_url']}/login.fcgi"
        payload = {
            "login": cfg['login'],
            "password": cfg['password']
        }
        headers = {"Content-Type": "application/json"}
        
        logger.info(f"[ControlId] login -> base_url={cfg['base_url']} user={cfg['login']}")
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        
        response_data = response.json()
        if 'session' in response_data:
            session = response_data['session']
            logger.info(f"Sesión obtenida exitosamente: {session}")
            return session
        else:
            logger.error("No se encontró sesión en la respuesta del login")
            return None
            
    except Exception as e:
        logger.error(f"Error al obtener sesión: {e}")
        return None

def main():
    """
    Función principal que ejecuta el flujo inteligente.
    """
    logger.info("=== INICIANDO FLUJO INTELIGENTE DE USUARIOS ===")
    
    try:
        # Obtener sesión
        session = obtener_sesion()
        if not session:
            logger.error("No se pudo obtener sesión. Abortando proceso.")
            return False
        
        # Obtener usuario de MiID
        logger.info("Obteniendo usuario de MiID...")
        usuario_miid = obtener_ultimo_usuario_midd()
        
        if not usuario_miid:
            logger.error("No se pudo obtener usuario de MiID")
            return False
        
        logger.info(f"Usuario obtenido: {usuario_miid['nombre']} - {usuario_miid['documento']}")
        
        # Procesar usuario de manera inteligente
        user_id = procesar_usuario_inteligente(
            session, 
            usuario_miid['nombre'], 
            usuario_miid['documento']
        )
        
        if user_id:
            logger.info(f"=== PROCESO COMPLETADO EXITOSAMENTE ===")
            logger.info(f"Usuario procesado: {usuario_miid['nombre']} (ID: {user_id})")
            return True
        else:
            logger.error("Error en el procesamiento del usuario")
            return False
            
    except Exception as e:
        logger.error(f"Error en el proceso principal: {e}")
        return False

if __name__ == "__main__":
    # Este bloque solo se ejecuta cuando el script es el punto de entrada principal
    success = main()
    if success:
        print("\n[EXITO] Proceso completado exitosamente")
    else:
        print("\n[ERROR] El proceso falló. Revisa los logs para más detalles.")
