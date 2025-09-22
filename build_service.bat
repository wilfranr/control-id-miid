@echo off

echo Instalando dependencias desde requirements.txt...
call .\.venv\Scripts\activate.bat
pip install -r requirements.txt

echo Instalando PyInstaller...
pip install pyinstaller

echo Compilando el servicio en un ejecutable...

pyinstaller --name ControlIdService ^
    --onefile ^
    --console ^
    --hidden-import=win32timezone ^
    --hidden-import=win32service ^
    --hidden-import=win32event ^
    --hidden-import=servicemanager ^
    ControlIdService.py

echo.
echo Proceso completado.

echo.
echo El ejecutable se encuentra en la carpeta 'dist'.

pause
