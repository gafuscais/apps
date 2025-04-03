import streamlit as st
import pandas as pd
from datetime import datetime
import requests
from io import StringIO

# Configuración de página
st.set_page_config(
    page_title="Dashboard Ecocentros Montevideo",
    page_icon="♻️",
    layout="wide"
)

# URL de los datos
DATA_URL = "https://ckan-data.montevideo.gub.uy/dataset/0a4cdc0a-ec35-4517-9e90-081659188ac0/resource/9eb3e81c-b916-4c6d-9f40-31dabebc708d/download/tabla_de_datos_de_material_ingresado_a_ecocentros.csv"

# Función para cargar los datos desde la URL
@st.cache_data(ttl=3600)  # Cache por 1 hora
def load_data_from_url(url):
    try:
        # Mostrar mensaje mientras se cargan los datos
        with st.spinner('Descargando datos desde la URL...'):
            # Descargar datos desde la URL
            response = requests.get(url)
            response.raise_for_status()  # Verificar si la descarga fue exitosa
            
            # Convertir el contenido a un DataFrame
            content = StringIO(response.text)
            df = pd.read_csv(content)
            
            st.success('Datos cargados correctamente')
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
    # Crear columna de fecha para ordenar cronológicamente
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

# Función para crear KPIs
def create_kpis(df):
    # Total recolectado
    total_recolectado = df['kg'].sum()
    
    # Promedio mensual
    monthly_data = df.groupby(['anio', 'mes'])['kg'].sum().reset_index()
    promedio_mensual = monthly_data['kg'].mean() if not monthly_data.empty else 0
    
    # Residuo más recolectado
    if not df.empty:
        residuo_counts = df.groupby('residuo')['kg'].sum()
        residuo_mas_recolectado = residuo_counts.idxmax() if not residuo_counts.empty else "N/A"
    else:
        residuo_mas_recolectado = "N/A"
    
    # Ecocentro más activo
    if not df.empty:
        ecocentro_counts = df.groupby('ecocentro')['kg'].sum()
        ecocentro_mas_activo = ecocentro_counts.idxmax() if not ecocentro_counts.empty else "N/A"
    else:
        ecocentro_mas_activo = "N/A"
    
    return total_recolectado, promedio_mensual, residuo_mas_recolectado, ecocentro_mas_activo

# Función principal
def main():
    # Título y descripción
    st.title("Dashboard de Ecocentros - Montevideo")
    st.markdown("Visualización de datos de residuos recolectados en los ecocentros de Montevideo")
    
    # Información sobre la fuente de datos
    st.markdown(f"**Fuente de datos:** [Catálogo de Datos Abiertos de Montevideo]({DATA_URL})")
    
    # Cargar datos desde la URL
    df = load_data_from_url(DATA_URL)
    
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
        st.markdown("### Indicadores Clave")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Recolectado", f"{total:,.0f} kg")
        
        with col2:
            st.metric("Promedio Mensual", f"{promedio:,.0f} kg")
        
        with col3:
            st.metric("Residuo Más Recolectado", residuo_max)
        
        with col4:
            st.metric("Ecocentro Más Activo", ecocentro_max)
        
        # Primera fila de gráficos
        st.markdown("### Evolución Temporal y Tipos de Residuos")
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Evolución Mensual de Residuos")
            # Crear datos para gráfico de evolución temporal
            time_df = filtered_df.groupby(['fecha', 'periodo'])['kg'].sum().reset_index()
            time_df = time_df.sort_values('fecha')
            
            if not time_df.empty:
                st.line_chart(time_df.set_index('fecha')['kg'])
            else:
                st.info("No hay datos disponibles para el gráfico de evolución temporal.")
        
        with col2:
            st.subheader("Top 10 Tipos de Residuos")
            # Crear datos para gráfico de distribución de residuos
            if not filtered_df.empty:
                residuo_df = filtered_df.groupby('residuo')['kg'].sum().reset_index()
                residuo_df = residuo_df.sort_values('kg', ascending=False).head(10)
                st.bar_chart(residuo_df.set_index('residuo'))
            else:
                st.info("No hay datos disponibles para el gráfico de tipos de residuos.")
        
        # Segunda fila de gráficos
        st.markdown("### Comparaciones por Ecocentro y Año")
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Comparación entre Ecocentros")
            # Crear datos para gráfico de comparación de ecocentros
            if not filtered_df.empty:
                ecocentro_df = filtered_df.groupby('ecocentro')['kg'].sum().reset_index()
                st.bar_chart(ecocentro_df.set_index('ecocentro'))
            else:
                st.info("No hay datos disponibles para el gráfico de comparación de ecocentros.")
        
        with col2:
            st.subheader("Comparación Anual")
            # Crear datos para gráfico de comparación anual
            if not filtered_df.empty:
                anual_df = filtered_df.groupby('anio')['kg'].sum().reset_index()
                st.bar_chart(anual_df.set_index('anio'))
            else:
                st.info("No hay datos disponibles para el gráfico de comparación anual.")
        
        # Datos detallados
        st.markdown("### Datos Detallados")
        if not filtered_df.empty:
            display_df = filtered_df[['ecocentro', 'anio', 'mes_nombre', 'residuo', 'kg']].sort_values(['anio', 'mes'], ascending=[False, False])
            st.dataframe(display_df, use_container_width=True)
            st.write(f"Mostrando {len(display_df)} de {len(filtered_df)} registros")
        else:
            st.info("No hay datos disponibles que coincidan con los filtros seleccionados.")
        
        # Información sobre los datos
        with st.expander("Acerca de los datos"):
            st.write(f"""
            ### Información del dataset
            
            Estos datos muestran la cantidad de residuos (en kilogramos) recolectados en los ecocentros de Montevideo.
            
            **Características del dataset:**
            - **Ecocentros disponibles**: {", ".join(df['ecocentro'].unique())}
            - **Tipos de residuos**: {len(df['residuo'].unique())}
            - **Rango de fechas**: {df['fecha'].min().strftime('%Y-%m')} a {df['fecha'].max().strftime('%Y-%m')}
            - **Total de registros**: {len(df)}
            
            **Fuente original:**
            Los datos se obtienen directamente del [Catálogo de Datos Abiertos de Montevideo]({DATA_URL}).
            """)
    else:
        st.error("No se pudieron cargar los datos. Por favor, verifica la conexión a Internet o si la URL del dataset sigue siendo válida.")
        
        # Mostrar URL fallida
        st.code(DATA_URL)
        
        # Información de instalación
        st.markdown("### Solución de problemas")
        st.markdown("""
        Si estás experimentando problemas al cargar los datos desde la URL, asegúrate de:
        
        1. Tener conexión a Internet estable.
        2. Que la URL del dataset sea accesible (es posible que haya cambiado).
        3. Tener instaladas todas las dependencias necesarias:
        ```
        pip install streamlit pandas requests
        ```
        
        Para ejecutar la aplicación correctamente:
        ```
        streamlit run nombre_del_script.py
        ```
        """)

if __name__ == "__main__":
    main()