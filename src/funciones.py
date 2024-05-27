import psycopg2
import pandas as pd
from datetime import datetime

def obtener_datos(host, port, dbname, user, password, query):
    connection = psycopg2.connect(
            host=host,
            port=port,
            dbname=dbname,
            user=user,
            password=password
        )
    cursor = connection.cursor()
    cursor.execute(query)
    # Obtener los nombres de las columnas
    colnames = [desc[0] for desc in cursor.description]
    # Obtener los datos
    data = cursor.fetchall()
    # Crear un DataFrame de pandas
    df = pd.DataFrame(data, columns=colnames)
    cursor.close()
    connection.close()
    return df

def calcular_edad(fecha_nacimiento):
    hoy = pd.Timestamp(datetime.now())
    edad = hoy.year - fecha_nacimiento.year - ((hoy.month, hoy.day) < (fecha_nacimiento.month, fecha_nacimiento.day))
    return edad