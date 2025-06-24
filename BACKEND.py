from flask import Flask, request, jsonify, render_template
import pyodbc
from datetime import datetime
import io
from flask import send_file
from flask_cors import CORS
import os

import base64

app = Flask(__name__)

# mi codigo
CORS(app)  # Esto permite CORS en todas las rutas


@app.route("/imagen-generica")
def imagen_generica():
    ruta = os.path.join(os.path.dirname(__file__), "img", "foto.jpg")
    return send_file(ruta, mimetype="image/jpg")


""" DB_CONFIG = {
    'server': 'SERVIDOR\\BREOGAN',
    'database': 'CENTRALBREOGAN',
    'username': 'sa',
    'password': 'masterkey',
    'driver': '{ODBC Driver 17 for SQL Server}'
} """

# Conectar a la base de datos local
""" DB_CONFIG = {
    'server': 'localhost',
    'database': 'CENTRALBREOGAN',
    'username': 'DESKTOP-LP5PVJ9\Victor',
    'password': '1229',
    'driver': '{ODBC Driver 17 for SQL Server}',
}

def get_connection():
    conn_str = (
        f"DRIVER={DB_CONFIG['driver']};"
        f"SERVER={DB_CONFIG['server']};"
        f"DATABASE={DB_CONFIG['database']};"
        f"UID={DB_CONFIG['username']};"
        f"PWD={DB_CONFIG['password']}"
        
    )
    return pyodbc.connect(conn_str) """
DB_CONFIG = {
    "server": "localhost",
    "database": "CENTRALBREOGAN",
    "driver": "{ODBC Driver 17 for SQL Server}",
}


def get_connection():
    conn_str = (
        f"DRIVER={DB_CONFIG['driver']};"
        f"SERVER={DB_CONFIG['server']};"
        f"DATABASE={DB_CONFIG['database']};"
        f"Trusted_Connection=yes;"
    )
    return pyodbc.connect(conn_str)


@app.route("/ventas", methods=["GET", "OPTIONS"])
def get_ventas():
    if request.method == "OPTIONS":
        return ("", 200, cors_headers())

    tienda = request.args.get("tienda")
    fechaini = request.args.get("fechaini")
    fechafin = request.args.get("fechafin")

    if not all([tienda, fechaini, fechafin]):
        return (
            jsonify({"error": "Faltan parámetros: tienda, fechaini o fechafin"}),
            400,
            cors_headers(),
        )

    try:
        fechaini_dt = datetime.strptime(fechaini, "%Y-%m-%d")
        fechafin_dt = datetime.strptime(fechafin, "%Y-%m-%d")
    except ValueError:
        return (
            jsonify({"error": "Formato de fecha inválido. Usa YYYY-MM-DD"}),
            400,
            cors_headers(),
        )

    if tienda != "T0":
        query = """
        SELECT 
            ALBVENTALIN.REFERENCIA, 
            DESCRIPCION, 
            TALLA,
            COLOR,
            SUM(UNIDADESTOTAL) AS UNIDADES, 
            SUM(UNIDADESTOTAL) * PRECIOIVA AS TOTAL
        FROM ALBVENTALIN 
        LEFT JOIN ALBVENTACAB 
            ON ALBVENTALIN.NUMSERIE = ALBVENTACAB.NUMSERIE 
            AND ALBVENTALIN.NUMALBARAN = ALBVENTACAB.NUMALBARAN 
        WHERE 
            ALBVENTACAB.FECHA BETWEEN ? AND ?
            AND ALBVENTALIN.CODALMACEN = ?
        GROUP BY 
            ALBVENTALIN.REFERENCIA, DESCRIPCION, TALLA, COLOR, PRECIOIVA
    """

        try:
            with get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, (fechaini_dt, fechafin_dt, tienda))
                    columns = [col[0] for col in cursor.description]
                    data = [dict(zip(columns, row)) for row in cursor.fetchall()]
            return (
                jsonify({"message": "Consulta ejecutada correctamente", "data": data}),
                200,
                cors_headers(),
            )

        except Exception as e:
            return (
                jsonify(
                    {
                        "message": "Ocurrió un error durante la ejecución",
                        "error": str(e),
                    }
                ),
                500,
                cors_headers(),
            )

    else:
        query = """
        SELECT 
            ALBVENTALIN.REFERENCIA, 
            DESCRIPCION, 
            TALLA,
            COLOR,
            SUM(UNIDADESTOTAL) AS UNIDADES, 
            SUM(UNIDADESTOTAL) * PRECIOIVA AS TOTAL
        FROM ALBVENTALIN 
        LEFT JOIN ALBVENTACAB 
            ON ALBVENTALIN.NUMSERIE = ALBVENTACAB.NUMSERIE 
            AND ALBVENTALIN.NUMALBARAN = ALBVENTACAB.NUMALBARAN 
        WHERE 
            ALBVENTACAB.FECHA BETWEEN ? AND ?
            AND (ALBVENTALIN.CODALMACEN = 'T1' OR ALBVENTALIN.CODALMACEN = 'T2' OR ALBVENTALIN.CODALMACEN = 'T3' 
            OR ALBVENTALIN.CODALMACEN = 'T4')  
        GROUP BY 
            ALBVENTALIN.REFERENCIA, DESCRIPCION, TALLA, COLOR, PRECIOIVA
    """

        try:
            with get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, (fechaini_dt, fechafin_dt))
                    columns = [col[0] for col in cursor.description]
                    data = [dict(zip(columns, row)) for row in cursor.fetchall()]
            return (
                jsonify({"message": "Consulta ejecutada correctamente", "data": data}),
                200,
                cors_headers(),
            )

        except Exception as e:
            return (
                jsonify(
                    {
                        "message": "Ocurrió un error durante la ejecución",
                        "error": str(e),
                    }
                ),
                500,
                cors_headers(),
            )


@app.route("/stock", methods=["GET", "OPTIONS"])
def get_stock():
    if request.method == "OPTIONS":
        return "", 200, cors_headers()

    referencia = request.args.get("referencia")
    if not referencia:
        return (
            jsonify({"error": "Falta el parámetro 'referencia'"}),
            400,
            cors_headers(),
        )

    query = """
        SELECT 
            ALM.NOMBREALMACEN AS TIENDA,
            A.REFPROVEEDOR AS REFERENCIA, 
            A.DESCRIPCION,
            SUM(CASE WHEN S.TALLA = '18' THEN S.STOCK ELSE 0 END) AS T18,
            SUM(CASE WHEN S.TALLA = '19' THEN S.STOCK ELSE 0 END) AS T19,
            SUM(CASE WHEN S.TALLA = '20' THEN S.STOCK ELSE 0 END) AS T20,
            SUM(CASE WHEN S.TALLA = '21' THEN S.STOCK ELSE 0 END) AS T21,
            SUM(CASE WHEN S.TALLA = '22' THEN S.STOCK ELSE 0 END) AS T22,
            SUM(CASE WHEN S.TALLA = '23' THEN S.STOCK ELSE 0 END) AS T23,
            SUM(CASE WHEN S.TALLA = '24' THEN S.STOCK ELSE 0 END) AS T24,
            SUM(CASE WHEN S.TALLA = '25' THEN S.STOCK ELSE 0 END) AS T25,
            SUM(CASE WHEN S.TALLA = '26' THEN S.STOCK ELSE 0 END) AS T26,
            SUM(CASE WHEN S.TALLA = '27' THEN S.STOCK ELSE 0 END) AS T27,
            SUM(CASE WHEN S.TALLA = '28' THEN S.STOCK ELSE 0 END) AS T28,
            SUM(CASE WHEN S.TALLA = '29' THEN S.STOCK ELSE 0 END) AS T29,
            SUM(CASE WHEN S.TALLA = '30' THEN S.STOCK ELSE 0 END) AS T30,
            SUM(CASE WHEN S.TALLA = '31' THEN S.STOCK ELSE 0 END) AS T31,
            SUM(CASE WHEN S.TALLA = '32' THEN S.STOCK ELSE 0 END) AS T32,
            SUM(CASE WHEN S.TALLA = '33' THEN S.STOCK ELSE 0 END) AS T33,
            SUM(CASE WHEN S.TALLA = '34' THEN S.STOCK ELSE 0 END) AS T34,
            SUM(CASE WHEN S.TALLA = '35' THEN S.STOCK ELSE 0 END) AS T35,
            SUM(CASE WHEN S.TALLA = '36' THEN S.STOCK ELSE 0 END) AS T36,
            SUM(CASE WHEN S.TALLA = '37' THEN S.STOCK ELSE 0 END) AS T37,
            SUM(CASE WHEN S.TALLA = '38' THEN S.STOCK ELSE 0 END) AS T38,
            SUM(CASE WHEN S.TALLA = '39' THEN S.STOCK ELSE 0 END) AS T39,
            SUM(CASE WHEN S.TALLA = '40' THEN S.STOCK ELSE 0 END) AS T40,
            SUM(CASE WHEN S.TALLA = '41' THEN S.STOCK ELSE 0 END) AS T41,
            SUM(CASE WHEN S.TALLA = '42' THEN S.STOCK ELSE 0 END) AS T42,
            SUM(CASE WHEN S.TALLA = '43' THEN S.STOCK ELSE 0 END) AS T43,
            SUM(CASE WHEN S.TALLA = '44' THEN S.STOCK ELSE 0 END) AS T44,
            SUM(CASE WHEN S.TALLA = '45' THEN S.STOCK ELSE 0 END) AS T45,
            SUM(CASE WHEN S.TALLA = '46' THEN S.STOCK ELSE 0 END) AS T46,
            SUM(CASE WHEN S.TALLA = '47' THEN S.STOCK ELSE 0 END) AS T47,
            SUM(CASE WHEN S.TALLA = '48' THEN S.STOCK ELSE 0 END) AS T48,
            SUM(S.STOCK) AS TOTAL
        FROM ARTICULOS A
        LEFT JOIN ARTICULOSLIN ALIN ON A.CODARTICULO = ALIN.CODARTICULO
        LEFT JOIN STOCKS S ON ALIN.CODARTICULO = S.CODARTICULO AND ALIN.TALLA = S.TALLA AND ALIN.COLOR = S.COLOR
        LEFT JOIN ALMACEN ALM ON S.CODALMACEN = ALM.CODALMACEN
        LEFT JOIN REFERENCIASPROV RP ON A.REFPROVEEDOR = RP.REFPROVEEDOR
        WHERE A.REFPROVEEDOR = ? AND ALM.CODALMACEN IN ('T1', 'T2', 'T3', 'T4')
        GROUP BY 
            ALM.CODALMACEN, ALM.NOMBREALMACEN, A.REFPROVEEDOR, A.TEMPORADA, ALIN.CODARTICULO, ALIN.COLOR, A.DESCRIPCION
        ORDER BY REFERENCIA;
    """

    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (referencia,))
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            data = [dict(zip(columns, row)) for row in rows]

        return (
            jsonify({"message": "Consulta de stock realizada", "data_detail": data}),
            200,
            cors_headers(),
        )

    except Exception as e:
        return (
            jsonify({"message": "Error durante la consulta", "error": str(e)}),
            500,
            cors_headers(),
        )


@app.route("/historico", methods=["GET", "OPTIONS"])
def historico():
    print("📡 Recibida petición a /historico")

    if request.method == "OPTIONS":
        return ("", 200, cors_headers())

    referencia = request.args.get("referencia")
    if not referencia:
        return (
            jsonify({"message": "El parámetro 'referencia' es obligatorio"}),
            400,
            cors_headers(),
        )

    query = """
        SELECT 
            ALM.NOMBREALMACEN AS TIENDA,
            A.REFPROVEEDOR,
            A.DESCRIPCION,
            SUM(CASE WHEN AVL.TALLA = '18' THEN AVL.UNIDADESTOTAL ELSE 0 END) AS T18,
            SUM(CASE WHEN AVL.TALLA = '19' THEN AVL.UNIDADESTOTAL ELSE 0 END) AS T19,
            SUM(CASE WHEN AVL.TALLA = '20' THEN AVL.UNIDADESTOTAL ELSE 0 END) AS T20,
            SUM(CASE WHEN AVL.TALLA = '21' THEN AVL.UNIDADESTOTAL ELSE 0 END) AS T21,
            SUM(CASE WHEN AVL.TALLA = '22' THEN AVL.UNIDADESTOTAL ELSE 0 END) AS T22,
            SUM(CASE WHEN AVL.TALLA = '23' THEN AVL.UNIDADESTOTAL ELSE 0 END) AS T23,
            SUM(CASE WHEN AVL.TALLA = '24' THEN AVL.UNIDADESTOTAL ELSE 0 END) AS T24,
            SUM(CASE WHEN AVL.TALLA = '25' THEN AVL.UNIDADESTOTAL ELSE 0 END) AS T25,
            SUM(CASE WHEN AVL.TALLA = '26' THEN AVL.UNIDADESTOTAL ELSE 0 END) AS T26,
            SUM(CASE WHEN AVL.TALLA = '27' THEN AVL.UNIDADESTOTAL ELSE 0 END) AS T27,
            SUM(CASE WHEN AVL.TALLA = '28' THEN AVL.UNIDADESTOTAL ELSE 0 END) AS T28,
            SUM(CASE WHEN AVL.TALLA = '29' THEN AVL.UNIDADESTOTAL ELSE 0 END) AS T29,
            SUM(CASE WHEN AVL.TALLA = '30' THEN AVL.UNIDADESTOTAL ELSE 0 END) AS T30,
            SUM(CASE WHEN AVL.TALLA = '31' THEN AVL.UNIDADESTOTAL ELSE 0 END) AS T31,
            SUM(CASE WHEN AVL.TALLA = '32' THEN AVL.UNIDADESTOTAL ELSE 0 END) AS T32,
            SUM(CASE WHEN AVL.TALLA = '33' THEN AVL.UNIDADESTOTAL ELSE 0 END) AS T33,
            SUM(CASE WHEN AVL.TALLA = '34' THEN AVL.UNIDADESTOTAL ELSE 0 END) AS T34,
            SUM(CASE WHEN AVL.TALLA = '35' THEN AVL.UNIDADESTOTAL ELSE 0 END) AS T35,
            SUM(CASE WHEN AVL.TALLA = '36' THEN AVL.UNIDADESTOTAL ELSE 0 END) AS T36,
            SUM(CASE WHEN AVL.TALLA = '37' THEN AVL.UNIDADESTOTAL ELSE 0 END) AS T37,
            SUM(CASE WHEN AVL.TALLA = '38' THEN AVL.UNIDADESTOTAL ELSE 0 END) AS T38,
            SUM(CASE WHEN AVL.TALLA = '39' THEN AVL.UNIDADESTOTAL ELSE 0 END) AS T39,
            SUM(CASE WHEN AVL.TALLA = '40' THEN AVL.UNIDADESTOTAL ELSE 0 END) AS T40,
            SUM(CASE WHEN AVL.TALLA = '41' THEN AVL.UNIDADESTOTAL ELSE 0 END) AS T41,
            SUM(CASE WHEN AVL.TALLA = '42' THEN AVL.UNIDADESTOTAL ELSE 0 END) AS T42,
            SUM(CASE WHEN AVL.TALLA = '43' THEN AVL.UNIDADESTOTAL ELSE 0 END) AS T43,
            SUM(CASE WHEN AVL.TALLA = '44' THEN AVL.UNIDADESTOTAL ELSE 0 END) AS T44,
            SUM(CASE WHEN AVL.TALLA = '45' THEN AVL.UNIDADESTOTAL ELSE 0 END) AS T45,
            SUM(CASE WHEN AVL.TALLA = '46' THEN AVL.UNIDADESTOTAL ELSE 0 END) AS T46,
            SUM(CASE WHEN AVL.TALLA = '47' THEN AVL.UNIDADESTOTAL ELSE 0 END) AS T47,
            SUM(CASE WHEN AVL.TALLA = '48' THEN AVL.UNIDADESTOTAL ELSE 0 END) AS T48,
            SUM(AVL.UNIDADESTOTAL) AS TOTAL
        FROM ARTICULOS A
        LEFT JOIN ARTICULOSLIN ALIN ON A.CODARTICULO = ALIN.CODARTICULO
        LEFT JOIN ALBVENTALIN AVL ON ALIN.CODARTICULO = AVL.CODARTICULO AND ALIN.TALLA = AVL.TALLA AND ALIN.COLOR = AVL.COLOR
        LEFT JOIN ALMAC EN ALM ON AVL.CODALMACEN = ALM.CODALMACEN
        LEFT JOIN REFERENCIASPROV RP ON A.REFPROVEEDOR = RP.REFPROVEEDOR
        WHERE A.REFPROVEEDOR = ? AND ALM.CODALMACEN IN ('T1', 'T2', 'T3', 'T4')
        GROUP BY ALM.CODALMACEN, ALM.NOMBREALMACEN, A.REFPROVEEDOR, A.TEMPORADA, ALIN.CODARTICULO, ALIN.COLOR, A.DESCRIPCION
        ORDER BY A.REFPROVEEDOR
    """

    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (referencia,))
            rows = cursor.fetchall()
            columns = [column[0] for column in cursor.description]
            data_detail = [dict(zip(columns, row)) for row in rows]

        return (
            jsonify(
                {
                    "message": "Consulta ejecutada correctamente",
                    "data_detail": data_detail,
                }
            ),
            200,
            cors_headers(),
        )

    except Exception as e:
        print("❌ Error:", str(e))
        return (
            jsonify(
                {"message": "Ocurrió un error durante la ejecución", "error": str(e)}
            ),
            500,
            cors_headers(),
        )


@app.route("/existencias", methods=["GET", "OPTIONS"])
def get_existencias():
    if request.method == "OPTIONS":
        return "", 200, cors_headers()

    proveedor = request.args.get("proveedor")
    if not proveedor:
        return (
            jsonify({"message": "Falta el parámetro 'proveedor'"}),
            400,
            cors_headers(),
        )

    query = """
        SELECT 
            A.CODARTICULO,
            A.REFPROVEEDOR AS REFERENCIA, 
            A.DESCRIPCION,
            SUM(CASE WHEN S.TALLA = '18' THEN S.STOCK ELSE 0 END) AS T18,
            SUM(CASE WHEN S.TALLA = '19' THEN S.STOCK ELSE 0 END) AS T19,
            SUM(CASE WHEN S.TALLA = '20' THEN S.STOCK ELSE 0 END) AS T20,
            SUM(CASE WHEN S.TALLA = '21' THEN S.STOCK ELSE 0 END) AS T21,
            SUM(CASE WHEN S.TALLA = '22' THEN S.STOCK ELSE 0 END) AS T22,
            SUM(CASE WHEN S.TALLA = '23' THEN S.STOCK ELSE 0 END) AS T23,
            SUM(CASE WHEN S.TALLA = '24' THEN S.STOCK ELSE 0 END) AS T24,
            SUM(CASE WHEN S.TALLA = '25' THEN S.STOCK ELSE 0 END) AS T25,
            SUM(CASE WHEN S.TALLA = '26' THEN S.STOCK ELSE 0 END) AS T26,
            SUM(CASE WHEN S.TALLA = '27' THEN S.STOCK ELSE 0 END) AS T27,
            SUM(CASE WHEN S.TALLA = '28' THEN S.STOCK ELSE 0 END) AS T28,
            SUM(CASE WHEN S.TALLA = '29' THEN S.STOCK ELSE 0 END) AS T29,
            SUM(CASE WHEN S.TALLA = '30' THEN S.STOCK ELSE 0 END) AS T30,
            SUM(CASE WHEN S.TALLA = '31' THEN S.STOCK ELSE 0 END) AS T31,
            SUM(CASE WHEN S.TALLA = '32' THEN S.STOCK ELSE 0 END) AS T32,
            SUM(CASE WHEN S.TALLA = '33' THEN S.STOCK ELSE 0 END) AS T33,
            SUM(CASE WHEN S.TALLA = '34' THEN S.STOCK ELSE 0 END) AS T34,
            SUM(CASE WHEN S.TALLA = '35' THEN S.STOCK ELSE 0 END) AS T35,
            SUM(CASE WHEN S.TALLA = '36' THEN S.STOCK ELSE 0 END) AS T36,
            SUM(CASE WHEN S.TALLA = '37' THEN S.STOCK ELSE 0 END) AS T37,
            SUM(CASE WHEN S.TALLA = '38' THEN S.STOCK ELSE 0 END) AS T38,
            SUM(CASE WHEN S.TALLA = '39' THEN S.STOCK ELSE 0 END) AS T39,
            SUM(CASE WHEN S.TALLA = '40' THEN S.STOCK ELSE 0 END) AS T40,
            SUM(CASE WHEN S.TALLA = '41' THEN S.STOCK ELSE 0 END) AS T41,
            SUM(CASE WHEN S.TALLA = '42' THEN S.STOCK ELSE 0 END) AS T42,
            SUM(CASE WHEN S.TALLA = '43' THEN S.STOCK ELSE 0 END) AS T43,
            SUM(CASE WHEN S.TALLA = '44' THEN S.STOCK ELSE 0 END) AS T44,
            SUM(CASE WHEN S.TALLA = '45' THEN S.STOCK ELSE 0 END) AS T45,
            SUM(CASE WHEN S.TALLA = '46' THEN S.STOCK ELSE 0 END) AS T46,
            SUM(CASE WHEN S.TALLA = '47' THEN S.STOCK ELSE 0 END) AS T47,
            SUM(CASE WHEN S.TALLA = '48' THEN S.STOCK ELSE 0 END) AS T48,
            SUM(S.STOCK) AS TOTAL,
            MAX(PV.PNETO) AS PVP,
            A.TEMPORADA,
            PR.NOMPROVEEDOR
        FROM ARTICULOS A
        LEFT JOIN STOCKS S ON A.CODARTICULO = S.CODARTICULO
        LEFT JOIN REFERENCIASPROV RP ON A.REFPROVEEDOR = RP.REFPROVEEDOR
        LEFT JOIN PROVEEDORES PR ON RP.CODPROVEEDOR = PR.CODPROVEEDOR
        LEFT JOIN PRECIOSVENTA PV ON S.CODARTICULO = PV.CODARTICULO AND S.TALLA = PV.TALLA AND S.COLOR = PV.COLOR
        WHERE LEFT(PR.NOMPROVEEDOR, 3) = ?
          AND PV.IDTARIFAV = 1
        GROUP BY 
            A.CODARTICULO,
            A.REFPROVEEDOR,
            A.DESCRIPCION,
            A.TEMPORADA,
            PR.NOMPROVEEDOR
        ORDER BY A.REFPROVEEDOR
    """

    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (proveedor,))
                columns = [col[0] for col in cursor.description]
                data = [dict(zip(columns, row)) for row in cursor.fetchall()]

        return (
            jsonify({"message": "Consulta de existencias ejecutada", "data": data}),
            200,
            cors_headers(),
        )

    except Exception as e:
        traceback.print_exc()
        return (
            jsonify({"message": "Error al obtener existencias", "error": str(e)}),
            500,
            cors_headers(),
        )


@app.route("/cuadrobeneficios", methods=["GET", "OPTIONS"])
def cuadro_beneficios():
    if request.method == "OPTIONS":
        return "", 200, cors_headers()

    fechaini = request.args.get("fechaini")
    fechafin = request.args.get("fechafin")
    temporadas = request.args.get("temporadas")  # puede ser None o tipo 'V25,V14'

    if not fechaini or not fechafin:
        return (
            jsonify({"error": "Faltan los parámetros 'fechaini' y/o 'fechafin'"}),
            400,
            cors_headers(),
        )

    query = """
    SELECT 
    ISNULL(c.PROVEEDOR, v.PROVEEDOR) AS PROVEEDOR,
    c.UDS AS UNIDADESCOMPRADAS,
    c.VALOR AS VALORCOMPRA,
    c.PMC AS PMC,
    v.UDS AS UNIDADESVENDIDAS,
    v.VALOR AS VALORVENTA,
    v.PMV AS PMV,
    s.STOCK AS STOCK,
    s.VALORACION AS VALORACION,
    t.TEMPORADAS,
    v.COSTO_VTA AS COSTO_VTA
FROM (
    SELECT 
        P.NOMPROVEEDOR AS PROVEEDOR, 
        SUM(L.UNIDADESTOTAL) AS UDS, 
        ROUND(SUM(L.TOTAL), 2) AS VALOR,
        ROUND(SUM(L.TOTAL) / SUM(L.UNIDADESTOTAL), 2) AS PMC
    FROM PROVEEDORES P
    INNER JOIN ALBCOMPRACAB C ON C.CODPROVEEDOR = P.CODPROVEEDOR
    INNER JOIN ALBCOMPRALIN L ON C.NUMSERIE = L.NUMSERIE AND C.NUMALBARAN = L.NUMALBARAN
    WHERE 
        L.UNIDADESTOTAL IS NOT NULL AND L.UNIDADESTOTAL <> 0
        AND L.TOTAL IS NOT NULL AND L.TOTAL <> 0
        AND C.FECHAALBARAN BETWEEN ? AND ?
        AND P.CODPROVEEDOR <> 10000
    GROUP BY P.NOMPROVEEDOR
) AS c

FULL OUTER JOIN (
    SELECT 
    P.NOMPROVEEDOR AS PROVEEDOR,
    SUM(ALBVENTALIN.UNIDADESTOTAL) AS UDS, 
    ROUND(SUM(ALBVENTALIN.TOTAL), 2) AS VALOR,
    ROUND(
        CASE 
            WHEN SUM(ALBVENTALIN.UNIDADESTOTAL) = 0 THEN NULL 
            ELSE SUM(ALBVENTALIN.TOTAL) / SUM(ALBVENTALIN.UNIDADESTOTAL)
        END, 2) AS PMV,
    ROUND(SUM(
        ALBVENTALIN.UNIDADESTOTAL * 
        COALESCE(ULTIMA_COMPRA.PRECIO, ALIN.ULTIMOCOSTE)
    ), 2) AS COSTO_VTA
FROM PROVEEDORES P
INNER JOIN REFERENCIASPROV ON REFERENCIASPROV.CODPROVEEDOR = P.CODPROVEEDOR
INNER JOIN ARTICULOS A ON A.REFPROVEEDOR = REFERENCIASPROV.REFPROVEEDOR
INNER JOIN ALBVENTALIN ON A.CODARTICULO = ALBVENTALIN.CODARTICULO
INNER JOIN ARTICULOSLIN ALIN ON A.CODARTICULO = ALIN.CODARTICULO 
    AND ALBVENTALIN.TALLA = ALIN.TALLA 
    AND ALBVENTALIN.COLOR = ALIN.COLOR
INNER JOIN ALBVENTACAB ON ALBVENTALIN.NUMSERIE = ALBVENTACAB.NUMSERIE 
    AND ALBVENTALIN.NUMALBARAN = ALBVENTACAB.NUMALBARAN

-- ÚLTIMA COMPRA POR NUMALBARAN PARA ALMACÉN T0
OUTER APPLY (
    SELECT TOP 1 ACL.PRECIO
    FROM ALBCOMPRALIN ACL
    WHERE 
        ACL.CODARTICULO = A.CODARTICULO
        AND ACL.TALLA = ALBVENTALIN.TALLA
        AND ACL.COLOR = ALBVENTALIN.COLOR
        AND ACL.CODALMACEN = 'T0'
    ORDER BY ACL.NUMALBARAN DESC
) AS ULTIMA_COMPRA

WHERE 
    ALBVENTALIN.UNIDADESTOTAL IS NOT NULL AND ALBVENTALIN.UNIDADESTOTAL <> 0
    AND ALBVENTALIN.TOTAL IS NOT NULL 
    AND (ALBVENTACAB.FECHA BETWEEN ? AND ?) 
    AND ALBVENTACAB.NUMSERIE LIKE 'Z0%'
    AND P.CODPROVEEDOR <> 10000
	    AND (
            ? IS NULL
            OR A.TEMPORADA IN (SELECT value FROM STRING_SPLIT(?, ','))
        )
GROUP BY P.NOMPROVEEDOR
) AS v ON c.PROVEEDOR = v.PROVEEDOR

LEFT JOIN (
    SELECT 
        P.NOMPROVEEDOR AS PROVEEDOR,
        SUM(S.STOCK) AS STOCK,
        ROUND(SUM(
        S.STOCK * 
        COALESCE(ULTIMA_COMPRA.PRECIO, ALIN.ULTIMOCOSTE)
    ), 2) AS VALORACION
    FROM PROVEEDORES P
    INNER JOIN REFERENCIASPROV R ON R.CODPROVEEDOR = P.CODPROVEEDOR
    INNER JOIN ARTICULOS A ON A.REFPROVEEDOR = R.REFPROVEEDOR
    INNER JOIN STOCKS S ON A.CODARTICULO = S.CODARTICULO
    INNER JOIN ARTICULOSLIN ALIN ON S.CODARTICULO = ALIN.CODARTICULO AND S.TALLA = ALIN.TALLA AND S.COLOR = ALIN.COLOR

    -- ÚLTIMA COMPRA POR NUMALBARAN PARA ALMACÉN T0
OUTER APPLY (
    SELECT TOP 1 ACL.PRECIO
    FROM ALBCOMPRALIN ACL
    WHERE 
        ACL.CODARTICULO = A.CODARTICULO
        AND ACL.TALLA = ALIN.TALLA
        AND ACL.COLOR = ALIN.COLOR
        AND ACL.CODALMACEN = 'T0'
    ORDER BY ACL.NUMALBARAN DESC
) AS ULTIMA_COMPRA

    GROUP BY P.NOMPROVEEDOR
) AS s ON s.PROVEEDOR = ISNULL(c.PROVEEDOR, v.PROVEEDOR)

LEFT JOIN (
    SELECT 
        P.NOMPROVEEDOR AS PROVEEDOR,
        STUFF((
            SELECT DISTINCT ',' + A2.TEMPORADA
            FROM REFERENCIASPROV R2
            INNER JOIN ARTICULOS A2 ON A2.REFPROVEEDOR = R2.REFPROVEEDOR
            WHERE R2.CODPROVEEDOR = P.CODPROVEEDOR
                AND A2.TEMPORADA IS NOT NULL
            FOR XML PATH(''), TYPE).value('.', 'NVARCHAR(MAX)'), 1, 1, ''
        ) AS TEMPORADAS
    FROM PROVEEDORES P
) AS t ON t.PROVEEDOR = ISNULL(c.PROVEEDOR, v.PROVEEDOR)

WHERE c.PROVEEDOR IS NOT NULL OR v.PROVEEDOR IS NOT NULL
ORDER BY PROVEEDOR;
    """

    parameters = [fechaini, fechafin, fechaini, fechafin, temporadas, temporadas]

    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, parameters)
            rows = cursor.fetchall()
            columns = [col[0] for col in cursor.description]
            data = [dict(zip(columns, row)) for row in rows]

        return (
            jsonify({"message": "Consulta ejecutada correctamente", "data": data}),
            200,
            cors_headers(),
        )

    except Exception as e:
        print("❌ Error en /beneficios:", str(e))
        return (
            jsonify({"message": "Error al ejecutar la consulta", "error": str(e)}),
            500,
            cors_headers(),
        )


@app.route("/historico-stocks", methods=["GET", "OPTIONS"])
def historico_stocks():
    if request.method == "OPTIONS":
        return "", 200, cors_headers()

    referencia = request.args.get("referencia")
    if not referencia:
        return (
            jsonify({"error": "Falta el parámetro 'referencia'"}),
            400,
            cors_headers(),
        )

    # Escapamos comillas simples por seguridad
    referencia_sql = referencia.replace("'", "''")

    query = f"""
    DECLARE @cols NVARCHAR(MAX), @sql NVARCHAR(MAX);

    SELECT @cols = STRING_AGG(QUOTENAME(TALLA), ',')
    FROM (
        SELECT DISTINCT TALLA
        FROM (
            SELECT ALBVENTALIN.TALLA
            FROM ARTICULOS
            INNER JOIN ALBVENTALIN ON ARTICULOS.CODARTICULO = ALBVENTALIN.CODARTICULO
            INNER JOIN ALBVENTACAB ON ALBVENTALIN.NUMSERIE = ALBVENTACAB.NUMSERIE AND ALBVENTALIN.NUMALBARAN = ALBVENTACAB.NUMALBARAN
            WHERE ARTICULOS.REFPROVEEDOR = '{referencia_sql}' AND ALBVENTALIN.CODALMACEN <> 'T0' AND ALBVENTALIN.UNIDADESTOTAL > 0

            UNION

            SELECT ALBCOMPRALIN.TALLA
            FROM ARTICULOS
            INNER JOIN ALBCOMPRALIN ON ARTICULOS.CODARTICULO = ALBCOMPRALIN.CODARTICULO
            INNER JOIN ALBCOMPRACAB ON ALBCOMPRALIN.NUMSERIE = ALBCOMPRACAB.NUMSERIE AND ALBCOMPRALIN.NUMALBARAN = ALBCOMPRACAB.NUMALBARAN
            WHERE ARTICULOS.REFPROVEEDOR = '{referencia_sql}' AND ALBCOMPRALIN.CODALMACEN <> 'T0' AND ALBCOMPRALIN.UNIDADESTOTAL > 0

            UNION

            SELECT MOVIMENTS.TALLA
            FROM ARTICULOS
            INNER JOIN MOVIMENTS ON ARTICULOS.CODARTICULO = MOVIMENTS.CODARTICULO
            WHERE ARTICULOS.REFPROVEEDOR = '{referencia_sql}' AND MOVIMENTS.UNIDADES > 0
        ) AS TALLAS_VALIDAS
        WHERE TALLA IS NOT NULL
    ) AS ListaFinalTallas;

    SET @sql = '
    SELECT 
        MOVIMIENTO,
        TIENDA,
        FORMAT(FECHA, ''dd/MM/yyyy'') AS FECHA,
        REFPROVEEDOR,
        DESCRIPCION,
        COLOR,
        ' + @cols + '
    FROM (
        SELECT 
            MOVIMIENTO,
            TIENDA,
            FECHA,
            REFPROVEEDOR,
            DESCRIPCION,
            COLOR,
            TALLA,
            UNIDADESTOTAL
        FROM (
            SELECT 
                ALBVENTACAB.FECHA,
                ARTICULOS.REFPROVEEDOR,
                ARTICULOS.DESCRIPCION,
                ALBVENTALIN.TALLA,
                ALBVENTALIN.COLOR,
                ALMACEN.NOMBREALMACEN AS TIENDA,
                ''VENTA'' AS MOVIMIENTO,
                ALBVENTALIN.UNIDADESTOTAL
            FROM ARTICULOS
            INNER JOIN ALBVENTALIN ON ARTICULOS.CODARTICULO = ALBVENTALIN.CODARTICULO
            INNER JOIN ALBVENTACAB ON ALBVENTALIN.NUMSERIE = ALBVENTACAB.NUMSERIE AND ALBVENTALIN.NUMALBARAN = ALBVENTACAB.NUMALBARAN
            INNER JOIN ALMACEN ON ALBVENTALIN.CODALMACEN = ALMACEN.CODALMACEN
            WHERE ARTICULOS.REFPROVEEDOR = ''{referencia_sql}'' AND ALBVENTALIN.CODALMACEN <> ''T0''

            UNION ALL

            SELECT 
                ALBCOMPRACAB.FECHAALBARAN,
                ARTICULOS.REFPROVEEDOR,
                ARTICULOS.DESCRIPCION,
                ALBCOMPRALIN.TALLA,
                ALBCOMPRALIN.COLOR,
                ALMACEN.NOMBREALMACEN,
                ''RECEPCIÓN DE MERCANCÍA'',
                ALBCOMPRALIN.UNIDADESTOTAL
            FROM ARTICULOS
            INNER JOIN ALBCOMPRALIN ON ARTICULOS.CODARTICULO = ALBCOMPRALIN.CODARTICULO
            INNER JOIN ALBCOMPRACAB ON ALBCOMPRALIN.NUMSERIE = ALBCOMPRACAB.NUMSERIE AND ALBCOMPRALIN.NUMALBARAN = ALBCOMPRACAB.NUMALBARAN
            INNER JOIN ALMACEN ON ALBCOMPRALIN.CODALMACEN = ALMACEN.CODALMACEN
            WHERE ARTICULOS.REFPROVEEDOR = ''{referencia_sql}'' AND ALBCOMPRALIN.CODALMACEN <> ''T0''

            UNION ALL

            SELECT 
                MOVIMENTS.FECHA,
                ARTICULOS.REFPROVEEDOR,
                ARTICULOS.DESCRIPCION,
                MOVIMENTS.TALLA,
                MOVIMENTS.COLOR,
                ALMACEN.NOMBREALMACEN,
                CASE 
                    WHEN MOVIMENTS.CODALMACENDESTINO IS NULL OR MOVIMENTS.CODALMACENDESTINO = '''' THEN ''REGULARIZACIÓN''
                    ELSE ''TRASPASO DE '' + MOVIMENTS.CODALMACENORIGEN + '' - '' + MOVIMENTS.CODALMACENDESTINO 
                END,
                MOVIMENTS.UNIDADES
            FROM ARTICULOS
            INNER JOIN MOVIMENTS ON ARTICULOS.CODARTICULO = MOVIMENTS.CODARTICULO
            INNER JOIN ALMACEN ON MOVIMENTS.CODALMACENORIGEN = ALMACEN.CODALMACEN
            WHERE ARTICULOS.REFPROVEEDOR = ''{referencia_sql}''
        ) AS BaseDatos
    ) AS SourceTable
    PIVOT (
        SUM(UNIDADESTOTAL)
        FOR TALLA IN (' + @cols + ')
    ) AS PivotTable
    ORDER BY MOVIMIENTO, TIENDA, FECHA ASC;
    ';

    EXEC sp_executesql @sql;
    """

    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()
            data = [dict(zip(columns, row)) for row in rows]

        return (
            jsonify(
                {"message": "Histórico de stock obtenido correctamente", "data": data}
            ),
            200,
            cors_headers(),
        )

    except Exception as e:
        print("❌ Error en /historico-stock:", str(e))
        return (
            jsonify({"message": "Error al ejecutar la consulta", "error": str(e)}),
            500,
            cors_headers(),
        )


@app.route("/consulta", methods=["GET", "OPTIONS"])
def consulta_general():
    if request.method == "OPTIONS":
        return "", 200, cors_headers()

    referencia = request.args.get("referencia")
    if not referencia:
        return (
            jsonify({"error": "Falta el parámetro 'referencia'"}),
            400,
            cors_headers(),
        )

    try:
        with get_connection() as conn:
            cursor = conn.cursor()

            # Obtener STOCK
            cursor.execute(
                """
            -- Paso 1: Recibes un único parámetro
DECLARE @parametro NVARCHAR(50) = ?;  -- Puede ser REFPROVEEDOR o CODBARRAS
DECLARE @codArticulo NVARCHAR(50); -- Este es el artículo completo (no la talla específica)

-- Paso 2: Intentar buscar por REFPROVEEDOR directamente
SELECT TOP 1 @codArticulo = CODARTICULO
FROM ARTICULOS
WHERE REFPROVEEDOR = @parametro;

-- Paso 3: Si no lo encuentra, buscar por CODBARRAS
IF @codArticulo IS NULL
BEGIN
    SELECT TOP 1 @codArticulo = AL.CODARTICULO
    FROM ARTICULOSLIN AL
    WHERE AL.CODBARRAS = @parametro;
END

-- Paso 4: Consultar TODAS las tallas y colores del artículo completo
SELECT 
    ALM.NOMBREALMACEN AS TIENDA,
    A.REFPROVEEDOR AS REFERENCIA,
    A.DESCRIPCION,
    SUM(CASE WHEN S.TALLA = '18' THEN S.STOCK ELSE 0 END) AS T18,
    SUM(CASE WHEN S.TALLA = '19' THEN S.STOCK ELSE 0 END) AS T19,
    SUM(CASE WHEN S.TALLA = '20' THEN S.STOCK ELSE 0 END) AS T20,
    SUM(CASE WHEN S.TALLA = '21' THEN S.STOCK ELSE 0 END) AS T21,
    SUM(CASE WHEN S.TALLA = '22' THEN S.STOCK ELSE 0 END) AS T22,
    SUM(CASE WHEN S.TALLA = '23' THEN S.STOCK ELSE 0 END) AS T23,
    SUM(CASE WHEN S.TALLA = '24' THEN S.STOCK ELSE 0 END) AS T24,
    SUM(CASE WHEN S.TALLA = '25' THEN S.STOCK ELSE 0 END) AS T25,
    SUM(CASE WHEN S.TALLA = '26' THEN S.STOCK ELSE 0 END) AS T26,
    SUM(CASE WHEN S.TALLA = '27' THEN S.STOCK ELSE 0 END) AS T27,
    SUM(CASE WHEN S.TALLA = '28' THEN S.STOCK ELSE 0 END) AS T28,
    SUM(CASE WHEN S.TALLA = '29' THEN S.STOCK ELSE 0 END) AS T29,
    SUM(CASE WHEN S.TALLA = '30' THEN S.STOCK ELSE 0 END) AS T30,
    SUM(CASE WHEN S.TALLA = '31' THEN S.STOCK ELSE 0 END) AS T31,
    SUM(CASE WHEN S.TALLA = '32' THEN S.STOCK ELSE 0 END) AS T32,
    SUM(CASE WHEN S.TALLA = '33' THEN S.STOCK ELSE 0 END) AS T33,
    SUM(CASE WHEN S.TALLA = '34' THEN S.STOCK ELSE 0 END) AS T34,
    SUM(CASE WHEN S.TALLA = '35' THEN S.STOCK ELSE 0 END) AS T35,
    SUM(CASE WHEN S.TALLA = '36' THEN S.STOCK ELSE 0 END) AS T36,
    SUM(CASE WHEN S.TALLA = '37' THEN S.STOCK ELSE 0 END) AS T37,
    SUM(CASE WHEN S.TALLA = '38' THEN S.STOCK ELSE 0 END) AS T38,
    SUM(CASE WHEN S.TALLA = '39' THEN S.STOCK ELSE 0 END) AS T39,
    SUM(CASE WHEN S.TALLA = '40' THEN S.STOCK ELSE 0 END) AS T40,
    SUM(CASE WHEN S.TALLA = '41' THEN S.STOCK ELSE 0 END) AS T41,
    SUM(CASE WHEN S.TALLA = '42' THEN S.STOCK ELSE 0 END) AS T42,
    SUM(CASE WHEN S.TALLA = '43' THEN S.STOCK ELSE 0 END) AS T43,
    SUM(CASE WHEN S.TALLA = '44' THEN S.STOCK ELSE 0 END) AS T44,
    SUM(CASE WHEN S.TALLA = '45' THEN S.STOCK ELSE 0 END) AS T45,
    SUM(CASE WHEN S.TALLA = '46' THEN S.STOCK ELSE 0 END) AS T46,
    SUM(CASE WHEN S.TALLA = '47' THEN S.STOCK ELSE 0 END) AS T47,
    SUM(CASE WHEN S.TALLA = '48' THEN S.STOCK ELSE 0 END) AS T48,
    SUM(S.STOCK) AS TOTAL
FROM STOCKS S
INNER JOIN ARTICULOS A ON A.CODARTICULO = S.CODARTICULO
INNER JOIN ALMACEN ALM ON S.CODALMACEN = ALM.CODALMACEN
WHERE S.CODARTICULO = @codArticulo
  AND ALM.CODALMACEN IN ('T1', 'T2', 'T3', 'T4')
GROUP BY 
    ALM.CODALMACEN, ALM.NOMBREALMACEN, A.REFPROVEEDOR, A.DESCRIPCION
ORDER BY REFERENCIA;
            """,
                (referencia),
            )
            stock_columns = [col[0] for col in cursor.description]
            stock_data = [dict(zip(stock_columns, row)) for row in cursor.fetchall()]

            # Obtener HISTÓRICO
            cursor.execute(
                """
            -- 1. Recibe un único parámetro
DECLARE @parametro NVARCHAR(50) = ?;  -- Puede ser REFPROVEEDOR o CODBARRAS
DECLARE @codArticulo NVARCHAR(50);

-- 2. Buscar CODARTICULO directamente desde REFPROVEEDOR
SELECT TOP 1 @codArticulo = CODARTICULO
FROM ARTICULOS
WHERE REFPROVEEDOR = @parametro;

-- 3. Si no lo encuentra, buscarlo desde el CODBARRAS
IF @codArticulo IS NULL
BEGIN
    SELECT TOP 1 @codArticulo = AL.CODARTICULO
    FROM ARTICULOSLIN AL
    WHERE AL.CODBARRAS = @parametro;
END;

-- 4. Consulta principal basada en CODARTICULO completo
SELECT 
    ALM.NOMBREALMACEN AS TIENDA,
    A.REFPROVEEDOR,
    A.DESCRIPCION,
    SUM(CASE WHEN AVL.TALLA = '18' THEN AVL.UNIDADESTOTAL ELSE 0 END) AS T18,
    SUM(CASE WHEN AVL.TALLA = '19' THEN AVL.UNIDADESTOTAL ELSE 0 END) AS T19,
    SUM(CASE WHEN AVL.TALLA = '20' THEN AVL.UNIDADESTOTAL ELSE 0 END) AS T20,
    SUM(CASE WHEN AVL.TALLA = '21' THEN AVL.UNIDADESTOTAL ELSE 0 END) AS T21,
    SUM(CASE WHEN AVL.TALLA = '22' THEN AVL.UNIDADESTOTAL ELSE 0 END) AS T22,
    SUM(CASE WHEN AVL.TALLA = '23' THEN AVL.UNIDADESTOTAL ELSE 0 END) AS T23,
    SUM(CASE WHEN AVL.TALLA = '24' THEN AVL.UNIDADESTOTAL ELSE 0 END) AS T24,
    SUM(CASE WHEN AVL.TALLA = '25' THEN AVL.UNIDADESTOTAL ELSE 0 END) AS T25,
    SUM(CASE WHEN AVL.TALLA = '26' THEN AVL.UNIDADESTOTAL ELSE 0 END) AS T26,
    SUM(CASE WHEN AVL.TALLA = '27' THEN AVL.UNIDADESTOTAL ELSE 0 END) AS T27,
    SUM(CASE WHEN AVL.TALLA = '28' THEN AVL.UNIDADESTOTAL ELSE 0 END) AS T28,
    SUM(CASE WHEN AVL.TALLA = '29' THEN AVL.UNIDADESTOTAL ELSE 0 END) AS T29,
    SUM(CASE WHEN AVL.TALLA = '30' THEN AVL.UNIDADESTOTAL ELSE 0 END) AS T30,
    SUM(CASE WHEN AVL.TALLA = '31' THEN AVL.UNIDADESTOTAL ELSE 0 END) AS T31,
    SUM(CASE WHEN AVL.TALLA = '32' THEN AVL.UNIDADESTOTAL ELSE 0 END) AS T32,
    SUM(CASE WHEN AVL.TALLA = '33' THEN AVL.UNIDADESTOTAL ELSE 0 END) AS T33,
    SUM(CASE WHEN AVL.TALLA = '34' THEN AVL.UNIDADESTOTAL ELSE 0 END) AS T34,
    SUM(CASE WHEN AVL.TALLA = '35' THEN AVL.UNIDADESTOTAL ELSE 0 END) AS T35,
    SUM(CASE WHEN AVL.TALLA = '36' THEN AVL.UNIDADESTOTAL ELSE 0 END) AS T36,
    SUM(CASE WHEN AVL.TALLA = '37' THEN AVL.UNIDADESTOTAL ELSE 0 END) AS T37,
    SUM(CASE WHEN AVL.TALLA = '38' THEN AVL.UNIDADESTOTAL ELSE 0 END) AS T38,
    SUM(CASE WHEN AVL.TALLA = '39' THEN AVL.UNIDADESTOTAL ELSE 0 END) AS T39,
    SUM(CASE WHEN AVL.TALLA = '40' THEN AVL.UNIDADESTOTAL ELSE 0 END) AS T40,
    SUM(CASE WHEN AVL.TALLA = '41' THEN AVL.UNIDADESTOTAL ELSE 0 END) AS T41,
    SUM(CASE WHEN AVL.TALLA = '42' THEN AVL.UNIDADESTOTAL ELSE 0 END) AS T42,
    SUM(CASE WHEN AVL.TALLA = '43' THEN AVL.UNIDADESTOTAL ELSE 0 END) AS T43,
    SUM(CASE WHEN AVL.TALLA = '44' THEN AVL.UNIDADESTOTAL ELSE 0 END) AS T44,
    SUM(CASE WHEN AVL.TALLA = '45' THEN AVL.UNIDADESTOTAL ELSE 0 END) AS T45,
    SUM(CASE WHEN AVL.TALLA = '46' THEN AVL.UNIDADESTOTAL ELSE 0 END) AS T46,
    SUM(CASE WHEN AVL.TALLA = '47' THEN AVL.UNIDADESTOTAL ELSE 0 END) AS T47,
    SUM(CASE WHEN AVL.TALLA = '48' THEN AVL.UNIDADESTOTAL ELSE 0 END) AS T48,
    SUM(AVL.UNIDADESTOTAL) AS TOTAL
FROM ARTICULOS A
INNER JOIN ALBVENTALIN AVL ON A.CODARTICULO = AVL.CODARTICULO
INNER JOIN ALMACEN ALM ON AVL.CODALMACEN = ALM.CODALMACEN
WHERE A.CODARTICULO = @codArticulo
  AND ALM.CODALMACEN IN ('T1', 'T2', 'T3', 'T4')
GROUP BY 
    ALM.CODALMACEN, ALM.NOMBREALMACEN, A.REFPROVEEDOR, A.DESCRIPCION
ORDER BY A.REFPROVEEDOR;

            """,
                (referencia,),
            )
            historico_columns = [col[0] for col in cursor.description]
            historico_data = [
                dict(zip(historico_columns, row)) for row in cursor.fetchall()
            ]

        return (
            jsonify(
                {
                    "message": "Consulta combinada completada",
                    "stock": stock_data,
                    "historico": historico_data,
                }
            ),
            200,
            cors_headers(),
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500, cors_headers()


@app.route("/cuadrobeneficiostemporadas", methods=["GET", "OPTIONS"])
def cuadro_beneficios_temporadas():
    if request.method == "OPTIONS":
        return "", 200, cors_headers()

    fechaini = request.args.get("fechaini")
    fechafin = request.args.get("fechafin")
    temporadas = request.args.get("temporadas")  # puede ser None o tipo 'V25,V14'

    if not fechaini or not fechafin:
        return (
            jsonify({"error": "Faltan los parámetros 'fechaini' y/o 'fechafin'"}),
            400,
            cors_headers(),
        )

    query = """
    SELECT 
    ISNULL(c.TEMPORADA, v.TEMPORADA) AS TEMPORADA,
    c.UDS AS UNIDADESCOMPRADAS,
    c.VALOR AS VALORCOMPRA,
    c.PMC AS PMC,
    v.UDS AS UNIDADESVENDIDAS,
    v.VALOR AS VALORVENTA,
    v.PMV AS PMV,
    s.STOCK AS STOCK,
    s.VALORACION AS VALORACION,
    v.COSTO_VTA AS COSTO_VTA
FROM (
    SELECT 
        A.TEMPORADA AS TEMPORADA, 
        SUM(L.UNIDADESTOTAL) AS UDS, 
        ROUND(SUM(L.TOTAL), 2) AS VALOR,
        ROUND(SUM(L.TOTAL) / SUM(L.UNIDADESTOTAL), 2) AS PMC
    FROM PROVEEDORES P
    INNER JOIN ALBCOMPRACAB C ON C.CODPROVEEDOR = P.CODPROVEEDOR
    INNER JOIN ALBCOMPRALIN L ON C.NUMSERIE = L.NUMSERIE AND C.NUMALBARAN = L.NUMALBARAN
	INNER JOIN ARTICULOS A ON L.CODARTICULO = A.CODARTICULO
    WHERE 
        L.UNIDADESTOTAL IS NOT NULL AND L.UNIDADESTOTAL <> 0
        AND L.TOTAL IS NOT NULL AND L.TOTAL <> 0
        AND C.FECHAALBARAN BETWEEN ? AND ?
        AND P.CODPROVEEDOR <> 10000
    GROUP BY A.TEMPORADA
) AS c

FULL OUTER JOIN (
    SELECT 
        A.TEMPORADA AS TEMPORADA,
        SUM(ALBVENTALIN.UNIDADESTOTAL) AS UDS, 
        ROUND(SUM(ALBVENTALIN.TOTAL), 2) AS VALOR,
        ROUND(
            CASE 
                WHEN SUM(ALBVENTALIN.UNIDADESTOTAL) = 0 THEN NULL 
                ELSE SUM(ALBVENTALIN.TOTAL) / SUM(ALBVENTALIN.UNIDADESTOTAL)
            END, 2) AS PMV,
        ROUND(SUM(
            ALBVENTALIN.UNIDADESTOTAL * 
            COALESCE(ULTIMA_COMPRA.PRECIO, ALIN.ULTIMOCOSTE)
        ), 2) AS COSTO_VTA
    FROM PROVEEDORES P
    INNER JOIN REFERENCIASPROV ON REFERENCIASPROV.CODPROVEEDOR = P.CODPROVEEDOR
    INNER JOIN ARTICULOS A ON A.REFPROVEEDOR = REFERENCIASPROV.REFPROVEEDOR
    INNER JOIN ALBVENTALIN ON A.CODARTICULO = ALBVENTALIN.CODARTICULO
    INNER JOIN ARTICULOSLIN ALIN ON A.CODARTICULO = ALIN.CODARTICULO AND ALBVENTALIN.TALLA = ALIN.TALLA AND ALBVENTALIN.COLOR = ALIN.COLOR
    INNER JOIN ALBVENTACAB ON ALBVENTALIN.NUMSERIE = ALBVENTACAB.NUMSERIE 
        AND ALBVENTALIN.NUMALBARAN = ALBVENTACAB.NUMALBARAN
    
    -- ÚLTIMA COMPRA POR NUMALBARAN PARA ALMACÉN T0
    OUTER APPLY (
        SELECT TOP 1 ACL.PRECIO
        FROM ALBCOMPRALIN ACL
        WHERE 
            ACL.CODARTICULO = A.CODARTICULO
            AND ACL.TALLA = ALBVENTALIN.TALLA
            AND ACL.COLOR = ALBVENTALIN.COLOR
            AND ACL.CODALMACEN = 'T0'
        ORDER BY ACL.NUMALBARAN DESC
    ) AS ULTIMA_COMPRA

    WHERE 
        ALBVENTALIN.UNIDADESTOTAL IS NOT NULL AND ALBVENTALIN.UNIDADESTOTAL <> 0
        AND ALBVENTALIN.TOTAL IS NOT NULL 
        AND (ALBVENTACAB.FECHA BETWEEN ? AND ?) 
        AND ALBVENTACAB.NUMSERIE LIKE 'Z0%'
        AND P.CODPROVEEDOR <> 10000
    GROUP BY A.TEMPORADA
) AS v ON c.TEMPORADA = v.TEMPORADA

LEFT JOIN (
    SELECT 
		A.TEMPORADA AS TEMPORADA,
        SUM(S.STOCK) AS STOCK,
        ROUND(SUM(
        S.STOCK * 
        COALESCE(ULTIMA_COMPRA.PRECIO, ALIN.ULTIMOCOSTE)
    ), 2) AS VALORACION
    FROM PROVEEDORES P
    INNER JOIN REFERENCIASPROV R ON R.CODPROVEEDOR = P.CODPROVEEDOR
    INNER JOIN ARTICULOS A ON A.REFPROVEEDOR = R.REFPROVEEDOR
    INNER JOIN STOCKS S ON A.CODARTICULO = S.CODARTICULO
    INNER JOIN ARTICULOSLIN ALIN ON S.CODARTICULO = ALIN.CODARTICULO AND S.TALLA = ALIN.TALLA AND S.COLOR = ALIN.COLOR

    -- ÚLTIMA COMPRA POR NUMALBARAN PARA ALMACÉN T0
    OUTER APPLY (
        SELECT TOP 1 ACL.PRECIO
        FROM ALBCOMPRALIN ACL
        WHERE 
            ACL.CODARTICULO = A.CODARTICULO
            AND ACL.TALLA = ALIN.TALLA
            AND ACL.COLOR = ALIN.COLOR
            AND ACL.CODALMACEN = 'T0'
        ORDER BY ACL.NUMALBARAN DESC
    ) AS ULTIMA_COMPRA

    GROUP BY A.TEMPORADA
) AS s ON s.TEMPORADA = ISNULL(c.TEMPORADA, v.TEMPORADA)

WHERE c.TEMPORADA IS NOT NULL OR v.TEMPORADA IS NOT NULL
ORDER BY TEMPORADA;
    """

    parameters = [fechaini, fechafin, fechaini, fechafin]

    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, parameters)
            rows = cursor.fetchall()
            columns = [col[0] for col in cursor.description]
            data = [dict(zip(columns, row)) for row in rows]

        return (
            jsonify({"message": "Consulta ejecutada correctamente", "data": data}),
            200,
            cors_headers(),
        )

    except Exception as e:
        print("❌ Error en /beneficios:", str(e))
        return (
            jsonify({"message": "Error al ejecutar la consulta", "error": str(e)}),
            500,
            cors_headers(),
        )


@app.route("/cierresdecaja", methods=["GET", "OPTIONS"])
def cierresdecaja():
    if request.method == "OPTIONS":
        return "", 200, cors_headers()

    fechaini = request.args.get("fechaini")
    fechafin = request.args.get("fechafin")

    if not fechaini or not fechafin:
        return (
            jsonify({"error": "Faltan los parámetros 'fechaini' y/o 'fechafin'"}),
            400,
            cors_headers(),
        )

    query = """
    SELECT 
    FORMAT(AR.FECHA, 'dd/MM/yyyy') AS FECHA,

    -- Z01
    SUM(CASE WHEN AR.CAJA = 'Z01' AND TP.DESCRIPCION LIKE '%EFECTIVO%' THEN AL.DECLARADO-AL.FIANZA ELSE 0 END) AS Z01_EFECTIVO,
    SUM(CASE WHEN AR.CAJA = 'Z01' AND TP.DESCRIPCION LIKE '%TARJETA%' THEN AL.DECLARADO ELSE 0 END) AS Z01_TARJETA,
    SUM(CASE WHEN AR.CAJA = 'Z01' AND TP.DESCRIPCION LIKE '%EFECTIVO%' THEN AL.DECLARADO-AL.FIANZA ELSE 0 END) +
    SUM(CASE WHEN AR.CAJA = 'Z01' AND TP.DESCRIPCION LIKE '%TARJETA%' THEN AL.DECLARADO ELSE 0 END) AS Z01_TOTAL,

    -- Z02
    SUM(CASE WHEN AR.CAJA = 'Z02' AND TP.DESCRIPCION LIKE '%EFECTIVO%' THEN AL.DECLARADO-AL.FIANZA ELSE 0 END) AS Z02_EFECTIVO,
    SUM(CASE WHEN AR.CAJA = 'Z02' AND TP.DESCRIPCION LIKE '%TARJETA%' THEN AL.DECLARADO ELSE 0 END) AS Z02_TARJETA,
    SUM(CASE WHEN AR.CAJA = 'Z02' AND TP.DESCRIPCION LIKE '%EFECTIVO%' THEN AL.DECLARADO-AL.FIANZA ELSE 0 END) +
    SUM(CASE WHEN AR.CAJA = 'Z02' AND TP.DESCRIPCION LIKE '%TARJETA%' THEN AL.DECLARADO ELSE 0 END) AS Z02_TOTAL,

    -- Z03
    SUM(CASE WHEN AR.CAJA = 'Z03' AND TP.DESCRIPCION LIKE '%EFECTIVO%' THEN AL.DECLARADO-AL.FIANZA ELSE 0 END) AS Z03_EFECTIVO,
    SUM(CASE WHEN AR.CAJA = 'Z03' AND TP.DESCRIPCION LIKE '%TARJETA%' THEN AL.DECLARADO ELSE 0 END) AS Z03_TARJETA,
    SUM(CASE WHEN AR.CAJA = 'Z03' AND TP.DESCRIPCION LIKE '%EFECTIVO%' THEN AL.DECLARADO-AL.FIANZA ELSE 0 END) +
    SUM(CASE WHEN AR.CAJA = 'Z03' AND TP.DESCRIPCION LIKE '%TARJETA%' THEN AL.DECLARADO ELSE 0 END) AS Z03_TOTAL,

    -- Z04
    SUM(CASE WHEN AR.CAJA = 'Z04' AND TP.DESCRIPCION LIKE '%EFECTIVO%' THEN AL.DECLARADO-AL.FIANZA ELSE 0 END) AS Z04_EFECTIVO,
    SUM(CASE WHEN AR.CAJA = 'Z04' AND TP.DESCRIPCION LIKE '%TARJETA%' THEN AL.DECLARADO ELSE 0 END) AS Z04_TARJETA,
    SUM(CASE WHEN AR.CAJA = 'Z04' AND TP.DESCRIPCION LIKE '%EFECTIVO%' THEN AL.DECLARADO-AL.FIANZA ELSE 0 END) +
    SUM(CASE WHEN AR.CAJA = 'Z04' AND TP.DESCRIPCION LIKE '%TARJETA%' THEN AL.DECLARADO ELSE 0 END) AS Z04_TOTAL,

    -- TOTAL
    SUM(CASE WHEN AR.CAJA LIKE 'Z0%' AND TP.DESCRIPCION LIKE '%EFECTIVO%' THEN AL.DECLARADO-AL.FIANZA ELSE 0 END) AS Z0_EFECTIVO,
    SUM(CASE WHEN AR.CAJA LIKE 'Z0%' AND TP.DESCRIPCION LIKE '%TARJETA%' THEN AL.DECLARADO ELSE 0 END) AS Z0_TARJETA,
    SUM(CASE WHEN AR.CAJA LIKE 'Z0%' AND TP.DESCRIPCION LIKE '%EFECTIVO%' THEN AL.DECLARADO-AL.FIANZA ELSE 0 END) +
    SUM(CASE WHEN AR.CAJA LIKE 'Z0%' AND TP.DESCRIPCION LIKE '%TARJETA%' THEN AL.DECLARADO ELSE 0 END) AS Z0_TOTAL

FROM ARQUEOS AR
INNER JOIN ARQUEOSLIN AL ON AR.CAJA = AL.CAJA AND AR.NUMERO = AL.NUMERO
INNER JOIN TIPOSPAGO TP ON AL.CODTIPOPAGO = TP.CODTIPOPAGO
WHERE AR.ARQUEO = 'Z'
  AND (AR.FECHA >= ? AND AR.FECHA <= ?) 
  AND AR.CAJA IN ('Z01', 'Z02', 'Z03', 'Z04')
GROUP BY AR.FECHA
ORDER BY AR.FECHA;
    """

    parameters = [fechaini, fechafin]

    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, parameters)
            rows = cursor.fetchall()
            columns = [col[0] for col in cursor.description]
            data = [dict(zip(columns, row)) for row in rows]

        return (
            jsonify({"message": "Consulta ejecutada correctamente", "data": data}),
            200,
            cors_headers(),
        )

    except Exception as e:
        print("❌ Error en /cierresdecaja:", str(e))
        return (
            jsonify({"message": "Error al ejecutar la consulta", "error": str(e)}),
            500,
            cors_headers(),
        )


# Función para obtener la imagen de la base de datos
def get_image_by_reference(referencia):
    conn = get_connection()
    cursor = conn.cursor()
    query = """
        SELECT FOTO FROM ARTICULOS WHERE REFPROVEEDOR = ?
    """
    cursor.execute(query, (referencia,))
    row = cursor.fetchone()

    if row:
        return io.BytesIO(row[0])  # Devolvemos la imagen como un BytesIO
    else:
        return None


# Nueva ruta para obtener la foto del artículo
@app.route("/articulo/foto", methods=["GET", "OPTIONS"])
def get_foto_articulo():
    if request.method == "OPTIONS":
        return "", 200, cors_headers()

    referencia = request.args.get("referencia")
    if not referencia:
        return (
            jsonify({"error": "Falta el parámetro 'referencia'"}),
            400,
            cors_headers(),
        )

    image_data = get_image_by_reference(referencia)

    if image_data:
        response = send_file(image_data, mimetype="image/jpeg")
        # Agregar cabeceras CORS manualmente
        for key, value in cors_headers().items():
            response.headers[key] = value
        return response
    else:
        return jsonify({"error": "Imagen no encontrada"}), 404, cors_headers()


# # Mi codigo
# # Función para obtener imagen según temporada
# def get_image_by_season(referencia):
#     conn = get_connection()
#     cursor = conn.cursor()
#     query = """
#         SELECT 
#             A.CODARTICULO,
#             A.DESCRIPCION,
#             A.DESCRIPADIC,
#             A.FOTO,
#             S.TALLA,
#             S.STOCK
#         FROM dbo.ARTICULOS A
#         JOIN dbo.STOCKS S ON A.CODARTICULO = S.CODARTICULO
#         WHERE A.TEMPORADA = ? AND S.STOCK > 0
#     """
#     cursor.execute(query, (referencia,))
#     rows = cursor.fetchall()

#     # lista para guardar las imagenes transformadas
#     imagenes = []
#     if rows:
#         for cod, desc, descadic, foto, talla, stock in rows:
#             # Convertimos FOTO (bytes) a base64
#             foto_b64 = base64.b64encode(foto).decode("utf-8") if foto else None
#             imagenes.append(
#                 {
#                     "codarticulo": cod,
#                     "descripcion": desc,
#                     "descripcionadic": descadic,
#                     "foto": foto_b64,
#                     "talla": talla,
#                     "stock": stock,
#                 }
#             )

#         return imagenes


def get_image_by_season(referencia):
    conn = get_connection()
    cursor = conn.cursor()

    query = """
        SELECT 
            A.CODARTICULO,
            A.DESCRIPCION,
            A.REFPROVEEDOR,
            A.FOTO,
            S.TALLA,
            S.STOCK,
            PV.PBRUTO
        FROM dbo.ARTICULOS A
        JOIN dbo.STOCKS S ON A.CODARTICULO = S.CODARTICULO
        LEFT JOIN dbo.PRECIOSVENTA PV ON A.CODARTICULO = PV.CODARTICULO AND S.TALLA = PV.TALLA
        WHERE A.TEMPORADA = ? AND S.STOCK > 0
    """

    cursor.execute(query, (referencia,))
    rows = cursor.fetchall()

    imagenes = []
    if rows:
        for cod, desc, descadic, foto, talla, stock, pbruto in rows:
            foto_b64 = base64.b64encode(foto).decode("utf-8") if foto else None
            imagenes.append(
                {
                    "codarticulo": cod,
                    "descripcion": desc,
                    "descripcionadic": descadic,
                    "foto": foto_b64,
                    "talla": talla,
                    "stock": stock,
                    "pbruto": float(pbruto) if pbruto is not None else None,
                }
            )

    return imagenes


# Ruta para obtener catalago imagenes
@app.route("/catalogo-temporada", methods=["GET", "OPTIONS"])
def get_catalogo_temporada():
    if request.method == "OPTIONS":
        return "", 200, cors_headers()

    referencia = request.args.get("referencia")
    if not referencia:
        return jsonify({"error": "Falta el código de 'temporada'"}), 400, cors_headers()

    image_data = get_image_by_season(referencia)

    if image_data:
        return (
            jsonify(
                {
                    "message": f"{len(image_data)} artículos encontrados",
                    "data": image_data,
                }
            ),
            200,
            cors_headers(),
        )
    else:
        return jsonify({"error": "No se encontraron artículos"}), 404, cors_headers()


@app.route("/catalogo-proveedor", methods=["GET", "OPTIONS"])
def get_catalogo_proveedor():
    if request.method == "OPTIONS":
        return "", 200, cors_headers()

    proveedor = request.args.get("proveedor")
    if not proveedor:
        return jsonify({"error": "Falta el código de 'proveedor'"}), 400, cors_headers()

    image_data = get_images_by_supplier(proveedor)

    if image_data:
        return (
            jsonify(
                {
                    "message": f"{len(image_data)} artículos encontrados",
                    "data": image_data,
                }
            ),
            200,
            cors_headers(),
        )
    else:
        return jsonify({"error": "No se encontraron artículos"}), 404, cors_headers()


# def get_images_by_supplier(proveedor):
#     conn = get_connection()
#     cursor = conn.cursor()

#     query = """
#         SELECT 
#             A.CODARTICULO,
#             A.DESCRIPCION,
#             A.DESCRIPADIC,
#             A.FOTO,
#             S.TALLA,
#             S.STOCK
#         FROM dbo.ARTICULOS A
#         JOIN dbo.STOCKS S ON A.CODARTICULO = S.CODARTICULO
#         WHERE 
#             S.STOCK > 0
#             AND (
#                 LEFT(A.DESCRIPADIC, 3) COLLATE Modern_Spanish_CI_AS = ?
#                 OR LEFT(A.REFPROVEEDOR, 3) COLLATE Modern_Spanish_CI_AS = ?
#             )
#     """
#     cursor.execute(query, (proveedor, proveedor))
#     rows = cursor.fetchall()

#     imagenes = []
#     if rows:
#         for cod, desc, descadic, foto, talla, stock in rows:
#             foto_b64 = base64.b64encode(foto).decode("utf-8") if foto else None
#             imagenes.append(
#                 {
#                     "codarticulo": cod,
#                     "descripcion": desc,
#                     "descripcionadic": descadic,
#                     "foto": foto_b64,
#                     "talla": talla,
#                     "stock": stock,
#                 }
#             )

#     return imagenes


def get_images_by_supplier(proveedor):
    conn = get_connection()
    cursor = conn.cursor()

    query = """
        SELECT 
            A.CODARTICULO,
            A.DESCRIPCION,
            A.REFPROVEEDOR,
            A.FOTO,
            S.TALLA,
            S.STOCK,
            PV.PBRUTO
        FROM dbo.ARTICULOS A
        JOIN dbo.STOCKS S ON A.CODARTICULO = S.CODARTICULO
        LEFT JOIN dbo.PRECIOSVENTA PV ON A.CODARTICULO = PV.CODARTICULO
        WHERE 
            S.STOCK > 0
            AND (
                LEFT(A.REFPROVEEDOR, 3) COLLATE Modern_Spanish_CI_AS = ?
            )
    """
    cursor.execute(query, (proveedor))
    rows = cursor.fetchall()

    imagenes = []
    if rows:
        for cod, desc, descadic, foto, talla, stock, pbruto in rows:
            foto_b64 = base64.b64encode(foto).decode("utf-8") if foto else None
            imagenes.append(
                {
                    "codarticulo": cod,
                    "descripcion": desc,
                    "descripcionadic": descadic,
                    "foto": foto_b64,
                    "talla": talla,
                    "stock": stock,
                    "pbruto": float(pbruto) if pbruto is not None else None
                }
            )

    return imagenes




# ruta prueba index
@app.route("/")
def index():
    temporada = "V22"
    imagenes = get_image_by_season(temporada)

    if imagenes:
        data = []
        for img in imagenes:
            img.seek(0)
            encoded = base64.b64encode(img.read()).decode("utf-8")
            data.append({"imagen": encoded})
    else:
        data = []

    return render_template("indexPrueba.html", data=data)


# Fin mi codigo


@app.route("/formas-pago/resumen", methods=["GET", "OPTIONS"])
def resumen_formas_pago():
    if request.method == "OPTIONS":
        return "", 200, cors_headers()

    tienda = request.args.get("tienda")
    fechaini = request.args.get("fechaini")
    fechafin = request.args.get("fechafin")

    if not all([tienda, fechaini, fechafin]):
        return (
            jsonify({"error": "Faltan parámetros: tienda, fechaini o fechafin"}),
            400,
            cors_headers(),
        )

    try:
        fechaini_dt = datetime.strptime(fechaini, "%Y-%m-%d")
        fechafin_dt = datetime.strptime(fechafin, "%Y-%m-%d")
    except ValueError:
        return (
            jsonify({"error": "Formato de fecha inválido. Usa YYYY-MM-DD"}),
            400,
            cors_headers(),
        )

    try:
        conn = get_connection()
        cursor = conn.cursor()
        query = """
            SELECT FORMASPAGO.DESCRIPCION AS FORMAPAGO, SUM(IMPORTE) AS TOTAL_IMPORTE
            FROM TESORERIA
            INNER JOIN FORMASPAGO
            ON TESORERIA.CODFORMAPAGO = FORMASPAGO.CODFORMAPAGO
            WHERE TESORERIA.FECHADOCUMENTO BETWEEN ? AND ?
            AND TESORERIA.SERIE LIKE 'Z02%'
            GROUP BY FORMASPAGO.DESCRIPCION
        """
        cursor.execute(query, (fechaini_dt, fechafin_dt))
        resultados = cursor.fetchall()

        data = [
            {"formapago": row[0], "total_importe": float(row[1])} for row in resultados
        ]
        return jsonify(data), 200, cors_headers()
    except Exception as e:
        return jsonify({"error": str(e)}), 500, cors_headers()


def cors_headers():
    return {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization",
    }


if __name__ == "__main__":
    app.run(debug=True, port=5000)
