param(
  [switch]$OneFile
)

$ErrorActionPreference = 'Stop'

# Crear venv si no existe
if (-not (Test-Path .venv)) {
  python -m venv .venv
}

# Activar venv
. .\.venv\Scripts\Activate.ps1

# Instalar dependencias
pip install --upgrade pip
pip install -r requirements.txt

# Limpiar dist/build previos
if (Test-Path build) { Remove-Item -Recurse -Force build }
if (Test-Path dist) { Remove-Item -Recurse -Force dist }

# Construir
if ($OneFile) {
  pyinstaller --clean --noconfirm --onefile --windowed control_id_gui_final.spec
} else {
  pyinstaller --clean --noconfirm control_id_gui_final.spec
}

Write-Host "Build finalizado. Revisa la carpeta dist/ControlIdGUI" -ForegroundColor Green
