"""
Extraigo el último registro exitoso de MiID, recupero LP_ID, importante filtrar por EC_ID = 11000 (MatchId)
"""

import mysql.connector
import logging
import json
import os
from pathlib import Path
from config import AZURE_CONFIG, MIID_CONFIG as _CFG_MIID
try:
    # Preferir env_config con entornos
    from env_config import ENVIRONMENTS as _ENVIRONMENTS, ACTIVE_ENV as _ACTIVE_ENV
except Exception:
    _ENVIRONMENTS, _ACTIVE_ENV = {}, None
def _resolve_miid_config():
    """Resolver configuración de MiID desde env_config[ACTIVE_ENV] si existe; fallback a config.MIID_CONFIG."""
    try:
        # Priorizar variable de entorno; luego releer env_config dinámicamente
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
    """Resolver MIID_EC_ID desde env_config[ACTIVE_ENV].miid.ec_id; fallback a config.MIID_EC_ID; env var; o default."""
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
            # Permitir sobreescribir MIID_EC_ID desde un config externo junto al exe
            try:
                MIID_EC_ID = int(getattr(_mod, 'MIID_EC_ID', MIID_EC_ID))
            except Exception:
                pass
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
        cfg = _resolve_miid_config()
        host = cfg.get('host') if isinstance(cfg, dict) else None
        user = cfg.get('user') if isinstance(cfg, dict) else None
        database = cfg.get('database') if isinstance(cfg, dict) else None
        logger.info(f"Conectando a MiID -> host={host}, user={user}, database={database}")

        # Filtrar solo parámetros válidos para la conexión MySQL
        allowed_keys = {"host", "port", "user", "password", "database"}
        conn_args = {k: v for k, v in (cfg or {}).items() if k in allowed_keys}
        # Asegurar tipo de puerto
        try:
            if "port" in conn_args and isinstance(conn_args["port"], str) and conn_args["port"].isdigit():
                conn_args["port"] = int(conn_args["port"])
        except Exception:
            pass
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

def obtener_ultimo_usuario_midd():
    """
    Consulto el último usuario con proceso exitoso en MiID
    """
    conexion = None
    try:
        conexion = conectar_miid()

        cursor = conexion.cursor()

        # Query para traer el último usuario usando solo las columnas que existen
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
            lpe.LP_CREATION_DATE
        FROM log_process_enroll lpe
        INNER JOIN person p ON lpe.PER_ID = p.PER_ID
        WHERE lpe.LP_STATUS_PROCESS = 1 AND lpe.EC_ID = %s
        ORDER BY lpe.LP_CREATION_DATE DESC
        LIMIT 1
        """

        ec_id = _resolve_miid_ec_id()
        logger.info(f"Ejecutando query para obtener el último usuario (EC_ID={ec_id})...")
        cursor.execute(query, (ec_id,))
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
