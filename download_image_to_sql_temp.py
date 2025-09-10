#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Descargo la imagen desde Azure SQL vía SP y la guardo localmente
para que UpdatePhoto se encargue de cargarla a ControlId.
"""

import pyodbc
import requests
import json
from typing import Optional
from pathlib import Path

# Importar configuración
try:
    from config import AZURE_CONFIG, CARPETAS_CONFIG
except ImportError:
    print("  Error: No se pudo importar config.py")
    exit(1)

def conectar_base_datos(servidor: str, base_datos: str, usuario: str, contraseña: str) -> pyodbc.Connection:
    """
    Abro conexión a Azure SQL con ODBC 17 y TLS y devuelvo la conexión lista
    para ejecutar SPs.
    
    Args:
        servidor: Host de Azure SQL
        base_datos: Base de datos destino
        usuario: Usuario SQL
        contraseña: Password SQL
        
    Returns:
        Conexión activa a la base de datos.
    
    Raises:
        pyodbc.Error: Si falla la conexión.
    """
    try:
        # Cadena de conexión para SQL Server en Azure
        connection_string = (
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={servidor};"
            f"DATABASE={base_datos};"
            f"UID={usuario};"
            f"PWD={contraseña};"
            f"Encrypt=yes;"
            f"TrustServerCertificate=no;"
        )
        
        print("Conectando a la base de datos...")
        conexion = pyodbc.connect(connection_string)
        print("Conexión establecida exitosamente")
        return conexion
        
    except pyodbc.Error as e:
        print(f"Error al conectar a la base de datos: {e}")
        raise

def ejecutar_stored_procedure(conexion: pyodbc.Connection, nombre_sp: str, 
                             lpid: str, business_context: str) -> Optional[pyodbc.Cursor]:
    """
    Ejecuto el SP con parámetros y regreso el cursor para procesar la salida.
    
    Args:
        conexion: Conexión activa a la base de datos
        nombre_sp: Nombre del Stored Procedure (ej: dbo.GetMatchIDImgFaceByCASBid)
        lpid: Valor para @LPID
        business_context: Valor para @BusinessContext
        
    Returns:
        Cursor con los resultados del SP.
    
    Raises:
        pyodbc.Error: Si falla la ejecución del SP.
    """
    try:
        cursor = conexion.cursor()
        
        # Query para ejecutar el SP con parámetros
        query = f"EXEC {nombre_sp} @LPID = ?, @BusinessContext = ?"
        
        print(f"Ejecutando SP: {nombre_sp}")
        print(f"Parámetros: LPID = {lpid}, BusinessContext = {business_context}")
        
        cursor.execute(query, (lpid, business_context))
        
        print("Stored Procedure ejecutado exitosamente")
        return cursor
        
    except pyodbc.Error as e:
        print(f"Error al ejecutar el Stored Procedure: {e}")
        raise

def procesar_resultado_sp(cursor: pyodbc.Cursor) -> Optional[str]:
    """
    Reviso el resultset para encontrar la columna que contenga la URL de la
    imagen y devuelvo la primera encontrada.
    
    Args:
        cursor: Cursor con los resultados del SP
        
    Returns:
        URL de la imagen si existe, None si no aparece.
    """
    try:
        # Obtener información de las columnas
        columns = [column[0] for column in cursor.description]
        print(f"Columnas disponibles: {columns}")
        
        # Buscar la columna que contiene la URL de la imagen
        url_column = None
        for col in columns:
            if 'url' in col.lower() or 'image' in col.lower():
                url_column = col
                break
        
        if not url_column:
            print("  No se encontró columna de URL de imagen")
            return None
        
        # Obtener el primer resultado
        row = cursor.fetchone()
        if row:
            # Obtener el índice de la columna URL
            url_index = columns.index(url_column)
            image_url = row[url_index]
            
            if image_url:
                print(f"URL de imagen encontrada: {image_url}")
                return image_url
            else:
                print("  URL de imagen está vacía")
                return None
        else:
            print("  No se encontraron resultados del SP")
            return None
            
    except Exception as e:
        print(f"Error al procesar resultado del SP: {e}")
        return None


def descargar_imagen(url: str, ruta_destino: Path) -> bool:
    """
    Descargo la imagen de la URL y la guardo localmente.
    
    Args:
        url: URL de la imagen a descargar
        ruta_destino: Ruta donde guardar la imagen
        
    Returns:
        True si se descargó correctamente; False si falló.
    """
    try:
        print(f"Descargando imagen desde: {url}")
        
        # Realizar la descarga
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        # Guardar la imagen
        with open(ruta_destino, 'wb') as f:
            f.write(response.content)
        
        # Verificar que se guardó correctamente
        if ruta_destino.exists():
            file_size = ruta_destino.stat().st_size
            print(f"Imagen descargada exitosamente. Tamaño: {file_size} bytes")
            return True
        else:
            print("  Error: La imagen no se guardó correctamente")
            return False
            
    except requests.RequestException as e:
        print(f"Error al descargar imagen: {e}")
        return False
    except Exception as e:
        print(f"Error inesperado al guardar imagen: {e}")
        return False

def obtener_usuario_actual():
    """
    Obtiene el usuario desde el archivo JSON generado por GetUserMiID.py
    """
    try:
        # Intentar leer el usuario extraído persistido
        ruta_json = Path(__file__).parent / "last_user.json"
        if ruta_json.exists():
            with open(ruta_json, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # Buscar el usuario en la estructura JSON
            if "usuario" in data:
                return data["usuario"]
            else:
                # Fallback: buscar en las claves del JSON
                keys = list(data.keys())
                if keys:
                    return data[keys[0]]
                else:
                    print("  last_user.json no contiene datos válidos")
        else:
            print("  Error: last_user.json no encontrado. Ejecuta primero: python GetUserMiID.py")
            return None
        
    except Exception as e:
        print(f"Error al obtener usuario actual: {e}")
        return None

def main():
    """
    Orquesto la descarga de imagen de Azure SQL y la guardo localmente
    para que UpdatePhoto se encargue de cargarla a ControlId.
    """
    print("=== DESCARGA DE IMAGEN DESDE BYKEEPERDESARROLLO ===")
    
    # Obtener usuario actual
    usuario = obtener_usuario_actual()
    if not usuario:
        print("  No se pudo obtener usuario de la configuración")
        return
    
    print(f"Usuario: {usuario['documento']}")
    print(f"Carpeta local: {CARPETAS_CONFIG['carpeta_local_temp']}")
    print()
    
    # Verificar que el usuario tenga LPID
    if not usuario.get('lpid'):
        print("  Error: El usuario no tiene LPID configurado")
        print("  Sugerencia: Ejecuta primero: python GetUserMiID.py")
        return
    
    # Preparar carpeta local
    ruta_local = Path(CARPETAS_CONFIG['carpeta_local_temp'])
    ruta_local.mkdir(parents=True, exist_ok=True)
    
    # Nombre del archivo de imagen
    extension = CARPETAS_CONFIG.get('extension_imagen', '.jpg')
    nombre_archivo = f"{usuario['documento']}{extension}"
    ruta_imagen_local = ruta_local / nombre_archivo
    
    try:
        # Conectar a la base de datos
        conexion = conectar_base_datos(
            AZURE_CONFIG['servidor'],
            AZURE_CONFIG['base_datos'],
            AZURE_CONFIG['usuario'],
            AZURE_CONFIG['contraseña']
        )
        
        try:
            # Ejecutar Stored Procedure
            cursor = ejecutar_stored_procedure(
                conexion,
                AZURE_CONFIG['stored_procedure'],
                usuario['lpid'],
                AZURE_CONFIG['business_context']
            )
            
            if cursor:
                # Procesar resultado para obtener URL de imagen
                image_url = procesar_resultado_sp(cursor)
                
                if image_url:
                    # Descargar imagen localmente
                    if descargar_imagen(image_url, ruta_imagen_local):
                        print("\n=== RESUMEN FINAL ===")
                        print("¡Proceso completado exitosamente!")
                        print(f"Imagen descargada: {nombre_archivo}")
                        print(f"Guardada localmente en: {ruta_imagen_local}")
                        print()
                        print("IMPORTANTE: La imagen está lista para ser usada por UpdatePhoto")
                        print("que se encargará de cargarla a ControlId.")
                    else:
                        print("  Error al descargar la imagen")
                else:
                    print("  No se pudo obtener URL de imagen del SP")
                    
                cursor.close()
            else:
                print("  Error al ejecutar el Stored Procedure")
                
        finally:
            conexion.close()
            print("Conexión a la base de datos cerrada")
            
    except Exception as e:
        print(f"  Error en el proceso: {e}")

if __name__ == "__main__":
    main()
