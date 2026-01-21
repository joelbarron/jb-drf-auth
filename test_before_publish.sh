# 1) limpiar dist previa
rm -rf dist build *.egg-info

# 2) instalar herramientas
pip install -U build twine

# 3) construir
python -m build

# 4) validar metadata/README
twine check dist/*