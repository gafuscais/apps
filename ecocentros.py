import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import numpy as np

# Configuración de página
st.set_page_config(
    page_title="Dashboard Ecocentros Montevideo",
    page_icon="♻️",
    layout="wide"
)

# Función para cargar los datos
@st.cache_data
def load_data():
    # En una aplicación real se usaría:
    # df = pd.read_csv('tabla_de_datos_de_material_ingresado_a_ecocentros.csv')
    
    # Para este ejemplo, asumimos que el archivo está cargado como en el análisis previo
    try:
        df = pd.read_csv('tabla_de_datos_de_material_ingresado_a_ecocentros.csv')
        return df
    except Exception as e:
        st.error(f"Error al cargar los datos: {e}")
        return None

# Mapeo de meses
MESES = {
    1: 'Enero',
    2: 'Febrero',
    3: 'Marzo',
    4: 'Abril',
    5: 'Mayo',
    6: 'Junio',
    7: 'Julio',
    8: 'Agosto',
    9: 'Septiembre',
    10: 'Octubre',
    11: 'Noviembre',
    12: 'Diciembre'
}

# Función para crear fecha completa
def create_date_column(df):
    df['fecha'] = pd.to_datetime([f"{year}-{month}-01" for year, month in zip(df.anio, df.mes)])
    df['mes_nombre'] = df['mes'].map(MESES)
    df['periodo'] = df['mes_nombre'] + ' ' + df['anio'].astype(str)
    return df

# Función para aplicar filtros
def filter_dataframe(df, ecocentro, residuo, anio):
    filtered_df = df.copy()
    
    if ecocentro != "Todos":
        filtered_df = filtered_df[filtered_df.ecocentro == ecocentro]
    
    if residuo != "Todos":
        filtered_df = filtered_df[filtered_df.residuo == residuo]
    
    if anio != "Todos":
        filtered_df = filtered_df[filtered_df.anio == int(anio)]
    
    return filtered_df

# Función para crear serie temporal
def create_time_series(df):
    # Agrupar por fecha y sumar kilogramos
    time_df = df.groupby(['fecha', 'periodo'])['kg'].sum().reset_index()
    time_df = time_df.sort_values('fecha')
    
    # Crear gráfico
    fig = px.line(
        time_df, 
        x='fecha', 
        y='kg',
        labels={'kg': 'Cantidad (kg)', 'fecha': 'Fecha'},
        title='Evolución Mensual de Residuos'
    )
    
    fig.update_layout(
        xaxis_title='Fecha',
        yaxis_title='Kilogramos',
        height=400,
        hovermode='x',
        xaxis=dict(tickangle=-45)
    )
    
    # Ajustar el formato de las etiquetas del eje X
    fig.update_xaxes(
        tickformat="%b %Y"
    )
    
    return fig

# Función para crear distribución de residuos
def create_residuo_distribution(df):
    residuo_df = df.groupby('residuo')['kg'].sum().reset_index()
    residuo_df = residuo_df.sort_values('kg', ascending=False).head(10)
    
    fig = px.bar(
        residuo_df,
        y='residuo',
        x='kg',
        orientation='h',
        labels={'kg': 'Cantidad (kg)', 'residuo': 'Tipo de Residuo'},
        title='Top 10 Tipos de Residuos'
    )
    
    fig.update_layout(
        height=400,
        yaxis=dict(autorange="reversed")
    )
    
    return fig

# Función para crear comparación de ecocentros
def create_ecocentros_comparison(df):
    ecocentro_df = df.groupby('ecocentro')['kg'].sum().reset_index()
    
    fig = px.bar(
        ecocentro_df,
        x='ecocentro',
        y='kg',
        color='ecocentro',
        labels={'kg': 'Cantidad (kg)', 'ecocentro': 'Ecocentro'},
        title='Comparación entre Ecocentros'
    )
    
    fig.update_layout(
        height=400,
        xaxis_title='Ecocentro',
        yaxis_title='Kilogramos'
    )
    
    return fig

# Función para crear comparación anual
def create_anual_comparison(df):
    anual_df = df.groupby('anio')['kg'].sum().reset_index()
    
    fig = px.bar(
        anual_df,
        x='anio',
        y='kg',
        labels={'kg': 'Cantidad (kg)', 'anio': 'Año'},
        title='Comparación Anual'
    )
    
    fig.update_layout(
        height=400,
        xaxis_title='Año',
        yaxis_title='Kilogramos'
    )
    
    # Asegurarse de que las etiquetas del eje X sean años enteros
    fig.update_xaxes(
        tickvals=anual_df['anio'].unique(),
    )
    
    return fig

# Función para crear KPIs
def create_kpis(df):
    # Total recolectado
    total_recolectado = df['kg'].sum()
    
    # Promedio mensual
    monthly_data = df.groupby(['anio', 'mes'])['kg'].sum().reset_index()
    promedio_mensual = monthly_data['kg'].mean()
    
    # Residuo más recolectado
    residuo_counts = df.groupby('residuo')['kg'].sum()
    residuo_mas_recolectado = residuo_counts.idxmax()
    
    # Ecocentro más activo
    ecocentro_counts = df.groupby('ecocentro')['kg'].sum()
    ecocentro_mas_activo = ecocentro_counts.idxmax()
    
    return total_recolectado, promedio_mensual, residuo_mas_recolectado, ecocentro_mas_activo

# Función principal
def main():
    # Título y descripción
    st.title("Dashboard de Ecocentros - Montevideo")
    st.markdown("Visualización de datos de residuos recolectados en los ecocentros de Montevideo")
    
    # Cargar datos
    df = load_data()
    
    if df is not None:
        # Preprocesar datos
        df = create_date_column(df)
        
        # Sidebar con filtros
        st.sidebar.title("Filtros")
        
        # Obtener opciones únicas para filtros
        ecocentros = ["Todos"] + sorted(df['ecocentro'].unique().tolist())
        residuos = ["Todos"] + sorted(df['residuo'].unique().tolist())
        anios = ["Todos"] + sorted(df['anio'].unique().astype(str).tolist())
        
        # Crear filtros
        selected_ecocentro = st.sidebar.selectbox("Ecocentro", ecocentros)
        selected_residuo = st.sidebar.selectbox("Tipo de Residuo", residuos)
        selected_anio = st.sidebar.selectbox("Año", anios)
        
        # Aplicar filtros
        filtered_df = filter_dataframe(df, selected_ecocentro, selected_residuo, selected_anio)
        
        # Mostrar KPIs
        total, promedio, residuo_max, ecocentro_max = create_kpis(filtered_df)
        
        # Layout para KPIs en una fila
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Recolectado", f"{total:,.0f} kg")
        
        with col2:
            st.metric("Promedio Mensual", f"{promedio:,.0f} kg")
        
        with col3:
            st.metric("Residuo Más Recolectado", residuo_max)
        
        with col4:
            st.metric("Ecocentro Más Activo", ecocentro_max)
        
        # Gráficos en la primera fila
        col1, col2 = st.columns(2)
        
        with col1:
            time_series_fig = create_time_series(filtered_df)
            st.plotly_chart(time_series_fig, use_container_width=True)
        
        with col2:
            residuo_fig = create_residuo_distribution(filtered_df)
            st.plotly_chart(residuo_fig, use_container_width=True)
        
        # Gráficos en la segunda fila
        col1, col2 = st.columns(2)
        
        with col1:
            ecocentro_fig = create_ecocentros_comparison(filtered_df)
            st.plotly_chart(ecocentro_fig, use_container_width=True)
        
        with col2:
            anual_fig = create_anual_comparison(filtered_df)
            st.plotly_chart(anual_fig, use_container_width=True)
        
        # Datos detallados
        st.subheader("Datos Detallados")
        st.dataframe(
            filtered_df[['ecocentro', 'anio', 'mes_nombre', 'residuo', 'kg']]
            .sort_values(['anio', 'mes'], ascending=[False, False])
            .head(1000),
            use_container_width=True
        )
        
        # Información sobre los datos
        with st.expander("Acerca de los datos"):
            st.write("""
            Estos datos muestran la cantidad de residuos (en kilogramos) recolectados en los ecocentros de Montevideo.
            
            - **Ecocentros disponibles**: {}
            - **Tipos de residuos**: {}
            - **Rango de fechas**: {} a {}
            - **Total de registros**: {}
            """.format(
                ", ".join(df['ecocentro'].unique()),
                len(df['residuo'].unique()),
                df['fecha'].min().strftime('%B %Y'),
                df['fecha'].max().strftime('%B %Y'),
                len(df)
            ))
    else:
        st.error("No se pudieron cargar los datos. Por favor, verifica que el archivo CSV esté disponible.")

if __name__ == "__main__":
    main()