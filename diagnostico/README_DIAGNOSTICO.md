# Diagnóstico y pruebas locales

Esta carpeta contiene scripts de diagnóstico que NO se incluyen en los artefactos de release.

## Cómo ejecutarlos
- Requisitos: Python 3.x y dependencias del proyecto instaladas.
- Desde la raíz del repo:

`powershell
# Ejemplos
python diagnostico/test_carga_masiva.py
python diagnostico/test_carga_pequena.py
python diagnostico/test_conexiones.py
python diagnostico/test_monitor_tiempo.py
`

## Datos de ejemplo
- diagnostico/datos/clientes.xlsx se usa para pruebas de carga/lectura.

## Notas
- Si creas nuevos scripts, colócalos aquí. El release los ignorará por .gitattributes.
