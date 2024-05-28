import streamlit as st
from PIL import Image
import pandas as pd
import numpy as np
import streamlit.components.v1 as c
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
import psycopg2
from funciones import obtener_datos, calcular_edad
import plotly.express as px
from config import host, port, dbname, user, password
import os

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


st.set_page_config(page_title="Descargas Play Store",
                   #page_icon="data/icono.png"
                   )

seleccion = st.sidebar.selectbox("Seleccione menu", ["Home", "Intereses Alumnos", "Histórico Interacciones", "Distribución de los Alumnos por País", "Facturación", "Referencias"])

if seleccion == "Home":
    st.title("ESTO HAY QUE EDITARLO")
    
    with st.expander("EDITAMOS"):
        st.write("EDITAMOS ")
        st.write("EDITAMOS")
    img = Image.open("img/bye.png")

    st.image(img)

elif seleccion == "Intereses Alumnos":

    st.title("Intereses Alumnos:")

    query = '''SELECT "alumnos".nombre || ' ' || "alumnos".apellidos AS "nombre_completo",
                    "servicios_generales"."nombre_servicio",
                    "alumnos".fecha_nacimiento,
                    "alumnos".pais,
                    "intereses".interesado
                    FROM "intereses" 
                    INNER JOIN "servicios_generales" ON "intereses".id_serviciog = "servicios_generales".id_serviciog
                    INNER JOIN "alumnos" ON "intereses".id_alumno = "alumnos".id_alumno;'''
        
    df = obtener_datos(host, port, dbname, user, password, query)
    df['fecha_nacimiento'] = pd.to_datetime(df['fecha_nacimiento'])
    df['edad'] = df['fecha_nacimiento'].apply(calcular_edad)


    filtro_edad = st.sidebar.selectbox("Filtro edad", ["Sin filtro"] + sorted(list(df["edad"].unique())))
    
    if filtro_edad != "Sin filtro":
        df = df[df["edad"]==filtro_edad]

    filtro_pais = st.sidebar.selectbox("Filtro pais", ["Sin filtro"] + sorted(list(df["pais"].unique())))

    if filtro_pais != "Sin filtro":
        df = df[df["pais"]==filtro_pais]

    if len(df)!=0:

        # Conexión a la base de datos
        try:
                
            df_interesados = df[df['interesado'] == True]

            # Contar la cantidad de veces que cada servicio ha sido contratado
            intereses = df_interesados['nombre_servicio'].value_counts()
            
            # Crear el gráfico de barras
            plt.figure(figsize=(10, 6))
            sns.barplot(x=intereses.index, y=intereses.values, palette='viridis')
            plt.title('Servicios Más Contratados')
            plt.xlabel('Servicio')
            plt.ylabel('Número de Contrataciones')
            plt.xticks(rotation=45)
            plt.show()

            st.pyplot(plt)
    

        except:
            st.write(" Error")
    else:
        st.write("No hay resultados")

elif seleccion == "Histórico Interacciones":

    st.title("Histórico Interacciones:")
    
    query = '''SELECT 
                agentes.id_agente,
                agentes.nombre || ' ' || agentes.apellidos AS agente,
                historico_contactos.fecha,
                historico_contactos.motivo

                FROM agentes
                INNER JOIN facturas ON agentes.id_agente = facturas.id_agente
                INNER JOIN historico_contactos ON facturas.id_factura = historico_contactos.id_factura
                ORDER BY id_agente'''

    df = obtener_datos(host, port, dbname, user, password, query)

    filtro_agente = st.sidebar.selectbox("Filtro Agentes", ["Sin filtro"] + sorted(list(df["agente"].unique())))

    titulo = "Distribución de Interacciones General:"

    if filtro_agente != "Sin filtro":
        df = df[df["agente"]==filtro_agente]
        titulo = "Distribución de Interacciones de " + filtro_agente + ":"
    
    recuento = df["motivo"].value_counts()
    plt.figure(figsize=(8, 8))
    plt.pie(recuento, labels=recuento.index, autopct='%1.1f%%', startangle=140, colors=['#ff9999','#66b3ff','#99ff99'])

    # Título del gráfico
    plt.title(titulo)

    # Mostrar el gráfico
    plt.show()
    st.pyplot(plt)

elif seleccion == "Distribución de los Alumnos por País":
    query = '''SELECT * FROM alumnos'''

    paises_df = obtener_datos(host, port, dbname, user, password, query)

    # Crear DataFrame con el recuento de alumnos por país
    paises_df = pd.DataFrame(paises_df['pais'].value_counts().reset_index())

    # Renombrar las columnas
    paises_df.columns = ['pais', 'recuento']

    # Reemplazar nombres de países
    paises_df['pais'].replace({'España': 'Spain', 'México': 'Mexico', 'Perú': 'Peru', 'Brasil': 'Brazil'}, inplace=True)

    # Verificar el DataFrame resultante
    print(paises_df.head())

    import plotly.express as px

    # Crear el mapa de burbujas
    fig = px.scatter_geo(
        paises_df,
        locations="pais",  # Utilizamos los nombres de los países como ubicaciones
        locationmode="country names",
        size="recuento",         # Tamaño de las burbujas basado en el número de alumnos
        hover_name="pais",  # Nombre que se muestra al pasar el cursor
        color="recuento",        # Color de las burbujas basado en el número de alumnos
        projection="natural earth",
        title="Número de Alumnos por País",
        color_continuous_scale=px.colors.sequential.Purples,  # Escala de color en morado
        color_continuous_midpoint=paises_df['recuento'].median(),  # Definir el punto medio de la escala de color
        range_color=[0.1, paises_df['recuento'].max()],  # Establecer el rango de la escala de color
    )

    # Personalizar el diseño del mapa
    fig.update_geos(
        bgcolor='lightgrey',  # Cambiar el color de fondo del mapa
    )

    # Ajustar el tamaño de la figura
    fig.update_layout(
        width=1000,  # Ancho de la figura
        height=600,  # Alto de la figura
    )

    # Mostrar el mapa
    st.plotly_chart(fig)

    # Guardar el mapa como archivo HTML
    fig.write_html('mapa_bubble_plot_alumnos_por_pais.html')


elif seleccion == "Facturación":

    evolucion_ventas = st.sidebar.checkbox('Mostrar gráfico de evolución de ingresos')
    if evolucion_ventas:

        meses = ["Sin filtrar"] + pd.date_range(start="2022-01-01", end="2023-12-31", freq='MS').strftime("%Y-%m").tolist()
        selected_month = st.sidebar.selectbox("Seleccione un mes para visualizar ventas posteriores:", meses)


        query = '''SELECT * FROM facturas
                    ORDER BY fecha'''
        df = obtener_datos(host, port, dbname, user, password, query)
        df["fecha"] = pd.to_datetime(df['fecha'])

        if selected_month != "Sin filtrar":
            df = df[df["fecha"]>selected_month] 

        fig = px.line(df, x='fecha', y='precio', title='Evolución de Ingresos', labels={'fecha': 'Fecha', 'precio': 'Precio (€)'})

        fig.update_layout(
        width=800,  # Ancho del gráfico
        height=400  # Alto del gráfico
        )

        # Mostrar el gráfico en Streamlit
        st.plotly_chart(fig)
    
    servicios_más_vendidos = st.sidebar.checkbox('Mostrar gráfico servicios más vendidos')
    if servicios_más_vendidos:
        query = '''SELECT
                    lineas_factura.precio,
                    lineas_factura.fecha,
                    paises.nombre AS pais,
                    servicios_generales.nombre_servicio
                    FROM lineas_factura
                    INNER JOIN servicios_especificos ON lineas_factura.id_servicioes = servicios_especificos.id_servicioes
                    INNER JOIN paises ON servicios_especificos.id_pais = paises.id_pais
                    INNER JOIN servicios_generales ON servicios_generales.id_serviciog = servicios_especificos.id_serviciog                 
                    '''
        df = obtener_datos(host, port, dbname, user, password, query)

        paises = ["Sin filtrar"] + sorted(list(df["pais"].unique()))

        selected_country = st.sidebar.selectbox("Seleccione un pais para ver sus servicios más vendidos:", paises)

        if selected_country != "Sin filtrar":
            df = df[df["pais"]==selected_country]
        ingresos_por_servicio = df.groupby("nombre_servicio")["precio"].sum().sort_values(ascending=False)

        plt.figure(figsize=(10, 6))
        sns.barplot(x=ingresos_por_servicio.index, y=ingresos_por_servicio.values, palette='viridis')
        plt.title('Servicios Más Contratados')
        plt.xlabel('Servicios')
        plt.ylabel('Ingresos')
        plt.xticks(rotation=45)
        plt.show()

        st.pyplot(plt)


        #Grafico de ingresos por agente
    ventas_agente = st.sidebar.checkbox('Mostrar gráfico de ventas por agente')
    if ventas_agente:
        query2 = '''SELECT 
        facturas.precio,
        CONCAT(agentes.nombre , ' ', agentes.apellidos) AS nombre_agente
        FROM facturas
        INNER JOIN agentes ON agentes.id_agente = facturas.id_agente'''
        df_facturas_agentes = obtener_datos(host,port,dbname,user,password,query2)
        facturas_por_agente = df_facturas_agentes.groupby('nombre_agente')['precio'].sum().sort_values(ascending=False).reset_index()

        # Crear el gráfico interactivo con Plotly
        fig = px.bar(facturas_por_agente, x='nombre_agente', y='precio', title='Sumatorio de Facturas por Agente',
                    labels={'nombre_agente': 'Agentes', 'precio': 'Ingresos'})

        # Mostrar el gráfico interactivo
        st.plotly_chart(fig)
    

    ventas_pais_origen = st.sidebar.checkbox('Mostrar gráfico de ventas por pais de origen:')
    if ventas_pais_origen:
        query1 = '''SELECT 
                    facturas.precio,
                    alumnos.pais
                    FROM facturas
                    INNER JOIN alumnos ON alumnos.id_alumno = facturas.id_alumno'''
        
        df_facturas_alumnos = obtener_datos(host,port,dbname,user,password,query1)
        facturas_por_pais = df_facturas_alumnos.groupby('pais')['precio'].sum().sort_values(ascending=False).reset_index()

        # Crear el gráfico interactivo con Plotly
        fig = px.bar(facturas_por_pais, x='pais', y='precio', title='Sumatorio de Facturas por País de Origen del Alumno',
                    labels={'pais': 'País', 'precio': 'Ingresos'})

        # Mostrar el gráfico interactivo
        st.plotly_chart(fig)

elif seleccion == "Referencias":

    # referencias
    query3 = '''SELECT 
    alumnos.nombre,
    referencias.descripcion,
    alumnos.pais,
    CONCAT(alumnos.nombre , ' ', alumnos.apellidos) AS nombre_alumno
    FROM alumnos
    INNER JOIN referencias ON referencias.id_referencia = alumnos.id_referencia'''

    df_referencias = obtener_datos(host,port,dbname,user,password,query3)

    paises = ["Sin filtrar"] + sorted(list(df_referencias["pais"].unique()))

    selected_country = st.sidebar.selectbox("Seleccione un pais para ver las referencias por pais:", paises)

    if selected_country != "Sin filtrar":
        df_referencias = df_referencias[df_referencias["pais"]==selected_country]


    referencias = df_referencias['descripcion'].value_counts()
    # Crear el gráfico de pastel
    fig = px.pie(referencias, values=referencias.values, names=referencias.index, title='¿A través qué plataformas nos conocen nuestros clientes?',
                 hole=0.4)

    st.plotly_chart(fig)
