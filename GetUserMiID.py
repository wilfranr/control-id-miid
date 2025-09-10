"""
Extraigo el último registro exitoso de MiID, recupero LP_ID, importante filtrar por EC_ID = 11000 (MatchId)
"""

import mysql.connector
import logging
import json
import os
from pathlib import Path
from config import AZURE_CONFIG, MIID_CONFIG
try:
    # Intentar cargar config externo junto al exe/CWD en modo empaquetado
    from importlib.util import spec_from_file_location, module_from_spec
    from pathlib import Path as _Path
    cfg_path = _Path.cwd() / "config.py"
    if cfg_path.exists():
        _spec = spec_from_file_location("config_external", str(cfg_path))
        if _spec and _spec.loader:
            _mod = module_from_spec(_spec)
            _spec.loader.exec_module(_mod)
            MIID_CONFIG = getattr(_mod, 'MIID_CONFIG', MIID_CONFIG)
except Exception:
    pass

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def conectar_miid():
    """
    Abro conexión  a MiID (Los datos de conexión los traigo desde config.py)
    """
    try:
        logger.info("Conectando a MiID")

        conexion = mysql.connector.connect(**MIID_CONFIG)
        logger.info("Conexión a MiID establecida exitosamente")
        return conexion

    except Exception as e:
        logger.error(f"Error al conectarse a la base de datos: {e}")
        return None

def obtener_ultimo_usuario_midd():
    """
    Consulto el último usuario con proceso exitoso en MiID
    """
    conexion = None
    try:
        conexion = conectar_miid()

        cursor = conexion.cursor()

        # Query para traer el último usuario
        # Por ahora solo voy a traer el nombre, LP_ID y el número de documento
        query = """
        SELECT
            lpe.LP_ID,
            p.PER_DOCUMENT_NUMBER,
            COALESCE(
                NULLIF(TRIM(p.PER_ANI_FIRST_NAME), ''), 
                CONCAT('Usuario_', p.PER_DOCUMENT_NUMBER)
            ) AS ANI_FIRST_NAME,
            lpe.LP_CREATION_DATE
        FROM log_process_enroll lpe
        INNER JOIN person p ON lpe.PER_ID = p.PER_ID
        WHERE lpe.LP_STATUS_PROCESS = 1 AND lpe.EC_ID = 11000
        ORDER BY lpe.LP_CREATION_DATE DESC
        LIMIT 1
        """

        logger.info("Ejecutando query para obtener el último usuario...")
        cursor.execute(query)
        usuario = cursor.fetchone()

        if usuario:
            (
                lp_id,
                doc_num,
                ani_first_name,
                creation_date,
            ) = usuario

            #Constructor
            first_name = ani_first_name
            logger.info("Último usuario encontrado en MiID: ")
            logger.info(f"  LP_ID: {lp_id}")
            logger.info(f"  Documento: {doc_num}")
            logger.info(f"  Nombre: {first_name}")
            logger.info(f"  Fecha: {creation_date}")

            return {
                'lpid': lp_id,
                'documento': doc_num,
                'nombre': first_name,
                'fecha_creacion': creation_date
            }
        else:
            logger.warning("No se encuentran usuarios en MiID")

    except Exception as e:
        logger.error(f"Error al obtener el usuario: {e}")
    finally:
        if conexion:
            try:
                conexion.close()
                logger.info("Conexión a MiID cerrada")
            except Exception as e:
                logger.error(f"Error al cerrar la conexion")

def main():
    """
    Orquesto la extracción del usuario y la actualización de la configuración
    para que el siguiente paso sea plug-and-play.
    """
    logger.info("=== EXTRACCIÓN DE ÚLTIMO USUARIO DE MIID (MySQL) ===")
    
    try:
        # Obtener último usuario de MiID (o usuario de prueba)
        usuario_miid = obtener_ultimo_usuario_midd()
        
        if usuario_miid:
            # Por ahora solo retornamos el usuario obtenido
            nuevo_usuario = usuario_miid
            
            # Guardar usuario en archivo JSON para uso posterior
            try:
                ruta_json = Path(__file__).parent / "last_user.json"
                with open(ruta_json, "w", encoding="utf-8") as f:
                    json.dump({"usuario": nuevo_usuario}, f, indent=2, default=str)
                logger.info(f"Usuario guardado en: {ruta_json}")
            except Exception as e:
                logger.warning(f"No se pudo guardar usuario en JSON: {e}")
            
            logger.info("=" * 60)
            logger.info("USUARIO CONFIGURADO EXITOSAMENTE")
            logger.info("=" * 60)
            logger.info(f"Documento: {nuevo_usuario['documento']}")
            logger.info(f"Nombre: {nuevo_usuario['nombre']}")
            logger.info(f"LPID: {nuevo_usuario['lpid']}")
            logger.info("=" * 60)
            logger.info("Pendiente ejecutar flujo de descarga de imagenes de BykeeperDesarrollo")
            
            return nuevo_usuario
        else:
            logger.error("No se pudo obtener usuario")
            return None
            
    except Exception as e:
        logger.error(f"Error en el proceso: {e}")
        return None

if __name__ == "__main__":
    main()
