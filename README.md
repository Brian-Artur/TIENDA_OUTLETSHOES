# Procedimiento

1. Crear entorno virtual:

```bash
python -m venv .venv

source .venv/Scripts/activate

pip install flask

pip install pyodbc

pip freeze > requirements.txt
```

2. Ejecutar tu backend dentro del entorno

```bash
python BACKEND.py
```