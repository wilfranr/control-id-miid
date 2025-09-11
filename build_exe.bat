@echo off
setlocal enabledelayedexpansion

REM Crear venv si no existe
if not exist .venv (
  python -m venv .venv
)

REM Activar venv
call .\.venv\Scripts\activate.bat

REM Instalar dependencias
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

REM Limpiar dist/build previos
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

REM Construir
if "%1"=="--onefile" (
  pyinstaller --clean --noconfirm --onefile --windowed control_id_gui_final.spec
) else (
  pyinstaller --clean --noconfirm control_id_gui_final.spec
)

echo Build finalizado. Revisa la carpeta dist\ControlIdGUI
endlocal
