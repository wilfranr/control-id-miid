@echo off
setlocal enabledelayedexpansion

echo ========================================
echo    CONSTRUCCION DE CONTROLID GUI
echo ========================================

REM Verificar que Python esté instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python no está instalado o no está en el PATH
    pause
    exit /b 1
)

REM Crear venv si no existe
if not exist .venv (
  echo Creando entorno virtual...
  python -m venv .venv
  if errorlevel 1 (
    echo ERROR: No se pudo crear el entorno virtual
    pause
    exit /b 1
  )
)

REM Activar venv
echo Activando entorno virtual...
call .\.venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: No se pudo activar el entorno virtual
    pause
    exit /b 1
)

REM Actualizar pip
echo Actualizando pip...
python -m pip install --upgrade pip --quiet

REM Instalar dependencias
echo Instalando dependencias...
python -m pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo ERROR: No se pudieron instalar las dependencias
    pause
    exit /b 1
)

REM Limpiar dist/build previos
echo Limpiando builds anteriores...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

REM Construir
echo Construyendo ejecutable...
if "%1"=="--onefile" (
  echo Modo: OneFile
  pyinstaller --clean --noconfirm --onefile --windowed --name ControlIdGUI control_id_gui_final.py
) else (
  echo Modo: Directorio
  pyinstaller --clean --noconfirm control_id_gui_final.spec
)

if errorlevel 1 (
    echo ERROR: La construcción falló
    pause
    exit /b 1
)

echo.
echo ========================================
echo    CONSTRUCCION COMPLETADA
echo ========================================
echo Build finalizado exitosamente.
echo Ejecutable disponible en: dist\ControlIdGUI\ControlIdGUI.exe
echo.

REM Verificar que el ejecutable existe
if exist "dist\ControlIdGUI\ControlIdGUI.exe" (
    echo ✓ Ejecutable creado correctamente
    echo Tamaño: 
    dir "dist\ControlIdGUI\ControlIdGUI.exe" | findstr ControlIdGUI.exe
) else (
    echo ✗ ERROR: El ejecutable no se creó correctamente
    pause
    exit /b 1
)

echo.
echo Presiona cualquier tecla para continuar...
pause >nul
endlocal
