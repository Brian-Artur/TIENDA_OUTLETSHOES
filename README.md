# Procedimiento

1. Crear entorno virtual:

```bash
python -m venv .venv
```
2. Activar entorno virtual:

```bash
source .venv/Scripts/activate
```

- Deberá aparecer un `(venv)` al principio de cada línea de comando.

3. Instalar Flask en el entorno

```bash
pip install flask
```

4. Instalar `pyodbc`
```bash
pip install pyodbc
```
5. Descargar e instalar driver de Microsoft ODBC 18
https://go.microsoft.com/fwlink/?linkid=2307162



5. Guardar dependencias

```bash
pip freeze > requirements.txt
```

5. Ejecutar tu backend dentro del entorno

```bash
python BACKEND.py
```