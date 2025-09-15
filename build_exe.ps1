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
  # Build onefile sin .spec (PyInstaller no acepta --onefile con .spec)
  $datas = @()
  if (Test-Path assets\images\logo.png) { $datas += "assets/images/logo.png;assets/images" }
  if (Test-Path config.py) { $datas += "config.py;." }

  $addDataArgs = @()
  foreach ($d in $datas) { $addDataArgs += @('--add-data', $d) }

  # Hidden imports para incluir módulos locales usados dinámicamente
  $hidden = @(
    'GetUserMiID',
    'GetUserByDocument',
    'flujo_usuario_inteligente',
    'download_image_to_sql_temp',
    'config',
    'pyodbc'
  )
  $hiddenArgs = @()
  foreach ($h in $hidden) { $hiddenArgs += @('--hidden-import', $h) }

  pyinstaller --clean --noconfirm --onefile --windowed --name ControlIdGUI @addDataArgs @hiddenArgs control_id_gui_final.py
} else {
  pyinstaller --clean --noconfirm control_id_gui_final.spec
}

Write-Host "Build finalizado. Revisa la carpeta dist/ControlIdGUI" -ForegroundColor Green
