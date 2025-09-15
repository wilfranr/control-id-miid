#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para probar las conexiones antes de la carga masiva.
Verifica que todas las conexiones estén funcionando correctamente.
"""

import mysql.connector
import pyodbc
import requests
import logging
from pathlib import Path

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuración (igual que en el script de carga masiva)
MIID_CONFIG = {
    "host": "miidsqldev.mysql.database.azure.com",
    "port": 3306,
    "user": "Wilfran.Rivera",
    "password": "zi4i1WFBpRX8*Bytte",
    "database": "miidcore"
}

AZURE_CONFIG = {
    "servidor": "inspruebas.database.windows.net",
    "base_datos": "ByKeeper_Desarrollo",
    "usuario": "MonitorOp",
    "contraseña": "zi3i1WFBpRX8*Bytte",
    "stored_procedure": "dbo.GetMatchIDImgFaceByCASBid",
    "business_context": "MatchId"
}

CONTROL_ID_CONFIG = {
    "base_url": "http://192.168.3.37",
    "login": "admin",
    "password": "admin"
}

def test_miid():
    """Probar conexión a MiID."""
    try:
        logger.info("Probando conexión a MiID...")
        conexion = mysql.connector.connect(**MIID_CONFIG)
        cursor = conexion.cursor()
        cursor.execute("SELECT 1")
        resultado = cursor.fetchone()
        cursor.close()
        conexion.close()
        logger.info("✅ MiID: Conexión exitosa")
        return True
    except Exception as e:
        logger.error(f"❌ MiID: Error de conexión - {e}")
        return False

def test_azure():
    """Probar conexión a Azure SQL."""
    try:
        logger.info("Probando conexión a Azure SQL...")
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
        cursor = conexion.cursor()
        cursor.execute("SELECT 1")
        resultado = cursor.fetchone()
        cursor.close()
        conexion.close()
        logger.info("✅ Azure SQL: Conexión exitosa")
        return True
    except Exception as e:
        logger.error(f"❌ Azure SQL: Error de conexión - {e}")
        return False

def test_controlid():
    """Probar conexión a ControlId."""
    try:
        logger.info("Probando conexión a ControlId...")
        url = f"{CONTROL_ID_CONFIG['base_url']}/login.fcgi"
        payload = {
            "login": CONTROL_ID_CONFIG['login'],
            "password": CONTROL_ID_CONFIG['password']
        }
        headers = {"Content-Type": "application/json"}
        
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        
        response_data = response.json()
        if 'session' in response_data:
            logger.info("✅ ControlId: Conexión exitosa")
            return True
        else:
            logger.error("❌ ControlId: No se encontró sesión en la respuesta")
            return False
    except Exception as e:
        logger.error(f"❌ ControlId: Error de conexión - {e}")
        return False

def test_archivos():
    """Probar que los archivos necesarios existan."""
    try:
        logger.info("Verificando archivos necesarios...")
        
        # Verificar archivo Excel
        archivo_excel = Path("tests/clientes.xlsx")
        if archivo_excel.exists():
            logger.info("✅ Archivo Excel encontrado")
        else:
            logger.error("❌ Archivo Excel no encontrado")
            return False
        
        # Verificar carpeta de imágenes
        carpeta_imagenes = Path(r"C:\Users\wilfran.rivera\Downloads\Imagenes Facial MiID")
        if carpeta_imagenes.exists():
            imagenes_count = len(list(carpeta_imagenes.glob("*.jpg")))
            logger.info(f"✅ Carpeta de imágenes encontrada ({imagenes_count} imágenes .jpg)")
        else:
            logger.error("❌ Carpeta de imágenes no encontrada")
            return False
        
        return True
    except Exception as e:
        logger.error(f"❌ Error verificando archivos - {e}")
        return False

def main():
    """Función principal de pruebas."""
    logger.info("=" * 60)
    logger.info("PRUEBAS DE CONEXIÓN - CARGA MASIVA")
    logger.info("=" * 60)
    
    resultados = []
    
    # Probar conexiones
    resultados.append(("MiID", test_miid()))
    resultados.append(("Azure SQL", test_azure()))
    resultados.append(("ControlId", test_controlid()))
    resultados.append(("Archivos", test_archivos()))
    
    # Mostrar resumen
    logger.info("\n" + "=" * 60)
    logger.info("RESUMEN DE PRUEBAS")
    logger.info("=" * 60)
    
    exitos = 0
    for nombre, resultado in resultados:
        status = "✅ ÉXITO" if resultado else "❌ FALLO"
        logger.info(f"{nombre}: {status}")
        if resultado:
            exitos += 1
    
    logger.info(f"\nPruebas exitosas: {exitos}/{len(resultados)}")
    
    if exitos == len(resultados):
        logger.info("🎉 TODAS LAS PRUEBAS EXITOSAS - Listo para carga masiva")
        return True
    else:
        logger.error("⚠️  ALGUNAS PRUEBAS FALLARON - Revisar configuración")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n[ÉXITO] Todas las conexiones funcionan correctamente")
        print("Puedes proceder con la carga masiva: python test_carga_masiva.py")
    else:
        print("\n[ERROR] Algunas conexiones fallaron. Revisar configuración antes de continuar.")
