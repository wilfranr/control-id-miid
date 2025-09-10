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
from config import AZURE_CONFIG, MIID_CONFIG

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
        logger.info("Conectando a MiID")

        conexion = mysql.connector.connect(**MIID_CONFIG)
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

        # Query para buscar usuario por número de documento
        query = """
        SELECT
            lpe.LP_ID,
            p.PER_DOCUMENT_NUMBER,
            COALESCE(
                NULLIF(TRIM(p.PER_ANI_FIRST_NAME), ''), 
                CONCAT('Usuario_', p.PER_DOCUMENT_NUMBER)
            ) AS ANI_FIRST_NAME,
            lpe.LP_CREATION_DATE,
            lpe.LP_STATUS_PROCESS
        FROM log_process_enroll lpe
        INNER JOIN person p ON lpe.PER_ID = p.PER_ID
        WHERE p.PER_DOCUMENT_NUMBER = %s AND lpe.EC_ID = 11000
        ORDER BY lpe.LP_CREATION_DATE DESC
        LIMIT 1
        """

        logger.info(f"Buscando usuario con documento: {numero_documento}")
        cursor.execute(query, (numero_documento,))
        usuario = cursor.fetchone()

        if usuario:
            (
                lp_id,
                doc_num,
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
