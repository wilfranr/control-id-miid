#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GUI final para ControlId con CustomTkinter - Versión robusta con distribución en dos columnas.
"""

import customtkinter as ctk
import threading
import time
import logging
from datetime import datetime
from pathlib import Path
import json
import sys
from PIL import Image, ImageTk

def resource_path(rel_path: str) -> str:
    try:
        base_path = getattr(sys, "_MEIPASS", None)
        if base_path:
            return str(Path(base_path) / rel_path)
        return str(Path(__file__).parent / rel_path)
    except Exception:
        return rel_path

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Versión de la aplicación
__version__ = "1.1.0"

"""Diagnóstico fino de imports para evitar 'Modo Prueba' silencioso.
Registramos exactamente qué módulo falla al empaquetar/ejecutar.
"""

# Importar módulos del proyecto con manejo de errores y diagnóstico
IMPORT_ERRORS = []
MODULES_LOADED = True

def _safe_import(label, import_callable):
    global MODULES_LOADED
    try:
        return import_callable()
    except Exception as exc:
        MODULES_LOADED = False
        msg = f"ImportError en {label}: {exc}"
        print(msg)
        IMPORT_ERRORS.append(msg)
        return None

# Imports protegidos
Safe_GetUserMiID = _safe_import("GetUserMiID", lambda: __import__("GetUserMiID", fromlist=["obtener_ultimo_usuario_midd"]))
if Safe_GetUserMiID:
    obtener_ultimo_usuario_midd = Safe_GetUserMiID.obtener_ultimo_usuario_midd

Safe_GetUserByDocument = _safe_import("GetUserByDocument", lambda: __import__("GetUserByDocument", fromlist=["buscar_usuario_por_documento"]))
if Safe_GetUserByDocument:
    buscar_usuario_por_documento = Safe_GetUserByDocument.buscar_usuario_por_documento

Safe_flujo = _safe_import(
    "flujo_usuario_inteligente",
    lambda: __import__(
        "flujo_usuario_inteligente",
        fromlist=["obtener_sesion", "procesar_usuario_inteligente", "buscar_usuario_por_registration", "set_control_id_config", "crear_grupo_para_usuario"]
    ),
)
if Safe_flujo:
    obtener_sesion = Safe_flujo.obtener_sesion
    procesar_usuario_inteligente = Safe_flujo.procesar_usuario_inteligente
    buscar_usuario_por_registration = Safe_flujo.buscar_usuario_por_registration
    set_control_id_config = Safe_flujo.set_control_id_config
    crear_grupo_para_usuario = Safe_flujo.crear_grupo_para_usuario

Safe_download = _safe_import(
    "download_image_to_sql_temp",
    lambda: __import__(
        "download_image_to_sql_temp",
        fromlist=["conectar_base_datos", "ejecutar_stored_procedure", "procesar_resultado_sp", "descargar_imagen"]
    ),
)
if Safe_download:
    conectar_base_datos = Safe_download.conectar_base_datos
    ejecutar_stored_procedure = Safe_download.ejecutar_stored_procedure
    procesar_resultado_sp = Safe_download.procesar_resultado_sp
    descargar_imagen = Safe_download.descargar_imagen

Safe_config = _safe_import("config", lambda: __import__("config", fromlist=["AZURE_CONFIG", "CARPETAS_CONFIG", "CONTROL_ID_CONFIG"]))
if Safe_config:
    AZURE_CONFIG = Safe_config.AZURE_CONFIG
    CARPETAS_CONFIG = Safe_config.CARPETAS_CONFIG
    CONTROL_ID_CONFIG = Safe_config.CONTROL_ID_CONFIG
    
    # Intentar sobrescribir con un config externo (al lado del exe o cwd)
    try:
        from importlib.util import spec_from_file_location, module_from_spec
        cfg_path = Path.cwd() / "config.py"
        if cfg_path.exists():
            spec = spec_from_file_location("config_external", str(cfg_path))
            if spec and spec.loader:
                mod = module_from_spec(spec)
                spec.loader.exec_module(mod)
                AZURE_CONFIG = getattr(mod, 'AZURE_CONFIG', AZURE_CONFIG)
                CARPETAS_CONFIG = getattr(mod, 'CARPETAS_CONFIG', CARPETAS_CONFIG)
                CONTROL_ID_CONFIG = getattr(mod, 'CONTROL_ID_CONFIG', CONTROL_ID_CONFIG)
    except Exception as _e:
        IMPORT_ERRORS.append(f"No se pudo cargar config externo: {_e}")
else:
    # Fallback: intentar cargar módulos .py colocados como datos junto al ejecutable
    try:
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            sys.path.insert(0, meipass)
            # Reintentar imports locales
            Safe_GetUserMiID = _safe_import("GetUserMiID", lambda: __import__("GetUserMiID", fromlist=["obtener_ultimo_usuario_midd"]))
            if Safe_GetUserMiID:
                obtener_ultimo_usuario_midd = Safe_GetUserMiID.obtener_ultimo_usuario_midd
            Safe_GetUserByDocument = _safe_import("GetUserByDocument", lambda: __import__("GetUserByDocument", fromlist=["buscar_usuario_por_documento"]))
            if Safe_GetUserByDocument:
                buscar_usuario_por_documento = Safe_GetUserByDocument.buscar_usuario_por_documento
            Safe_flujo = _safe_import(
                "flujo_usuario_inteligente",
                lambda: __import__("flujo_usuario_inteligente", fromlist=["obtener_sesion", "procesar_usuario_inteligente", "buscar_usuario_por_registration", "set_control_id_config", "crear_grupo_para_usuario"]))
            if Safe_flujo:
                obtener_sesion = Safe_flujo.obtener_sesion
                procesar_usuario_inteligente = Safe_flujo.procesar_usuario_inteligente
                buscar_usuario_por_registration = Safe_flujo.buscar_usuario_por_registration
                set_control_id_config = Safe_flujo.set_control_id_config
                crear_grupo_para_usuario = Safe_flujo.crear_grupo_para_usuario
            Safe_download = _safe_import(
                "download_image_to_sql_temp",
                lambda: __import__("download_image_to_sql_temp", fromlist=["conectar_base_datos", "ejecutar_stored_procedure", "procesar_resultado_sp", "descargar_imagen"]))
            if Safe_download:
                conectar_base_datos = Safe_download.conectar_base_datos
                ejecutar_stored_procedure = Safe_download.ejecutar_stored_procedure
                procesar_resultado_sp = Safe_download.procesar_resultado_sp
                descargar_imagen = Safe_download.descargar_imagen
            Safe_config_retry = _safe_import("config", lambda: __import__("config", fromlist=["AZURE_CONFIG", "CARPETAS_CONFIG", "CONTROL_ID_CONFIG"]))
            if Safe_config_retry:
                AZURE_CONFIG = Safe_config_retry.AZURE_CONFIG
                CARPETAS_CONFIG = Safe_config_retry.CARPETAS_CONFIG
                CONTROL_ID_CONFIG = Safe_config_retry.CONTROL_ID_CONFIG
    except Exception as _exc:
        IMPORT_ERRORS.append(f"Fallback de _MEIPASS falló: {_exc}")

class ControlIdGUI:
    def __init__(self):
        try:
            print("Iniciando ControlId GUI...")
            
            # Configurar CustomTkinter
            ctk.set_appearance_mode("dark")
            ctk.set_default_color_theme("blue")
            
            # Crear ventana principal
            self.root = ctk.CTk()
            self.root.title("ControlId - Gestión de Usuarios")
            self.root.geometry("1000x700")
            
            # Centrar la ventana en la pantalla
            self.root.update_idletasks()
            x = (self.root.winfo_screenwidth() // 2) - (1000 // 2)
            y = (self.root.winfo_screenheight() // 2) - (700 // 2)
            self.root.geometry(f"1000x700+{x}+{y}")
            
            # Variables de control
            self.sync_running = False
            self.sync_thread = None
            self.session = None
            self.current_user = None
            self.user_image = None
            
            print("Creando interfaz...")
            # Crear interfaz
            self.create_widgets()
            
            print("Obteniendo sesión inicial...")
            # Obtener sesión inicial
            if MODULES_LOADED:
                self.obtener_sesion_inicial()
            else:
                self.log_message("Modo de prueba - Módulos no cargados")
                if IMPORT_ERRORS:
                    for err in IMPORT_ERRORS:
                        self.log_message(err)
                self.status_label.configure(text="Modo Prueba", text_color="orange")
            
            print("GUI iniciada correctamente.")

            # Lanzar prueba de conexiones al iniciar sin bloquear la UI
            try:
                self.root.after(1000, self.probar_conexiones_inicial)
            except Exception:
                pass
            
        except Exception as e:
            print(f"Error al inicializar GUI: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
    
    def create_widgets(self):
        """Crear todos los widgets de la interfaz."""
        
        # Título principal
        self.title_label = ctk.CTkLabel(
            self.root, 
            text="ControlId - Gestión de Usuarios", 
            font=ctk.CTkFont(size=28, weight="bold")
        )
        self.title_label.pack(pady=15)
        
        # Frame principal con dos columnas
        self.main_container = ctk.CTkFrame(self.root)
        self.main_container.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Columna izquierda - Opciones
        self.left_column = ctk.CTkFrame(self.main_container)
        self.left_column.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        # Columna derecha - Información del usuario
        self.right_column = ctk.CTkFrame(self.main_container)
        self.right_column.pack(side="right", fill="both", expand=True, padx=(10, 0))
        
        # Crear secciones en la columna izquierda
        self.create_connection_section()
        self.create_user_options_section()
        self.create_sync_section()
        
        # Crear sección de información del usuario en la columna derecha
        self.create_user_info_section()
        
        # Crear sección de logs debajo de la información del usuario
        self.create_log_section()
    
    def create_connection_section(self):
        """Crear sección de estado de conexión."""
        self.connection_frame = ctk.CTkFrame(self.left_column)
        self.connection_frame.pack(fill="x", padx=15, pady=10)
        
        self.connection_label = ctk.CTkLabel(
            self.connection_frame, 
            text="Estado de Conexión", 
            font=ctk.CTkFont(size=18, weight="bold")
        )
        self.connection_label.pack(pady=10)
        
        self.status_label = ctk.CTkLabel(
            self.connection_frame, 
            text="Desconectado", 
            text_color="red",
            font=ctk.CTkFont(size=14)
        )
        self.status_label.pack(pady=5)
        
        self.status_desc_label = ctk.CTkLabel(
            self.connection_frame,
            text="La conexión con la base de datos está activa.",
            text_color="gray",
            font=ctk.CTkFont(size=12)
        )
        self.status_desc_label.pack(pady=2)
        
        self.refresh_btn = ctk.CTkButton(
            self.connection_frame,
            text="Actualizar Conexión",
            command=self.obtener_sesion_inicial,
            width=200,
            height=35
        )
        self.refresh_btn.pack(pady=10)
    
    def create_user_options_section(self):
        """Crear sección de opciones de usuario."""
        self.options_frame = ctk.CTkFrame(self.left_column)
        self.options_frame.pack(fill="x", padx=15, pady=10)
        
        self.options_label = ctk.CTkLabel(
            self.options_frame, 
            text="Opciones de Usuario", 
            font=ctk.CTkFont(size=18, weight="bold")
        )
        self.options_label.pack(pady=10)
        
        # Botón para último usuario de MiID
        self.last_user_btn = ctk.CTkButton(
            self.options_frame,
            text="Cargar Último Usuario de MiID",
            command=self.cargar_ultimo_usuario,
            width=300,
            height=45,
            font=ctk.CTkFont(size=14)
        )
        self.last_user_btn.pack(pady=10)
        
        # Frame para búsqueda por documento
        self.search_frame = ctk.CTkFrame(self.options_frame)
        self.search_frame.pack(fill="x", padx=10, pady=10)
        
        self.search_label = ctk.CTkLabel(
            self.search_frame, 
            text="Buscar por Número de Documento:",
            font=ctk.CTkFont(size=14)
        )
        self.search_label.pack(pady=5)
        
        self.document_entry = ctk.CTkEntry(
            self.search_frame,
            placeholder_text="Buscar por Número de Documento",
            width=250,
            height=35,
            font=ctk.CTkFont(size=12)
        )
        self.document_entry.pack(pady=5)
        
        self.search_btn = ctk.CTkButton(
            self.search_frame,
            text="Buscar Usuario",
            command=self.buscar_usuario_por_documento,
            width=200,
            height=35
        )
        self.search_btn.pack(pady=10)
    
    def create_sync_section(self):
        """Crear sección de sincronización automática."""
        self.sync_frame = ctk.CTkFrame(self.left_column)
        self.sync_frame.pack(fill="x", padx=15, pady=10)
        
        self.sync_label = ctk.CTkLabel(
            self.sync_frame, 
            text="Sincronización Automática", 
            font=ctk.CTkFont(size=18, weight="bold")
        )
        self.sync_label.pack(pady=10)
        
        # Estado de sincronización
        self.sync_status_label = ctk.CTkLabel(
            self.sync_frame,
            text="Detenido",
            text_color="red",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.sync_status_label.pack(pady=5)
        
        # Descripción
        self.sync_desc_label = ctk.CTkLabel(
            self.sync_frame,
            text="Ejecuta el proceso cada 5 segundos automáticamente.",
            text_color="gray",
            font=ctk.CTkFont(size=12)
        )
        self.sync_desc_label.pack(pady=2)
        
        # Botón de sincronización
        self.sync_btn = ctk.CTkButton(
            self.sync_frame,
            text="Iniciar Sincronización",
            command=self.toggle_sync,
            width=200,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.sync_btn.pack(pady=10)
    
    def create_user_info_section(self):
        """Crear sección de información del usuario."""
        self.user_info_frame = ctk.CTkFrame(self.right_column)
        self.user_info_frame.pack(fill="both", expand=True, padx=15, pady=10)
        
        self.user_info_label = ctk.CTkLabel(
            self.user_info_frame, 
            text="Información del Usuario", 
            font=ctk.CTkFont(size=18, weight="bold")
        )
        self.user_info_label.pack(pady=15)
        
        # Frame para la imagen del usuario
        self.image_frame = ctk.CTkFrame(self.user_info_frame)
        self.image_frame.pack(pady=10)
        
        self.user_image_label = ctk.CTkLabel(
            self.image_frame,
            text="Imagen",
            font=ctk.CTkFont(size=48),
            width=200,
            height=200
        )
        self.user_image_label.pack(pady=20)
        
        # Frame para información del usuario
        self.user_details_frame = ctk.CTkFrame(self.user_info_frame)
        self.user_details_frame.pack(fill="x", padx=10, pady=10)
        
        # Labels para mostrar información del usuario
        self.user_name_label = ctk.CTkLabel(
            self.user_details_frame,
            text="Nombre: -",
            font=ctk.CTkFont(size=14),
            anchor="w"
        )
        self.user_name_label.pack(fill="x", padx=10, pady=5)
        
        self.user_doc_label = ctk.CTkLabel(
            self.user_details_frame,
            text="Documento: -",
            font=ctk.CTkFont(size=14),
            anchor="w"
        )
        self.user_doc_label.pack(fill="x", padx=10, pady=5)
        
        self.user_lpid_label = ctk.CTkLabel(
            self.user_details_frame,
            text="LPID: -",
            font=ctk.CTkFont(size=14),
            anchor="w"
        )
        self.user_lpid_label.pack(fill="x", padx=10, pady=5)
        
        self.user_date_label = ctk.CTkLabel(
            self.user_details_frame,
            text="Fecha: -",
            font=ctk.CTkFont(size=14),
            anchor="w"
        )
        self.user_date_label.pack(fill="x", padx=10, pady=5)
        
        # Mensaje inicial
        self.placeholder_label = ctk.CTkLabel(
            self.user_info_frame,
            text="Busque un usuario para ver su información aquí.",
            text_color="gray",
            font=ctk.CTkFont(size=14)
        )
        self.placeholder_label.pack(pady=20)
        
        # Crear sección de logs dentro del panel de usuario
        self.create_log_section_in_user_panel()
    
    def create_log_section_in_user_panel(self):
        """Crear sección de logs dentro del panel de usuario."""
        # Frame para logs dentro del panel de usuario
        self.log_frame = ctk.CTkFrame(self.user_info_frame)
        self.log_frame.pack(fill="both", expand=True, padx=10, pady=(10, 0))
        
        self.log_label = ctk.CTkLabel(
            self.log_frame, 
            text="Log de Actividad", 
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.log_label.pack(pady=5)
        
        # Textbox para mostrar logs
        self.log_text = ctk.CTkTextbox(
            self.log_frame,
            height=120,
            font=ctk.CTkFont(family="Consolas", size=10)
        )
        self.log_text.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Frame para botones del log
        self.log_buttons_frame = ctk.CTkFrame(self.log_frame)
        self.log_buttons_frame.pack(fill="x", padx=5, pady=5)
        
        # Botón para limpiar log
        self.clear_log_btn = ctk.CTkButton(
            self.log_buttons_frame,
            text="Limpiar",
            command=self.limpiar_log,
            width=80,
            height=25,
            font=ctk.CTkFont(size=10)
        )
        self.clear_log_btn.pack(side="left", padx=2)
        
        # Botón para exportar log
        self.export_log_btn = ctk.CTkButton(
            self.log_buttons_frame,
            text="Exportar",
            command=self.exportar_log,
            width=80,
            height=25,
            font=ctk.CTkFont(size=10)
        )
        self.export_log_btn.pack(side="left", padx=2)
        
        # Botón para configuración
        self.config_btn = ctk.CTkButton(
            self.log_buttons_frame,
            text="Config",
            command=self.abrir_configuracion,
            width=80,
            height=25,
            font=ctk.CTkFont(size=10)
        )
        self.config_btn.pack(side="left", padx=2)
    
    def create_log_section(self):
        """Crear sección de log/resultados - Ya no se usa, los logs están en el panel de usuario."""
        pass
    
    def log_message(self, message):
        """Agregar mensaje al log."""
        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            log_entry = f"[{timestamp}] {message}\n"
            self.log_text.insert("end", log_entry)
            self.log_text.see("end")
            self.root.update()
        except Exception as e:
            print(f"Error al agregar mensaje al log: {e}")
    
    def limpiar_log(self):
        """Limpiar el contenido del log."""
        try:
            self.log_text.delete("1.0", "end")
            self.log_message("Log limpiado")
        except Exception as e:
            print(f"Error al limpiar log: {e}")
    
    def exportar_log(self):
        """Exportar log a archivo."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"control_id_log_{timestamp}.txt"
            log_content = self.log_text.get("1.0", "end")
            
            with open(filename, "w", encoding="utf-8") as f:
                f.write(log_content)
            
            self.log_message(f"Log exportado a: {filename}")
        except Exception as e:
            self.log_message(f"Error al exportar log: {str(e)}")
    
    def abrir_configuracion(self):
        """Abrir ventana de configuración."""
        try:
            config_window = ConfiguracionWindow(self.root, self)
        except Exception as e:
            self.log_message(f"Error al abrir configuración: {str(e)}")
    
    def obtener_sesion_inicial(self):
        """Obtener sesión inicial de ControlId."""
        if not MODULES_LOADED:
            self.log_message("Modo de prueba - No se puede obtener sesión")
            return
            
        def obtener_sesion_thread():
            try:
                self.log_message("Obteniendo sesión de ControlId...")
                self.session = obtener_sesion()
                if self.session:
                    self.status_label.configure(text="Conectado", text_color="green")
                    self.log_message("Sesión obtenida exitosamente")
                else:
                    self.status_label.configure(text="Error de Conexión", text_color="red")
                    self.log_message("Error al obtener sesión")
            except Exception as e:
                self.log_message(f"Error al obtener sesión: {str(e)}")
                self.status_label.configure(text="Error", text_color="red")
        
        threading.Thread(target=obtener_sesion_thread, daemon=True).start()
    
    def cargar_ultimo_usuario(self):
        """Cargar el último usuario de MiID."""
        if not MODULES_LOADED:
            self.log_message("Modo de prueba - Simulando carga de usuario")
            self.simular_usuario()
            return
            
        def cargar_thread():
            try:
                self.log_message("Obteniendo último usuario de MiID...")
                usuario = obtener_ultimo_usuario_midd()
                
                if usuario:
                    # Validar que el usuario tenga nombre válido
                    nombre_usuario = usuario.get('nombre', '').strip()
                    if not nombre_usuario:
                        self.log_message(f"Error: Usuario con documento {usuario['documento']} no tiene nombre válido.")
                        return
                    
                    self.log_message(f"Usuario obtenido: {usuario['nombre']} - {usuario['documento']}")
                    self.procesar_usuario_completo(usuario)
                else:
                    self.log_message("No se pudo obtener usuario de MiID")
            except Exception as e:
                self.log_message(f"Error al cargar usuario: {str(e)}")
        
        threading.Thread(target=cargar_thread, daemon=True).start()
    
    def buscar_usuario_por_documento(self):
        """Buscar usuario por número de documento."""
        documento = self.document_entry.get().strip()
        
        if not documento:
            self.log_message("Por favor ingrese un número de documento")
            return
        
        if not MODULES_LOADED:
            self.log_message("Modo de prueba - Simulando búsqueda")
            self.simular_usuario(documento)
            return
            
        def buscar_thread():
            try:
                self.log_message(f"Buscando usuario con documento: {documento}")
                usuario = buscar_usuario_por_documento(documento)
                
                if usuario:
                    # Validar que el usuario tenga nombre válido
                    nombre_usuario = usuario.get('nombre', '').strip()
                    if not nombre_usuario:
                        self.log_message(f"Error: Usuario con documento {usuario['documento']} no tiene nombre válido.")
                        return
                    
                    self.log_message(f"Usuario encontrado: {usuario['nombre']} - {usuario['documento']}")
                    self.procesar_usuario_completo(usuario)
                else:
                    self.log_message(f"No se encontró usuario con documento: {documento}")
            except Exception as e:
                self.log_message(f"Error al buscar usuario: {str(e)}")
        
        threading.Thread(target=buscar_thread, daemon=True).start()
    
    def simular_usuario(self, documento="12345678"):
        """Simular usuario para modo de prueba."""
        usuario_simulado = {
            'nombre': f'Usuario {documento}',
            'documento': documento,
            'lpid': f'test-lpid-{documento}',
            'fecha_creacion': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        self.update_user_info(usuario_simulado)
        self.log_message(f"Usuario simulado: {usuario_simulado['nombre']}")
    
    def procesar_usuario_completo(self, usuario):
        """Procesar usuario completo: descargar imagen, crear/modificar en ControlId."""
        def procesar_thread():
            try:
                # Paso 1: Descargar imagen
                self.log_message("Descargando imagen del usuario...")
                ruta_imagen = self.descargar_imagen_usuario(usuario['lpid'], usuario['documento'])
                
                if ruta_imagen:
                    self.log_message(f"Imagen descargada: {ruta_imagen}")
                else:
                    self.log_message("No se pudo descargar imagen")
                
                # Actualizar información del usuario en la interfaz (con imagen si está disponible)
                self.update_user_info(usuario, ruta_imagen)
                
                # Paso 2: Procesar usuario en ControlId
                self.log_message("Procesando usuario en ControlId...")
                user_id = procesar_usuario_inteligente(
                    self.session, 
                    usuario['nombre'], 
                    usuario['documento']
                )
                
                if user_id:
                    self.log_message(f"Usuario procesado exitosamente. ID: {user_id}")
                    
                    # Paso 3: Crear relación user_groups (grupo 1002)
                    self.log_message("Asignando grupo 1002 al usuario...")
                    if 'set_control_id_config' in globals():
                        # Asegurar que el flujo use la configuración actual
                        set_control_id_config(CONTROL_ID_CONFIG)
                    if 'crear_grupo_para_usuario' in globals():
                        if crear_grupo_para_usuario(self.session, user_id, 1002):
                            self.log_message("Grupo asignado exitosamente")
                        else:
                            self.log_message("Advertencia: no se pudo asignar grupo al usuario")
                    
                    # Paso 4: Asignar imagen al usuario si está disponible
                    if ruta_imagen and Path(ruta_imagen).exists():
                        self.log_message("Asignando imagen al usuario...")
                        if self.asignar_imagen_usuario(user_id, ruta_imagen):
                            self.log_message("Imagen asignada exitosamente")
                        else:
                            self.log_message("Error al asignar imagen")
                    else:
                        self.log_message("No hay imagen para asignar")
                    
                    self.log_message("Proceso completado exitosamente")
                else:
                    self.log_message("Error al procesar usuario en ControlId")
                    
            except Exception as e:
                self.log_message(f"Error en el procesamiento: {str(e)}")
        
        threading.Thread(target=procesar_thread, daemon=True).start()
    
    def update_user_info(self, usuario, ruta_imagen=None):
        """Actualizar la información del usuario en el panel derecho."""
        try:
            self.current_user = usuario
            
            # Ocultar placeholder
            self.placeholder_label.pack_forget()
            
            # Actualizar información
            self.user_name_label.configure(text=f"Nombre: {usuario['nombre']}")
            self.user_doc_label.configure(text=f"Documento: {usuario['documento']}")
            self.user_lpid_label.configure(text=f"LPID: {usuario['lpid']}")
            self.user_date_label.configure(text=f"Fecha: {usuario['fecha_creacion']}")
            
            # Cargar imagen si está disponible
            if ruta_imagen and Path(ruta_imagen).exists():
                self.load_user_image(ruta_imagen)
            else:
                self.user_image_label.configure(text="Sin imagen")
            
        except Exception as e:
            self.log_message(f"Error al actualizar información del usuario: {str(e)}")
    
    def load_user_image(self, ruta_imagen):
        """Cargar y mostrar la imagen del usuario."""
        try:
            if not Path(ruta_imagen).exists():
                self.user_image_label.configure(text="Imagen no encontrada")
                return
                
            # Cargar imagen con PIL
            image = Image.open(ruta_imagen)
            
            # Redimensionar imagen manteniendo proporción
            image.thumbnail((180, 180), Image.Resampling.LANCZOS)
            
            # Convertir a PhotoImage para tkinter
            photo = ImageTk.PhotoImage(image)
            
            # Actualizar label con la imagen
            self.user_image_label.configure(image=photo, text="")
            self.user_image_label.image = photo  # Mantener referencia
            
            self.log_message(f"Imagen cargada: {Path(ruta_imagen).name}")
            
        except Exception as e:
            self.log_message(f"Error al cargar imagen: {str(e)}")
            self.user_image_label.configure(text="Error al cargar imagen")

    def probar_conexiones_inicial(self):
        """Pre-chequeo silencioso: si falla algo, abrir modal con logs; si no, notificar éxito."""
        def run_precheck():
            try:
                # Cargar configuración actual
                miid_cfg = None
                azure_cfg = None
                control_cfg = None
                try:
                    from config import MIID_CONFIG as _MIID, AZURE_CONFIG as _AZR, CONTROL_ID_CONFIG as _CID
                    miid_cfg = dict(_MIID) if isinstance(_MIID, dict) else None
                    azure_cfg = dict(_AZR) if isinstance(_AZR, dict) else None
                    control_cfg = dict(_CID) if isinstance(_CID, dict) else None
                except Exception:
                    pass

                if azure_cfg is None and 'AZURE_CONFIG' in globals():
                    try:
                        azure_cfg = dict(AZURE_CONFIG)  # type: ignore
                    except Exception:
                        azure_cfg = None
                if control_cfg is None and 'CONTROL_ID_CONFIG' in globals():
                    try:
                        control_cfg = dict(CONTROL_ID_CONFIG)  # type: ignore
                    except Exception:
                        control_cfg = None

                cfg = {
                    'miid': miid_cfg or {
                        'host': '', 'port': 3306, 'user': '', 'password': '', 'database': ''
                    },
                    'azure': azure_cfg or {
                        'servidor': '', 'base_datos': '', 'usuario': '', 'contraseña': '', 'stored_procedure': '', 'business_context': ''
                    },
                    'control_id': control_cfg or {
                        'base_url': '', 'login': '', 'password': ''
                    }
                }

                # Ejecutar pruebas rápidas
                miid_ok = self._quick_test_miid(cfg['miid'])
                self.log_message(f"[MiID] {'OK' if miid_ok else 'FALLÓ'}")
                azure_ok = self._quick_test_azure(cfg['azure'])
                self.log_message(f"[Azure] {'OK' if azure_ok else 'FALLÓ'}")
                cid_ok = self._quick_test_controlid(cfg['control_id'])
                self.log_message(f"[ControlId] {'OK' if cid_ok else 'FALLÓ'}")

                def on_done():
                    try:
                        if miid_ok and azure_ok and cid_ok:
                            # Todas OK: solo actualizar estado visual a Conectado
                            if hasattr(self, 'status_label'):
                                self.status_label.configure(text="Conectado", text_color="green")
                            self.log_message("Todas las conexiones verificadas correctamente.")
                        else:
                            # Alguna falló: abrir modal detallado y marcar estado como problema
                            if hasattr(self, 'status_label'):
                                self.status_label.configure(text="Problemas de conexión", text_color="orange")
                            modal = ModalPruebasConexiones(self.root, self, cfg)
                            modal.ejecutar_pruebas_en_hilo()
                    except Exception as _exc:
                        self.log_message(f"Error mostrando resultado de conexiones: {_exc}")

                self.root.after(0, on_done)
            except Exception as exc:
                self.log_message(f"No se pudo completar pre-chequeo de conexiones: {exc}")

        threading.Thread(target=run_precheck, daemon=True).start()

    def _quick_test_miid(self, cfg):
        try:
            import mysql.connector
            cnx = mysql.connector.connect(
                host=cfg.get('host'),
                port=cfg.get('port') or 3306,
                user=cfg.get('user'),
                password=cfg.get('password'),
                database=cfg.get('database'),
                connection_timeout=5
            )
            try:
                cur = cnx.cursor()
                cur.execute("SELECT 1")
                _ = cur.fetchone()
                cur.close()
                return True
            finally:
                cnx.close()
        except Exception:
            return False

    def _quick_test_azure(self, cfg):
        try:
            if 'conectar_base_datos' in globals():
                conexion = conectar_base_datos(
                    cfg.get('servidor'),
                    cfg.get('base_datos'),
                    cfg.get('usuario'),
                    cfg.get('contraseña')
                )
                try:
                    return True if conexion else False
                finally:
                    try:
                        conexion.close()
                    except Exception:
                        pass
            return False
        except Exception:
            return False

    def _quick_test_controlid(self, cfg):
        try:
            if 'set_control_id_config' in globals():
                try:
                    set_control_id_config({
                        'base_url': cfg.get('base_url'),
                        'login': cfg.get('login'),
                        'password': cfg.get('password'),
                    })
                except Exception:
                    pass
            if 'obtener_sesion' in globals():
                session = obtener_sesion()
                return bool(session)
            return False
        except Exception:
            return False
    
    def descargar_imagen_usuario(self, lpid, numero_documento):
        """Descargar imagen del usuario desde BykeeperDesarrollo."""
        if not MODULES_LOADED:
            return None
            
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
                    lpid,
                    AZURE_CONFIG['business_context']
                )
                
                if cursor:
                    # Procesar resultado para obtener URL de imagen
                    image_url = procesar_resultado_sp(cursor)
                    
                    if image_url:
                        # Preparar ruta de destino
                        ruta_local = Path(CARPETAS_CONFIG['carpeta_local_temp'])
                        ruta_local.mkdir(parents=True, exist_ok=True)
                        extension = CARPETAS_CONFIG.get('extension_imagen', '.jpg')
                        nombre_archivo = f"{numero_documento}{extension}"
                        ruta_imagen = ruta_local / nombre_archivo
                        
                        # Descargar imagen
                        if descargar_imagen(image_url, ruta_imagen):
                            return str(ruta_imagen)
                        else:
                            return None
                    else:
                        return None
                        
                    cursor.close()
                else:
                    return None
                    
            finally:
                conexion.close()
                
        except Exception as e:
            self.log_message(f"Error al descargar imagen: {str(e)}")
            return None
    
    def asignar_imagen_usuario(self, user_id, ruta_imagen):
        """Asignar imagen a un usuario en ControlId usando el endpoint correcto."""
        if not MODULES_LOADED or not self.session:
            return False
            
        try:
            import requests
            import time
            from config import CONTROL_ID_CONFIG
            
            self.log_message(f"Asignando imagen al usuario ID: {user_id}")
            
            # Usar el endpoint correcto según la documentación
            url = f"{CONTROL_ID_CONFIG['base_url']}/user_set_image.fcgi"
            
            # Generar timestamp actual
            timestamp = str(int(time.time()))
            
            params = {
                'session': self.session,
                'user_id': user_id,
                'timestamp': timestamp
            }
            headers = {'Content-Type': 'application/octet-stream'}
            
            # Leer la imagen como datos binarios
            with open(ruta_imagen, 'rb') as image_file:
                image_data = image_file.read()
            
            self.log_message(f"Enviando imagen {Path(ruta_imagen).name} para usuario ID {user_id}")
            self.log_message(f"Tamaño de imagen: {len(image_data)} bytes")
            self.log_message(f"Timestamp: {timestamp}")
            
            response = requests.post(url, params=params, headers=headers, data=image_data, timeout=30)
            
            # Log de la respuesta para debugging
            self.log_message(f"Respuesta de asignación de imagen - Status: {response.status_code}")
            
            # El endpoint no devuelve cuerpo de respuesta según la documentación
            if response.status_code == 200:
                self.log_message("Imagen asignada exitosamente (sin respuesta del servidor)")
                return True
            else:
                self.log_message(f"Error en asignación de imagen - Status: {response.status_code}")
                if response.text:
                    self.log_message(f"Respuesta del servidor: {response.text}")
                return False
            
        except Exception as e:
            self.log_message(f"Error al asignar imagen: {str(e)}")
            return False
    
    def toggle_sync(self):
        """Alternar sincronización automática."""
        if not self.sync_running:
            self.iniciar_sincronizacion()
        else:
            self.detener_sincronizacion()
    
    def iniciar_sincronizacion(self):
        """Iniciar sincronización automática."""
        if not self.session and MODULES_LOADED:
            self.log_message("No hay sesión activa. No se puede iniciar sincronización.")
            return
        
        self.sync_running = True
        self.sync_btn.configure(text="Detener Sincronización")
        self.sync_status_label.configure(text="Ejecutando", text_color="green")
        self.log_message("Sincronización automática iniciada (cada 5 segundos)")
        
        # Iniciar hilo de sincronización
        self.sync_thread = threading.Thread(target=self.sincronizacion_loop, daemon=True)
        self.sync_thread.start()
    
    def detener_sincronizacion(self):
        """Detener sincronización automática."""
        self.sync_running = False
        self.sync_btn.configure(text="Iniciar Sincronización")
        self.sync_status_label.configure(text="Detenido", text_color="red")
        self.log_message("Sincronización automática detenida")
    
    def sincronizacion_loop(self):
        """Loop de sincronización automática."""
        while self.sync_running:
            try:
                self.log_message("Ejecutando sincronización automática...")
                
                if MODULES_LOADED:
                    # Obtener último usuario de MiID
                    usuario = obtener_ultimo_usuario_midd()
                    
                    if usuario:
                        # Validar que el usuario tenga nombre válido
                        nombre_usuario = usuario.get('nombre', '').strip()
                        if not nombre_usuario:
                            self.log_message(f"Advertencia: Usuario con documento {usuario['documento']} no tiene nombre válido. Saltando procesamiento.")
                            continue
                        
                        # Verificar si el usuario ya existe en ControlId
                        usuario_existente = buscar_usuario_por_registration(self.session, usuario['documento'])
                        
                        if not usuario_existente:
                            # Usuario no existe, procesarlo
                            self.log_message(f"Nuevo usuario detectado: {usuario['nombre']} - {usuario['documento']}")
                            self.procesar_usuario_completo(usuario)
                        else:
                            # Usuario ya existe, pero verificar si necesita actualización de imagen y grupo
                            self.log_message(f"Usuario ya existe: {usuario['nombre']} - {usuario['documento']}")
                            self.log_message("Verificando si necesita actualización de imagen y grupo...")
                            
                            # Asegurar que el usuario tenga el grupo 1002
                            if 'set_control_id_config' in globals():
                                set_control_id_config(CONTROL_ID_CONFIG)
                            if 'crear_grupo_para_usuario' in globals():
                                if crear_grupo_para_usuario(self.session, str(usuario_existente['id']), 1002):
                                    self.log_message("Grupo 1002 verificado/actualizado")
                                else:
                                    self.log_message("Advertencia: no se pudo verificar grupo del usuario")
                            
                            # Descargar imagen y asignarla
                            ruta_imagen = self.descargar_imagen_usuario(usuario['lpid'], usuario['documento'])
                            if ruta_imagen:
                                self.log_message("Asignando imagen actualizada...")
                                if self.asignar_imagen_usuario(usuario_existente['id'], ruta_imagen):
                                    self.log_message("Imagen actualizada exitosamente")
                                else:
                                    self.log_message("Error al actualizar imagen")
                            else:
                                self.log_message("No se pudo descargar imagen para actualización")
                    else:
                        self.log_message("No hay usuarios nuevos en MiID")
                else:
                    self.log_message("Modo de prueba - No hay usuarios nuevos")
                
                # Esperar 5 segundos
                for i in range(50):  # 50 * 0.1 = 5 segundos
                    if not self.sync_running:
                        break
                    time.sleep(0.1)
                    
            except Exception as e:
                self.log_message(f"Error en sincronización: {str(e)}")
                time.sleep(5)  # Esperar 5 segundos antes de reintentar
    
    def run(self):
        """Ejecutar la aplicación."""
        try:
            self.log_message("GUI final iniciada correctamente")
            self.log_message("Funcionalidades disponibles:")
            self.log_message("  • Sincronización automática")
            self.log_message("  • Cargar último usuario de MiID")
            self.log_message("  • Búsqueda por número de documento")
            self.log_message("  • Visualización de información de usuario")
            self.log_message("  • Log en tiempo real")
            if not MODULES_LOADED:
                self.log_message("  • Modo de prueba activado")
            self.root.mainloop()
        except Exception as e:
            print(f"Error al ejecutar GUI: {e}")
            import traceback
            traceback.print_exc()

class ConfiguracionWindow:
    """Ventana modal de configuración."""
    
    def __init__(self, parent, main_app):
        self.parent = parent
        self.main_app = main_app
        self.config_data = {}
        
        # Crear ventana modal
        self.window = ctk.CTkToplevel(parent)
        self.window.title("Configuración del Sistema")
        self.window.geometry("600x700")
        self.window.resizable(False, False)
        
        # Centrar ventana
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (600 // 2)
        y = (self.window.winfo_screenheight() // 2) - (700 // 2)
        self.window.geometry(f"600x700+{x}+{y}")
        
        # Cargar configuración actual
        self.cargar_configuracion()
        
        # Crear interfaz
        self.crear_interfaz()
        
        # Hacer que la ventana sea modal
        self.window.transient(parent)
        self.window.grab_set()
    
    def cargar_configuracion(self):
        """Cargar configuración actual desde config.py."""
        try:
            from config import MIID_CONFIG, AZURE_CONFIG, CONTROL_ID_CONFIG, CARPETAS_CONFIG
            
            self.config_data = {
                'miid': MIID_CONFIG.copy(),
                'azure': AZURE_CONFIG.copy(),
                'control_id': CONTROL_ID_CONFIG.copy(),
                'carpetas': CARPETAS_CONFIG.copy()
            }
        except Exception as e:
            print(f"Error al cargar configuración: {e}")
            # Configuración por defecto
            self.config_data = {
                'miid': {
                    'host': 'miidsqldev.mysql.database.azure.com',
                    'port': 3306,
                    'user': 'usuario',
                    'password': 'contraseña',
                    'database': 'miidcore'
                },
                'azure': {
                    'servidor': 'servidor.database.windows.net',
                    'base_datos': 'ByKeeper_Desarrollo',
                    'usuario': 'usuario',
                    'contraseña': 'contraseña',
                    'stored_procedure': 'dbo.GetMatchIDImgFaceByCASBid',
                    'business_context': 'Bytte'
                },
                'control_id': {
                    'base_url': '',
                    'login': '',
                    'password': ''
                },
                'carpetas': {
                    'carpeta_local_temp': 'C:\\temp\\Imagenes_Pro',
                    'extension_imagen': '.jpg'
                }
            }
    
    def crear_interfaz(self):
        """Crear la interfaz de configuración."""
        # Título
        title_label = ctk.CTkLabel(
            self.window,
            text="Configuración del Sistema",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(pady=15)
        
        # Crear notebook para pestañas
        self.notebook = ctk.CTkTabview(self.window)
        self.notebook.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Pestaña MiID
        self.crear_pestana_miid()
        
        # Pestaña Azure
        self.crear_pestana_azure()
        
        # Pestaña ControlId
        self.crear_pestana_control_id()
        
        # Pestaña Carpetas
        self.crear_pestana_carpetas()
        
        # Botones de acción
        self.crear_botones_accion()
    
    def crear_pestana_miid(self):
        """Crear pestaña de configuración MiID."""
        tab = self.notebook.add("MiID")
        
        # Título
        title = ctk.CTkLabel(tab, text="Configuración MiID (MySQL)", font=ctk.CTkFont(size=16, weight="bold"))
        title.pack(pady=10)
        
        # Host
        ctk.CTkLabel(tab, text="Host:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=20, pady=(10, 0))
        self.miid_host = ctk.CTkEntry(tab, width=400, height=30)
        self.miid_host.pack(padx=20, pady=(0, 5))
        self.miid_host.insert(0, self.config_data['miid']['host'])
        
        # Puerto
        ctk.CTkLabel(tab, text="Puerto:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=20, pady=(10, 0))
        self.miid_port = ctk.CTkEntry(tab, width=400, height=30)
        self.miid_port.pack(padx=20, pady=(0, 5))
        self.miid_port.insert(0, str(self.config_data['miid']['port']))
        
        # Usuario
        ctk.CTkLabel(tab, text="Usuario:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=20, pady=(10, 0))
        self.miid_user = ctk.CTkEntry(tab, width=400, height=30)
        self.miid_user.pack(padx=20, pady=(0, 5))
        self.miid_user.insert(0, self.config_data['miid']['user'])
        
        # Contraseña
        ctk.CTkLabel(tab, text="Contraseña:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=20, pady=(10, 0))
        self.miid_password = ctk.CTkEntry(tab, width=400, height=30, show="*")
        self.miid_password.pack(padx=20, pady=(0, 5))
        self.miid_password.insert(0, self.config_data['miid']['password'])
        
        # Base de datos
        ctk.CTkLabel(tab, text="Base de datos:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=20, pady=(10, 0))
        self.miid_database = ctk.CTkEntry(tab, width=400, height=30)
        self.miid_database.pack(padx=20, pady=(0, 5))
        self.miid_database.insert(0, self.config_data['miid']['database'])
    
    def crear_pestana_azure(self):
        """Crear pestaña de configuración Azure."""
        tab = self.notebook.add("Azure")
        
        # Título
        title = ctk.CTkLabel(tab, text="Configuración Azure SQL", font=ctk.CTkFont(size=16, weight="bold"))
        title.pack(pady=10)
        
        # Servidor
        ctk.CTkLabel(tab, text="Servidor:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=20, pady=(10, 0))
        self.azure_servidor = ctk.CTkEntry(tab, width=400, height=30)
        self.azure_servidor.pack(padx=20, pady=(0, 5))
        self.azure_servidor.insert(0, self.config_data['azure']['servidor'])
        
        # Base de datos
        ctk.CTkLabel(tab, text="Base de datos:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=20, pady=(10, 0))
        self.azure_database = ctk.CTkEntry(tab, width=400, height=30)
        self.azure_database.pack(padx=20, pady=(0, 5))
        self.azure_database.insert(0, self.config_data['azure']['base_datos'])
        
        # Usuario
        ctk.CTkLabel(tab, text="Usuario:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=20, pady=(10, 0))
        self.azure_user = ctk.CTkEntry(tab, width=400, height=30)
        self.azure_user.pack(padx=20, pady=(0, 5))
        self.azure_user.insert(0, self.config_data['azure']['usuario'])
        
        # Contraseña
        ctk.CTkLabel(tab, text="Contraseña:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=20, pady=(10, 0))
        self.azure_password = ctk.CTkEntry(tab, width=400, height=30, show="*")
        self.azure_password.pack(padx=20, pady=(0, 5))
        self.azure_password.insert(0, self.config_data['azure']['contraseña'])
        
        # Stored Procedure
        ctk.CTkLabel(tab, text="Stored Procedure:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=20, pady=(10, 0))
        self.azure_sp = ctk.CTkEntry(tab, width=400, height=30)
        self.azure_sp.pack(padx=20, pady=(0, 5))
        self.azure_sp.insert(0, self.config_data['azure']['stored_procedure'])
        
        # Business Context
        ctk.CTkLabel(tab, text="Business Context:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=20, pady=(10, 0))
        self.azure_context = ctk.CTkEntry(tab, width=400, height=30)
        self.azure_context.pack(padx=20, pady=(0, 5))
        self.azure_context.insert(0, self.config_data['azure']['business_context'])
    
    def crear_pestana_control_id(self):
        """Crear pestaña de configuración ControlId."""
        tab = self.notebook.add("ControlId")
        
        # Título
        title = ctk.CTkLabel(tab, text="Configuración ControlId", font=ctk.CTkFont(size=16, weight="bold"))
        title.pack(pady=10)
        
        # URL Base
        ctk.CTkLabel(tab, text="URL Base:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=20, pady=(10, 0))
        self.control_url = ctk.CTkEntry(tab, width=400, height=30)
        self.control_url.pack(padx=20, pady=(0, 5))
        self.control_url.insert(0, self.config_data['control_id']['base_url'])
        
        # Usuario
        ctk.CTkLabel(tab, text="Usuario:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=20, pady=(10, 0))
        self.control_user = ctk.CTkEntry(tab, width=400, height=30)
        self.control_user.pack(padx=20, pady=(0, 5))
        self.control_user.insert(0, self.config_data['control_id']['login'])
        
        # Contraseña
        ctk.CTkLabel(tab, text="Contraseña:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=20, pady=(10, 0))
        self.control_password = ctk.CTkEntry(tab, width=400, height=30, show="*")
        self.control_password.pack(padx=20, pady=(0, 5))
        self.control_password.insert(0, self.config_data['control_id']['password'])
    
    def crear_pestana_carpetas(self):
        """Crear pestaña de configuración de carpetas."""
        tab = self.notebook.add("Carpetas")
        
        # Título
        title = ctk.CTkLabel(tab, text="Configuración de Carpetas", font=ctk.CTkFont(size=16, weight="bold"))
        title.pack(pady=10)
        
        # Carpeta temporal
        ctk.CTkLabel(tab, text="Carpeta Temporal:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=20, pady=(10, 0))
        self.carpeta_temp = ctk.CTkEntry(tab, width=400, height=30)
        self.carpeta_temp.pack(padx=20, pady=(0, 5))
        self.carpeta_temp.insert(0, self.config_data['carpetas']['carpeta_local_temp'])
        
        # Extensión de imagen
        ctk.CTkLabel(tab, text="Extensión de Imagen:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=20, pady=(10, 0))
        self.extension_img = ctk.CTkEntry(tab, width=400, height=30)
        self.extension_img.pack(padx=20, pady=(0, 5))
        self.extension_img.insert(0, self.config_data['carpetas']['extension_imagen'])
    
    def crear_botones_accion(self):
        """Crear botones de acción."""
        button_frame = ctk.CTkFrame(self.window)
        button_frame.pack(fill="x", padx=20, pady=10)
        
        # Botón Guardar
        save_btn = ctk.CTkButton(
            button_frame,
            text="Guardar Configuración",
            command=self.guardar_configuracion,
            width=150,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        save_btn.pack(side="left", padx=10, pady=10)
        
        # Botón Cancelar
        cancel_btn = ctk.CTkButton(
            button_frame,
            text="Cancelar",
            command=self.cancelar,
            width=150,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        cancel_btn.pack(side="left", padx=10, pady=10)
        
        # Botón Probar Conexiones
        test_btn = ctk.CTkButton(
            button_frame,
            text="Probar Conexiones",
            command=self.probar_conexiones,
            width=150,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        test_btn.pack(side="left", padx=10, pady=10)
    
    def guardar_configuracion(self):
        """Guardar configuración en archivo config.py."""
        try:
            # Recopilar datos de los campos
            nueva_config = {
                'miid': {
                    'host': self.miid_host.get(),
                    'port': int(self.miid_port.get()),
                    'user': self.miid_user.get(),
                    'password': self.miid_password.get(),
                    'database': self.miid_database.get()
                },
                'azure': {
                    'servidor': self.azure_servidor.get(),
                    'base_datos': self.azure_database.get(),
                    'usuario': self.azure_user.get(),
                    'contraseña': self.azure_password.get(),
                    'stored_procedure': self.azure_sp.get(),
                    'business_context': self.azure_context.get()
                },
                'control_id': {
                    'base_url': self.control_url.get(),
                    'login': self.control_user.get(),
                    'password': self.control_password.get()
                },
                'carpetas': {
                    'carpeta_local_temp': self.carpeta_temp.get(),
                    'extension_imagen': self.extension_img.get()
                }
            }
            
            # Generar contenido del archivo config.py
            config_content = f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuración del sistema ControlId.
Este archivo se genera automáticamente desde la GUI de configuración.
"""

# Configuración MiID (MySQL)
MIID_CONFIG = {{
    "host": "{nueva_config['miid']['host']}",
    "port": {nueva_config['miid']['port']},
    "user": "{nueva_config['miid']['user']}",
    "password": "{nueva_config['miid']['password']}",
    "database": "{nueva_config['miid']['database']}"
}}

# Configuración Azure SQL (BykeeperDesarrollo)
AZURE_CONFIG = {{
    "servidor": "{nueva_config['azure']['servidor']}",
    "base_datos": "{nueva_config['azure']['base_datos']}",
    "usuario": "{nueva_config['azure']['usuario']}",
    "contraseña": "{nueva_config['azure']['contraseña']}",
    "stored_procedure": "{nueva_config['azure']['stored_procedure']}",
    "business_context": "{nueva_config['azure']['business_context']}"
}}

# Configuración ControlId
CONTROL_ID_CONFIG = {{
    "base_url": "{nueva_config['control_id']['base_url']}",
    "login": "{nueva_config['control_id']['login']}",
    "password": "{nueva_config['control_id']['password']}"
}}

# Configuración de carpetas
CARPETAS_CONFIG = {{
    "carpeta_local_temp": r"{nueva_config['carpetas']['carpeta_local_temp']}",
    "extension_imagen": "{nueva_config['carpetas']['extension_imagen']}"
}}
'''
            
            # Escribir archivo
            with open('config.py', 'w', encoding='utf-8') as f:
                f.write(config_content)
            
            # Recargar dinámicamente el módulo de configuración y propagar cambios
            try:
                import importlib
                import config as _cfg
                _cfg = importlib.reload(_cfg)
                # Actualizar variables globales utilizadas en la app
                global AZURE_CONFIG, CARPETAS_CONFIG, CONTROL_ID_CONFIG
                AZURE_CONFIG = _cfg.AZURE_CONFIG
                CARPETAS_CONFIG = _cfg.CARPETAS_CONFIG
                CONTROL_ID_CONFIG = _cfg.CONTROL_ID_CONFIG
                # Actualizar configuración usada por el flujo (peticiones HTTP)
                if 'set_control_id_config' in globals():
                    set_control_id_config(_cfg.CONTROL_ID_CONFIG)
                # Invalidar sesión actual para forzar re-login con nueva IP/credenciales
                if hasattr(self, 'main_app') and hasattr(self.main_app, 'session'):
                    self.main_app.session = None
                    if hasattr(self.main_app, 'status_label'):
                        self.main_app.status_label.configure(text="Desconectado", text_color="red")
            except Exception as _e:
                self.mostrar_mensaje(f"Advertencia: no se pudo recargar configuración en caliente: {_e}", "Error")

            # Mostrar mensaje de éxito
            self.mostrar_mensaje("Configuración guardada exitosamente", "Éxito")
            
            # Cerrar ventana
            self.window.destroy()
            
        except Exception as e:
            self.mostrar_mensaje(f"Error al guardar configuración: {str(e)}", "Error")
    
    def cancelar(self):
        """Cancelar y cerrar ventana."""
        self.window.destroy()
    
    def probar_conexiones(self):
        """Probar conexiones con la configuración actual."""
        try:
            # Recopilar configuración actual desde los inputs (sin guardar todavía)
            cfg = {
                'miid': {
                    'host': self.miid_host.get(),
                    'port': int(self.miid_port.get() or 0) if str(self.miid_port.get()).strip() else 0,
                    'user': self.miid_user.get(),
                    'password': self.miid_password.get(),
                    'database': self.miid_database.get(),
                },
                'azure': {
                    'servidor': self.azure_servidor.get(),
                    'base_datos': self.azure_database.get(),
                    'usuario': self.azure_user.get(),
                    'contraseña': self.azure_password.get(),
                    'stored_procedure': self.azure_sp.get(),
                    'business_context': self.azure_context.get(),
                },
                'control_id': {
                    'base_url': self.control_url.get(),
                    'login': self.control_user.get(),
                    'password': self.control_password.get(),
                }
            }

            # Abrir modal de pruebas con logs en tiempo real
            modal = ModalPruebasConexiones(self.parent, self.main_app, cfg)
            modal.ejecutar_pruebas_en_hilo()
            
        except Exception as e:
            self.mostrar_mensaje(f"Error en pruebas: {str(e)}", "Error")
    
    def mostrar_mensaje(self, mensaje, tipo):
        """Mostrar mensaje en la ventana principal."""
        if hasattr(self.main_app, 'log_message'):
            self.main_app.log_message(mensaje)
        
        # También mostrar en una ventana de mensaje
        import tkinter.messagebox as msgbox
        if tipo == "Éxito":
            msgbox.showinfo("Éxito", mensaje)
        elif tipo == "Error":
            msgbox.showerror("Error", mensaje)
        else:
            msgbox.showinfo("Información", mensaje)

class ModalPruebasConexiones:
    """Modal para mostrar logs de prueba de conexiones: MiID, Azure y ControlId."""
    def __init__(self, parent, main_app, config_dict):
        self.parent = parent
        self.main_app = main_app
        self.config_dict = config_dict

        self.window = ctk.CTkToplevel(parent)
        self.window.title("Pruebas de Conexión")
        self.window.geometry("700x500")
        self.window.resizable(True, True)

        # Centrar
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (700 // 2)
        y = (self.window.winfo_screenheight() // 2) - (500 // 2)
        self.window.geometry(f"700x500+{x}+{y}")

        # UI
        title = ctk.CTkLabel(self.window, text="Ejecución de pruebas de conexión", font=ctk.CTkFont(size=18, weight="bold"))
        title.pack(pady=10)

        self.text = ctk.CTkTextbox(self.window, font=ctk.CTkFont(family="Consolas", size=11))
        self.text.pack(fill="both", expand=True, padx=10, pady=10)

        btn_frame = ctk.CTkFrame(self.window)
        btn_frame.pack(fill="x", padx=10, pady=(0,10))

        self.close_btn = ctk.CTkButton(btn_frame, text="Cerrar", command=self.window.destroy)
        self.close_btn.pack(side="right")

        # Modal
        self.window.transient(parent)
        self.window.grab_set()

    def log(self, message):
        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            line = f"[{timestamp}] {message}\n"
            self.text.insert("end", line)
            self.text.see("end")
            if hasattr(self.main_app, 'log_message'):
                self.main_app.log_message(message)
            self.window.update()
        except Exception:
            pass

    def ejecutar_pruebas_en_hilo(self):
        threading.Thread(target=self._run_tests, daemon=True).start()

    def _run_tests(self):
        try:
            self.log("Iniciando pruebas de conexión...")
            self._test_miid()
            self._test_azure()
            self._test_controlid()
            self.log("Pruebas de conexión completadas.")
        except Exception as exc:
            self.log(f"Error general en pruebas: {exc}")

    def _test_miid(self):
        cfg = self.config_dict.get('miid', {})
        self.log("[MiID] Probando conexión MySQL...")
        try:
            import mysql.connector
            cnx = mysql.connector.connect(
                host=cfg.get('host'),
                port=cfg.get('port') or 3306,
                user=cfg.get('user'),
                password=cfg.get('password'),
                database=cfg.get('database'),
                connection_timeout=10
            )
            try:
                cur = cnx.cursor()
                cur.execute("SELECT 1")
                _ = cur.fetchone()
                cur.close()
                self.log("[MiID] Conexión OK y consulta simple exitosa.")
            finally:
                cnx.close()
        except Exception as exc:
            self.log(f"[MiID] Error: {exc}")

    def _test_azure(self):
        cfg = self.config_dict.get('azure', {})
        self.log("[Azure] Probando conexión a SQL y ejecución de SP de prueba...")
        try:
            # Reutilizar helper existente si está disponible
            if 'conectar_base_datos' in globals():
                conexion = conectar_base_datos(
                    cfg.get('servidor'),
                    cfg.get('base_datos'),
                    cfg.get('usuario'),
                    cfg.get('contraseña')
                )
                try:
                    # Ejecución mínima para validar SP si es posible
                    if 'ejecutar_stored_procedure' in globals():
                        try:
                            cursor = ejecutar_stored_procedure(conexion, cfg.get('stored_procedure'), 'TEST_LPID', cfg.get('business_context'))
                            if cursor:
                                self.log("[Azure] Conexión OK y SP ejecutado (dummy).")
                            else:
                                self.log("[Azure] Conexión OK, pero no se pudo ejecutar SP.")
                        except Exception as _:
                            self.log("[Azure] Conexión OK. SP no validado (parámetros de prueba).")
                    else:
                        self.log("[Azure] Conexión OK.")
                finally:
                    try:
                        conexion.close()
                    except Exception:
                        pass
            else:
                self.log("[Azure] No está disponible el helper de conexión.")
        except Exception as exc:
            self.log(f"[Azure] Error: {exc}")

    def _test_controlid(self):
        cfg = self.config_dict.get('control_id', {})
        self.log("[ControlId] Probando obtener sesión...")
        try:
            # Aplicar config temporalmente al flujo si está disponible
            if 'set_control_id_config' in globals():
                try:
                    set_control_id_config({
                        'base_url': cfg.get('base_url'),
                        'login': cfg.get('login'),
                        'password': cfg.get('password'),
                    })
                except Exception:
                    pass
            if 'obtener_sesion' in globals():
                session = obtener_sesion()
                if session:
                    self.log("[ControlId] Sesión obtenida correctamente.")
                else:
                    self.log("[ControlId] No se pudo obtener sesión.")
            else:
                self.log("[ControlId] Función obtener_sesion no disponible.")
        except Exception as exc:
            self.log(f"[ControlId] Error: {exc}")

def main():
    """Función principal."""
    try:
        print("Iniciando ControlId GUI Final...")
        app = ControlIdGUI()
        app.run()
    except Exception as e:
        print(f"Error fatal: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
