#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para buscar un usuario específico por número de documento en MiID.
"""

import mysql.connector
import logging
import json
import os
from pathlib import Path
from config import AZURE_CONFIG, MIID_CONFIG as _CFG_MIID
try:
    from env_config import ENVIRONMENTS as _ENVIRONMENTS, ACTIVE_ENV as _ACTIVE_ENV
except Exception:
    _ENVIRONMENTS, _ACTIVE_ENV = {}, None
def _resolve_miid_config():
    try:
        env_name = str((os.environ.get('ACTIVE_ENV') or _ACTIVE_ENV or 'DEV')).upper()
        try:
            import importlib as _importlib
            _env = _importlib.import_module('env_config')
            envs_live = dict(getattr(_env, 'ENVIRONMENTS', {}) or {})
        except Exception:
            envs_live = dict(_ENVIRONMENTS or {})
        mi = dict(((envs_live.get(env_name) or {}).get('miid')) or {})
        if mi:
            return mi
    except Exception:
        pass
    try:
        return dict(_CFG_MIID)
    except Exception:
        return {}

def _resolve_miid_ec_id(default_value: int = 11000) -> int:
    try:
        env_name = str((os.environ.get('ACTIVE_ENV') or _ACTIVE_ENV or 'DEV')).upper()
        try:
            import importlib as _importlib
            _env = _importlib.import_module('env_config')
            envs_live = dict(getattr(_env, 'ENVIRONMENTS', {}) or {})
        except Exception:
            envs_live = dict(_ENVIRONMENTS or {})
        val = (( envs_live.get(env_name) or {}).get('miid') or {}).get('ec_id')
        if val is not None:
            return int(val)
    except Exception:
        pass
    try:
        from config import MIID_EC_ID as _MIID_EC_ID
        return int(_MIID_EC_ID)
    except Exception:
        pass
    try:
        return int(os.environ.get('MIID_EC_ID', str(default_value)))
    except Exception:
        return default_value

MIID_CONFIG = _resolve_miid_config()
MIID_EC_ID = _resolve_miid_ec_id()

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def conectar_miid():
    """
    Abre conexión a MiID (Los datos de conexión los traigo desde config.py)
    """
    try:
        cfg = _resolve_miid_config()
        host = cfg.get('host') if isinstance(cfg, dict) else None
        user = cfg.get('user') if isinstance(cfg, dict) else None
        database = cfg.get('database') if isinstance(cfg, dict) else None
        logger.info(f"Conectando a MiID -> host={host}, user={user}, database={database}")

        # Filtrar solo parámetros válidos para la conexión MySQL
        allowed_keys = {"host", "port", "user", "password", "database"}
        conn_args = {k: v for k, v in (cfg or {}).items() if k in allowed_keys}
        try:
            if "port" in conn_args and isinstance(conn_args["port"], str) and conn_args["port"].isdigit():
                conn_args["port"] = int(conn_args["port"])
        except Exception:
            pass
        
        # Agregar parámetros para manejar problemas de autenticación
        conn_args.update({
            'auth_plugin': 'mysql_native_password',
            'autocommit': True,
            'use_unicode': True,
            'charset': 'utf8mb4'
        })
        
        conexion = mysql.connector.connect(**conn_args)
        try:
            cur = conexion.cursor()
            cur.execute("SELECT @@hostname, @@port, DATABASE()")
            row = cur.fetchone()
            if row:
                logger.info(f"MiID conectado a host={row[0]} port={row[1]} db={row[2]}")
            cur.close()
        except Exception as _einfo:
            logger.debug(f"No se pudo obtener info de servidor MySQL: {_einfo}")
        logger.info("Conexión a MiID establecida exitosamente")
        return conexion

    except Exception as e:
        logger.error(f"Error al conectarse a la base de datos: {e}")
        return None

def buscar_usuario_por_documento(numero_documento: str):
    """
    Busca un usuario específico por número de documento en MiID.
    
    Args:
        numero_documento: Número de documento a buscar
        
    Returns:
        Diccionario con datos del usuario si existe, None si no existe
    """
    conexion = None
    try:
        conexion = conectar_miid()
        if not conexion:
            return None

        cursor = conexion.cursor()

        # Query para buscar usuario por número de documento usando solo las columnas que existen
        query = """
        SELECT
            lpe.LP_ID,
            p.PER_DOCUMENT_NUMBER,
            p.PER_ANI_FIRST_NAME,
            p.PER_FIRST_NAME,
            p.PER_LAST_NAME,
            COALESCE(
                NULLIF(TRIM(CONCAT(p.PER_FIRST_NAME, ' ', p.PER_LAST_NAME)), ''), 
                NULLIF(TRIM(p.PER_ANI_FIRST_NAME), ''),
                CONCAT('Usuario_', p.PER_DOCUMENT_NUMBER)
            ) AS ANI_FIRST_NAME,
            lpe.LP_CREATION_DATE,
            lpe.LP_STATUS_PROCESS
        FROM log_process_enroll lpe
        INNER JOIN person p ON lpe.PER_ID = p.PER_ID
        WHERE p.PER_DOCUMENT_NUMBER = %s AND lpe.EC_ID = %s AND lpe.LP_STATUS_PROCESS = 1
        ORDER BY lpe.LP_CREATION_DATE DESC
        LIMIT 1
        """

        ec_id = _resolve_miid_ec_id()
        logger.info(f"Buscando usuario con documento: {numero_documento}")
        cursor.execute(query, (numero_documento, ec_id))
        usuario = cursor.fetchone()

        if usuario:
            (
                lp_id,
                doc_num,
                per_ani_first_name,
                per_first_name,
                per_last_name,
                ani_first_name,
                creation_date,
                status_process
            ) = usuario

            # Constructor
            first_name = ani_first_name
            logger.info("Usuario encontrado en MiID: ")
            logger.info(f"  LP_ID: {lp_id}")
            logger.info(f"  Documento: {doc_num}")
            logger.info(f"  Nombre: {first_name}")
            logger.info(f"  Fecha: {creation_date}")
            logger.info(f"  Estado: {status_process}")
            

            return {
                'lpid': lp_id,
                'documento': doc_num,
                'nombre': first_name,
                'fecha_creacion': creation_date,
                'estado': status_process
            }
        else:
            logger.warning(f"No se encontró usuario con documento: {numero_documento}")
            return None

    except Exception as e:
        logger.error(f"Error al buscar usuario: {e}")
        return None
    finally:
        if conexion:
            try:
                conexion.close()
                logger.info("Conexión a MiID cerrada")
            except Exception as e:
                logger.error(f"Error al cerrar la conexión: {e}")

def main():
    """
    Función principal para probar la búsqueda por documento.
    """
    logger.info("=== BÚSQUEDA DE USUARIO POR DOCUMENTO ===")
    
    # Solicitar número de documento al usuario
    numero_documento = input("Ingrese el número de documento a buscar: ").strip()
    
    if not numero_documento:
        logger.error("Número de documento no válido")
        return None
    
    try:
        # Buscar usuario
        usuario = buscar_usuario_por_documento(numero_documento)
        
        if usuario:
            # Guardar usuario en archivo JSON para uso posterior
            try:
                ruta_json = Path(__file__).parent / "usuario_buscado.json"
                with open(ruta_json, "w", encoding="utf-8") as f:
                    json.dump({"usuario": usuario}, f, indent=2, default=str)
                logger.info(f"Usuario guardado en: {ruta_json}")
            except Exception as e:
                logger.warning(f"No se pudo guardar usuario en JSON: {e}")
            
            logger.info("=" * 60)
            logger.info("USUARIO ENCONTRADO EXITOSAMENTE")
            logger.info("=" * 60)
            logger.info(f"Documento: {usuario['documento']}")
            logger.info(f"Nombre: {usuario['nombre']}")
            logger.info(f"LPID: {usuario['lpid']}")
            logger.info(f"Estado: {usuario['estado']}")
            logger.info("=" * 60)
            
            return usuario
        else:
            logger.error("No se encontró el usuario")
            return None
            
    except Exception as e:
        logger.error(f"Error en el proceso: {e}")
        return None

if __name__ == "__main__":
    main()
