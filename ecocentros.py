import streamlit as st
import pandas as pd
import requests
from io import StringIO

# Configuración de página
st.set_page_config(
    page_title="Dashboard Ecocentros Montevideo",
    page_icon="♻️",
    layout="wide"
)

# Aquí debes reemplazar con la ID de tu archivo en Google Drive
GDRIVE_FILE_ID = "13qduxVDFRice-FYfqeSOSKJRBkmeO2RU"  # Reemplaza esto con tu ID de archivo
GDRIVE_URL = f"https://drive.google.com/uc?export=download&id={GDRIVE_FILE_ID}"

# Función para cargar datos de ejemplo
def load_sample_data():
    data = {
        'ecocentro': ['Buceo', 'Buceo', 'Prado', 'Prado', 'Móviles', 'Móviles', 'Buceo', 'Prado', 'Buceo', 'Prado'],
        'mes': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        'anio': [2023, 2023, 2023, 2024, 2024, 2024, 2025, 2025, 2025, 2025],
        'residuo': ['Electrónicos grandes', 'Muebles y colchones', 'Escombros', 'Restos de jardinería y poda', 
                    'Papel', 'Plásticos PET', 'Metales', 'Envases de vidrio', 'Ropa y calzado', 'Otros objetos'],
        'kg': [5600, 4800, 8900, 12500, 3200, 2800, 4300, 6700, 1900, 2300]
    }
    return pd.DataFrame(data)

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

# Función para cargar datos desde Google Drive
@st.cache_data(ttl=3600)  # Cache por 1 hora
def load_data_from_gdrive():
    try:
        response = requests.get(GDRIVE_URL)
        
        if response.status_code == 200:
            content = StringIO(response.content.decode('utf-8'))
            df = pd.read_csv(content)
            return df, None
        else:
            return None, f"No se pudo acceder al archivo en Google Drive (Código {response.status_code})"
                
    except UnicodeDecodeError:
        try:
            # Intentar con codificación latina
            content = StringIO(response.content.decode('latin1'))
            df = pd.read_csv(content)
            return df, None
        except Exception as e:
            return None, f"Error de codificación: {e}"
    except Exception as e:
        return None, f"Error al cargar datos desde Google Drive: {e}"

# Función para cargar datos desde archivo subido (sin cache)
def load_data_from_file(uploaded_file):
    try:
        df = pd.read_csv(uploaded_file, encoding='utf-8')
        return df, None
    except UnicodeDecodeError:
        try:
            # Reiniciar el puntero del archivo
            uploaded_file.seek(0)
            df = pd.read_csv(uploaded_file, encoding='latin1')
            return df, None
        except Exception as e:
            return None, f"Error al leer el archivo: {e}"

# Función para crear fecha completa
def create_date_column(df):
    if df is None:
        return None
        
    df = df.copy()
    # Crear columna de fecha para ordenar cronológicamente
    df['fecha'] = pd.to_datetime([f"{year}-{month}-01" for year, month in zip(df.anio, df.mes)])
    df['mes_nombre'] = df['mes'].map(MESES)
    df['periodo'] = df['mes_nombre'] + ' ' + df['anio'].astype(str)
    return df

# Función para aplicar filtros
def filter_dataframe(df, ecocentro, residuo, anio):
    if df is None:
        return None
        
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
    if df is None or df.empty:
        return 0, 0, "N/A", "N/A"
        
    # Total recolectado
    total_recolectado = df['kg'].sum()
    
    # Promedio mensual
    monthly_data = df.groupby(['anio', 'mes'])['kg'].sum().reset_index()
    promedio_mensual = monthly_data['kg'].mean() if not monthly_data.empty else 0
    
    # Residuo más recolectado
    residuo_counts = df.groupby('residuo')['kg'].sum()
    residuo_mas_recolectado = residuo_counts.idxmax() if not residuo_counts.empty else "N/A"
    
    # Ecocentro más activo
    ecocentro_counts = df.groupby('ecocentro')['kg'].sum()
    ecocentro_mas_activo = ecocentro_counts.idxmax() if not ecocentro_counts.empty else "N/A"
    
    return total_recolectado, promedio_mensual, residuo_mas_recolectado, ecocentro_mas_activo

# Función principal
def main():
    # Título y descripción
    st.title("Dashboard de Ecocentros - Montevideo")
    st.markdown("Visualización de datos de residuos recolectados en los ecocentros de Montevideo")
    
    # Opciones para cargar datos
    st.sidebar.title("Cargar Datos")
    
    # Solo mostrar opción de Google Drive si se ha configurado el ID
    data_options = ["Subir archivo CSV", "Usar datos de ejemplo"]
    if GDRIVE_FILE_ID != "TU_ID_DE_ARCHIVO":
        data_options.insert(0, "Cargar desde Google Drive")
    
    data_source = st.sidebar.radio(
        "Selecciona la fuente de datos:",
        data_options
    )
    
    df = None
    error_message = None
    
    # Cargar datos según la opción seleccionada
    if data_source == "Cargar desde Google Drive":
        st.sidebar.info("Intentando cargar datos desde Google Drive...")
        df, error_message = load_data_from_gdrive()
        if df is not None:
            st.sidebar.success("Datos cargados correctamente desde Google Drive")
        else:
            st.sidebar.error(error_message)
    
    elif data_source == "Subir archivo CSV":
        uploaded_file = st.sidebar.file_uploader("Sube el archivo CSV:", type=['csv'])
        if uploaded_file is not None:
            df, error_message = load_data_from_file(uploaded_file)
            if df is not None:
                st.sidebar.success("Archivo cargado correctamente")
            else:
                st.sidebar.error(error_message)
                
    elif data_source == "Usar datos de ejemplo":
        df = load_sample_data()
        st.sidebar.success("Datos de ejemplo cargados")
    
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
            time_df = filtered_df.groupby(['fecha'])['kg'].sum().reset_index()
            time_df = time_df.sort_values('fecha')
            
            if not time_df.empty:
                st.line_chart(time_df.set_index('fecha'))
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
            # Mostrar los datos sin ordenar para evitar errores
            display_df = filtered_df[['ecocentro', 'anio', 'mes_nombre', 'residuo', 'kg']]
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
            """)
    else:
        if GDRIVE_FILE_ID == "TU_ID_DE_ARCHIVO":
            st.warning("""
            **Instrucciones de configuración:**
            
            1. Sube el archivo CSV a Google Drive
            2. Compártelo con "Cualquier persona con el enlace puede ver"
            3. Obtén el ID del archivo del enlace de Google Drive
            4. Reemplaza "TU_ID_DE_ARCHIVO" en el código (línea 14) con el ID obtenido
            
            Mientras tanto, puedes utilizar las opciones de carga manual o datos de ejemplo.
            """)
        else:
            st.warning("""
            Selecciona una opción para cargar los datos en el panel lateral.
            """)

if __name__ == "__main__":
    main()