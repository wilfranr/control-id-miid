import win32serviceutil
import win32service
import win32event
import servicemanager
import sys
import os
import time
import configparser
import logging
from logging.handlers import RotatingFileHandler

# --- Configuración de Rutas --- #
if getattr(sys, 'frozen', False):
    BASE_PATH = os.path.dirname(sys.executable)
else:
    BASE_PATH = os.path.dirname(os.path.realpath(__file__))
sys.path.append(BASE_PATH)

# Se importa después para que el path ya esté configurado
import flujo_usuario_inteligente

class ControlIdService(win32serviceutil.ServiceFramework):
    _svc_name_ = "ControlIdIntelligentFlow"
    _svc_display_name_ = "ControlId Intelligent Flow Service"
    _svc_description_ = "Ejecuta el flujo de procesamiento de usuarios de ControlId a intervalos regulares."

    def __init__(self, args):
        try:
            # --- DIAGNÓSTICO: Log #1 --- 
            servicemanager.LogInfoMsg(f"[{self._svc_name_}] Entrando en __init__.")
            
            win32serviceutil.ServiceFramework.__init__(self, args)
            self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
            self.is_running = False
            self.logger = logging.getLogger(self._svc_name_)

            # --- DIAGNÓSTICO: Log #2 --- 
            servicemanager.LogInfoMsg(f"[{self._svc_name_}] Saliendo de __init__ exitosamente.")

        except Exception as e:
            # --- DIAGNÓSTICO: Log de Error en __init__ --- 
            servicemanager.LogErrorMsg(f"[{self._svc_name_}] Error CRÍTICO durante __init__: {e}")
            # Detener inmediatamente si el constructor falla
            self.SvcStop()

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)
        self.is_running = False

    def SvcDoRun(self):
        try:
            # --- DIAGNÓSTICO: Log #3 --- 
            servicemanager.LogInfoMsg(f"[{self._svc_name_}] Entrando en SvcDoRun, iniciando configuración.")
            
            config_path = os.path.join(BASE_PATH, 'config.ini')
            config = configparser.ConfigParser()
            config.read(config_path, encoding='utf-8')

            self.sleep_interval = config.getint('Service', 'SleepInterval', fallback=10)
            log_file_rel = config.get('Service', 'LogFile', fallback='logs\\service.log')
            log_file_abs = os.path.join(BASE_PATH, log_file_rel)

            log_dir = os.path.dirname(log_file_abs)
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)

            handler = RotatingFileHandler(log_file_abs, maxBytes=5*1024*1024, backupCount=3, encoding='utf-8')
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)

            if self.logger.hasHandlers():
                self.logger.handlers.clear()
            self.logger.addHandler(handler)

            self.is_running = True
            # --- DIAGNÓSTICO: Log #4 --- 
            servicemanager.LogInfoMsg(f"[{self._svc_name_}] Configuración completada. Servicio listo para correr.")

        except Exception as e:
            servicemanager.LogErrorMsg(f"[{self._svc_name_}] Error CRÍTICO durante la configuración en SvcDoRun: {e}")
            self.SvcStop()
            return

        servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE, servicemanager.PYS_SERVICE_STARTED, (self._svc_name_, ''))
        self.logger.info("Servicio iniciado y corriendo.")

        while self.is_running:
            try:
                self.logger.info("Iniciando ciclo de ejecución.")
                flujo_usuario_inteligente.load_config()
                success = flujo_usuario_inteligente.main()
                if success:
                    self.logger.info("Ciclo de ejecución completado con éxito.")
                else:
                    self.logger.warning("Ciclo de ejecución finalizó con errores reportados.")
            except Exception as e:
                self.logger.error(f"Excepción en el bucle principal: {e}", exc_info=True)
            
            self.logger.info(f"Esperando {self.sleep_interval} segundos.")
            rc = win32event.WaitForSingleObject(self.hWaitStop, self.sleep_interval * 1000)
            if rc == win32event.WAIT_OBJECT_0:
                self.is_running = False

        self.logger.info("Servicio detenido.")

if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(ControlIdService)