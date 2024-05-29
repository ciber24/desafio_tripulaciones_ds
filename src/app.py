import streamlit as st
from PIL import Image
import pandas as pd
import numpy as np
import streamlit.components.v1 as c
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.cm as cm
import seaborn as sns
import psycopg2
from funciones import obtener_datos, calcular_edad
import plotly.express as px
import plotly.graph_objs as go
from dotenv import load_dotenv
import os

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

host = st.secrets["env"]["host"]
port = st.secrets["env"]["port"]
dbname = st.secrets["env"]["dbname"]
user = st.secrets["env"]["user"]
password = st.secrets["env"]["password"]


st.set_page_config(page_title="Admin Dashboard",
                   #page_icon="data/icono.png"
                   )

img = Image.open("img/bye.png")
st.sidebar.image(img)
sin_filtro = "Sin filtro"

seleccion = st.sidebar.selectbox("Seleccione menu", ["Home", "Intereses Alumnos", "Histórico Interacciones", "Distribución de los Alumnos por País", "Facturación", "Referencias"])
if seleccion == "Home":
    #st.title("Panel de control")
    img_2 = Image.open("img/intro.png")
    st.image(img_2, 
             width=570,
             )
    #    st.write("EDITAMOS ")
    #    st.write("EDITAMOS")


elif seleccion == "Intereses Alumnos":

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


    filtro_edad = st.sidebar.selectbox("Filtro edad", [sin_filtro] + sorted(list(df["edad"].unique())))
    
    if filtro_edad != sin_filtro:
        df = df[df["edad"]==filtro_edad]

    filtro_pais = st.sidebar.selectbox("Filtro pais", [sin_filtro] + sorted(list(df["pais"].unique())))

    if filtro_pais != sin_filtro:
        df = df[df["pais"]==filtro_pais]

    if len(df)!=0:

        # Conexión a la base de datos
                
        df_interesados = df[df['interesado'] == True]
        # Contar la cantidad de veces que cada servicio ha sido contratado
        intereses = df_interesados['nombre_servicio'].value_counts()
        
        # Definir el número de barras
        num_bars = len(intereses)
        titulo = "Distribución del interés del cliente en los servicios ofertados:"
        # Crear el gráfico de barras
        fig = go.Figure(data=[go.Bar(x=intereses.index, y=intereses.values, marker_color=px.colors.qualitative.Plotly)])
        base_color = '#A50085'
        cmap = cm.get_cmap('Purples', num_bars + 6)
        colors = [mcolors.to_hex(cmap(i)) for i in reversed(range(2,cmap.N))]
        # Establecer diseño del gráfico
        fig = go.Figure(data=[go.Bar(
        x=intereses.index,
        y=intereses.values,
        marker=dict(color=colors),
        text=intereses.values,
        textposition='auto'
        )])
        
        fig.update_layout(
            title=titulo,
            xaxis=dict(title='Servicios ofertados', tickangle=-20),
            yaxis=dict(title='Cantidad de interesados'),
            font=dict(family='Lato'),
            title_font=dict(family="Lato", size=24, color="#002766"),
            width=750,  # Ancho de la figura
            height=470,  # Alto de la figura
        )
        # Mostrar el gráfico en Streamlit
        st.plotly_chart(fig)


    else:
        st.write("No hay resultados")

elif seleccion == "Histórico Interacciones":

    
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

    filtro_agente = st.sidebar.selectbox("Filtro Agentes", [sin_filtro] + sorted(list(df["agente"].unique())))

    titulo = "Distribución de Interacciones con los clientes:"

    if filtro_agente != sin_filtro:
        df = df[df["agente"]==filtro_agente]
        titulo = "Distribución de Interacciones de " + filtro_agente + ":"
    
    
    recuento = df["motivo"].value_counts()

    category_color_map  = {
        'Seguimiento' : '#5e3070', 
        'Ofertas' : '#6f8779', 
        'Incidencias' : '#ad0937'
        }
    
    labels = recuento.index
    values = recuento.values
    colors = [category_color_map[label] for label in labels]

    fig = go.Figure(data=[go.Pie(labels=labels, values=values, hole=0.4, marker=dict(colors=colors))])
    
    
    fig.update_layout(
        title=titulo, 
        title_font=dict(family="Lato", size=24, color="#002766"),
        legend_font=dict(family="Lato", size=14, color="#002766"),
        width=800,  # Ancho del gráfico
        height=570,  # Alto del gráfico
        )

    # Mostrar el gráfico en Streamlit
    st.plotly_chart(fig)

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
        title="Distribución global del cliente:",
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
        width=900,  # Ancho de la figura
        height=600,  # Alto de la figura
        title_font=dict(family="Lato", size=24, color="#002766")
    )

    # Mostrar el mapa
    st.plotly_chart(fig)


elif seleccion == "Facturación":

    evolucion_ventas = st.sidebar.checkbox('Mostrar gráfico de evolución de la facturación')
    if evolucion_ventas:

        meses = ["Sin filtrar"] + pd.date_range(start="2022-01-01", end="2023-12-31", freq='MS').strftime("%Y-%m").tolist()
        selected_month = st.sidebar.selectbox("Seleccione un mes para visualizar las ventas posteriores:", meses)


        query = '''SELECT * FROM facturas
                    ORDER BY fecha'''
        df = obtener_datos(host, port, dbname, user, password, query)
        df["fecha"] = pd.to_datetime(df['fecha'])

        if selected_month != "Sin filtrar":
            df = df[df["fecha"]>selected_month] 

        fig = px.line(df, x='fecha', y='precio', title='Evolución de la facturación:', labels={'fecha': 'Fecha', 'precio': 'Precio (€)'})

        fig.update_layout(
            title_font=dict(family="Lato", size=24, color="#002766"),  # Fuente Lato para el título
            xaxis=dict(title='Fecha', title_font=dict(family="Lato", size=16, color="#000000")),  # Fuente Lato para el eje X
            yaxis=dict(title='Precio (€)', title_font=dict(family="Lato", size=16, color="#000000")),  # Fuente Lato para el eje Y
            width=700,  # Ancho del gráfico
            height=500  # Alto del gráfico
                )

        # Mostrar el gráfico en Streamlit
        st.plotly_chart(fig)
    
    servicios_más_vendidos = st.sidebar.checkbox('Mostrar gráfico servicios más contratados')
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
        num_bars = len(ingresos_por_servicio)

        # Generar colores degradados personalizados
        base_color = '#A50085'
        cmap = cm.get_cmap('Purples',num_bars + 6)
        colors = [mcolors.to_hex(cmap(i / (num_bars + 2))) for i in reversed(range(2, num_bars + 2))]

        fig = go.Figure(data=[go.Bar(x=ingresos_por_servicio.index, y=ingresos_por_servicio.values, marker=dict(color=colors[:num_bars]))])


        # Establecer diseño del gráfico
        fig.update_layout(
            title='Distribución de los servicios más contratados:',
            title_font=dict(family="Lato", size=24, color="#002766"),  # Fuente Lato para el título
            xaxis=dict(title='Servicios', tickangle=25, title_standoff=50, title_font=dict(family="Lato", size=16, color="#000000")),  # Fuente Lato para el eje X
            yaxis=dict(title='Ingresos', title_font=dict(family="Lato", size=16, color="#000000")),  # Fuente Lato para el eje Y
            width=800,  # Ancho del gráfico
            height=570  # Alto del gráfico
            )
        st.plotly_chart(fig)


        #Grafico de ingresos por agente
    ventas_agente = st.sidebar.checkbox('Mostrar gráfico de distribución de facturación por agente')
    if ventas_agente:
        query2 = '''SELECT 
        facturas.precio,
        CONCAT(agentes.nombre , ' ', agentes.apellidos) AS nombre_agente
        FROM facturas
        INNER JOIN agentes ON agentes.id_agente = facturas.id_agente'''
        df_facturas_agentes = obtener_datos(host,port,dbname,user,password,query2)
        facturas_por_agente = df_facturas_agentes.groupby('nombre_agente')['precio'].sum().sort_values(ascending=False).reset_index()

        # Definir el número de barras
        num_bars = len(facturas_por_agente)

        # Generar colores degradados personalizados
        base_color = '#A50085'
        cmap = cm.get_cmap('Purples', num_bars + 3)
        colors = [mcolors.to_hex(cmap(i)) for i in reversed(range(3, cmap.N))]

        # Crear el gráfico interactivo con Plotly
        fig = go.Figure(data=[go.Bar(
            x=facturas_por_agente['nombre_agente'],
            y=facturas_por_agente['precio'],
            marker=dict(color=colors[:num_bars]),  # Aplicar los colores generados
            text=facturas_por_agente['precio'],
            textposition='auto'
        )])

        fig.update_layout(
            title='Distribución de facturación por agente:',
            title_font=dict(family="Lato", size=24, color="#002766"),  # Fuente Lato para el título
            xaxis=dict(title='Agentes', tickangle=45, title_font=dict(family="Lato", size=16, color="#000000")),  # Fuente Lato para el eje X
            yaxis=dict(title='Ingresos', title_font=dict(family="Lato", size=16, color="#000000")),  # Fuente Lato para el eje Y
            width=900,  # Ancho del gráfico
            height=570  # Alto del gráfico
            )

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

        # Definir el número de barras
        num_bars = len(facturas_por_pais)

        # Generar colores degradados personalizados
        base_color = '#A50085'
        cmap = cm.get_cmap('Purples',num_bars + 6)
        colors = [mcolors.to_hex(cmap(i / (num_bars + 2))) for i in reversed(range(2, num_bars + 2))]

        # Crear el gráfico interactivo con Plotly
        fig = go.Figure(data=[go.Bar(
            x=facturas_por_pais['pais'],
            y=facturas_por_pais['precio'],
            marker=dict(color=colors),
            text=round(facturas_por_pais['precio'],2),
            textposition='auto'
            )])

        fig.update_layout(
            title='Distribución de facturación por país de origen del cliente:',
            xaxis=dict(title='País', tickangle=45, title_font=dict(family="Lato", size=16, color="#002766")),
            yaxis=dict(title='Ingresos (€)', title_font=dict(family="Lato", size=16, color="#002766")),
            title_font=dict(family="Lato", size=24, color="#002766"),
                        width=800,  # Ancho del gráfico
            height=570  # Alto del gráfico
                )

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

    paises = [sin_filtro] + sorted(list(df_referencias["pais"].unique()))

    selected_country = st.sidebar.selectbox("Seleccione un pais para ver las referencias por pais:", paises)

    if selected_country != sin_filtro:
        df_referencias = df_referencias[df_referencias["pais"]==selected_country]


    referencias = df_referencias['descripcion'].value_counts()

    ## Crear el gráfico de pastel
    category_color_map = {
        'Referencia (amigo, familiar, conocido)': '#E9D337',
        'Página Web': '#554AED',
        'Redes Sociales (Instagram, Facebook, Whatsapp, Newsletter, LinkedIn)': '#3BB9FF',
        'Institución (colegio, universidad, otras)': '#002766'
    }

    # Crear los datos del gráfico de pastel
    labels = referencias.index
    values = referencias.values
    colors = [category_color_map[label] for label in labels]

    # Crear el gráfico de pastel
    fig = go.Figure(data=[go.Pie(labels=labels, values=values, hole=0.4, marker=dict(colors=colors))])

    fig.update_layout(
        title='¿A través de qué plataformas nos han conocido nuestros clientes?',
        title_font=dict(family="Lato", size=24, color="#002766"),
        legend_font=dict(family="Lato", size=14, color="#002766"),
        width=800,  # Ancho del gráfico
        height=570,  # Alto del gráfico
    )

    # Mostrar el gráfico en Streamlit
    st.plotly_chart(fig)


