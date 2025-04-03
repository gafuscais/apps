import streamlit as st
import pandas as pd
from datetime import datetime
import requests
from io import StringIO

# Configuración de página y codificación UTF-8
st.set_page_config(
    page_title="Dashboard Ecocentros Montevideo",
    page_icon="♻️",
    layout="wide"
)

# URLs para los datos
DATA_URL = "https://ckan-data.montevideo.gub.uy/dataset/0a4cdc0a-ec35-4517-9e90-081659188ac0/resource/9eb3e81c-b916-4c6d-9f40-31dabebc708d/download/tabla_de_datos_de_material_ingresado_a_ecocentros.csv"
DATASET_PAGE_URL = "https://ckan-data.montevideo.gub.uy/dataset/ecocentros"

# Función para cargar datos de prueba cuando la URL está bloqueada
def load_sample_data():
    # Creamos algunos datos de ejemplo que imitan la estructura del dataset original
    data = {
        'ecocentro': ['Buceo', 'Buceo', 'Prado', 'Prado', 'Móviles', 'Móviles', 'Buceo', 'Prado', 'Buceo', 'Prado'],
        'mes': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        'anio': [2023, 2023, 2023, 2024, 2024, 2024, 2025, 2025, 2025, 2025],
        'residuo': ['Electrónicos grandes', 'Muebles y colchones', 'Escombros', 'Restos de jardinería y poda', 
                    'Papel', 'Plásticos PET', 'Metales', 'Envases de vidrio', 'Ropa y calzado', 'Otros objetos'],
        'kg': [5600, 4800, 8900, 12500, 3200, 2800, 4300, 6700, 1900, 2300]
    }
    return pd.DataFrame(data)

# Función para cargar los datos con manejo de bloqueos
@st.cache_data(ttl=3600)  # Cache por 1 hora
def load_data():
    # Primero intentamos cargar desde la URL original
    try:
        with st.spinner('Intentando descargar datos desde la URL original...'):
            # Configurar headers para simular un navegador
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3',
                'Referer': DATASET_PAGE_URL
            }
            
            response = requests.get(DATA_URL, headers=headers, timeout=10)
            response.raise_for_status()  # Verificar si la descarga fue exitosa
            
            # Convertir el contenido a un DataFrame con codificación UTF-8
            content = StringIO(response.text)
            df = pd.read_csv(content, encoding='utf-8')
            st.success('Datos cargados correctamente desde la URL original.')
            return df
    
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 403:
            st.warning(f"Acceso bloqueado (Error 403) a la URL original. Verifica si puedes descargar manualmente el archivo desde: [Catálogo de Datos Abiertos]({DATASET_PAGE_URL})")
            
            # Opción para cargar archivo local
            uploaded_file = st.file_uploader("Sube el archivo CSV descargado manualmente:", type=['csv'])
            if uploaded_file is not None:
                try:
                    # Intentar diferentes codificaciones
                    try:
                        df = pd.read_csv(uploaded_file, encoding='utf-8')
                    except UnicodeDecodeError:
                        try:
                            # Reiniciar el puntero del archivo antes de intentar con otra codificación
                            uploaded_file.seek(0)
                            df = pd.read_csv(uploaded_file, encoding='latin1')
                        except UnicodeDecodeError:
                            # Reiniciar el puntero del archivo antes de intentar con otra codificación
                            uploaded_file.seek(0)
                            df = pd.read_csv(uploaded_file, encoding='ISO-8859-1')
                    
                    st.success('Archivo cargado correctamente.')
                    return df
                except Exception as upload_error:
                    st.error(f"Error al procesar el archivo subido: {upload_error}")
                    
            # Opción para usar datos de prueba
            if st.button("Usar datos de ejemplo para demostración"):
                st.info("Usando datos de ejemplo para demostración. Estos NO son los datos reales.")
                return load_sample_data()
                
        else:
            st.error(f"Error HTTP al acceder a los datos: {e}")
    
    except Exception as e:
        st.error(f"Error general al cargar los datos: {e}")
    
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
    if df is not None:
        # Asegurarse de que 'anio' y 'mes' existen y son numéricos
        if 'anio' in df.columns and 'mes' in df.columns:
            # Convertir a numérico si no lo son
            df['anio'] = pd.to_numeric(df['anio'], errors='coerce')
            df['mes'] = pd.to_numeric(df['mes'], errors='coerce')
            
            # Crear columna de fecha
            df['fecha'] = pd.to_datetime(
                [f"{int(year)}-{int(month)}-01" for year, month in zip(df.anio, df.mes)], 
                errors='coerce'
            )
            
            # Crear columna de nombre de mes
            df['mes_nombre'] = df['mes'].map(MESES)
            
            # Crear columna de período
            df['periodo'] = df['mes_nombre'] + ' ' + df['anio'].astype(str)
    
    return df

def filter_dataframe(df, ecocentro, residuo, anio):
    if df is None:
        return pd.DataFrame()
        
    filtered_df = df.copy()
    
    if ecocentro != "Todos":
        filtered_df = filtered_df[filtered_df.ecocentro == ecocentro]
    
    if residuo != "Todos":
        filtered_df = filtered_df[filtered_df.residuo == residuo]
    
    if anio != "Todos":
        filtered_df = filtered_df[filtered_df.anio == int(anio)]
    
    return filtered_df

def create_kpis(df):
    if df is None or df.empty:
        return 0, 0, "N/A", "N/A"
        
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
    st.markdown(f"**Fuente de datos:** [Catálogo de Datos Abiertos de Montevideo]({DATASET_PAGE_URL})")
    
    # Cargar datos
    df = load_data()
    
    if df is not None:
        # Mostrar información básica sobre las columnas disponibles
        st.sidebar.markdown("#### Columnas disponibles")
        st.sidebar.write(", ".join(df.columns.tolist()))
        
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
            # Verificar columnas disponibles antes de intentar acceder a ellas
            display_columns = ['ecocentro', 'anio', 'residuo', 'kg']
            
            # Añadir 'mes_nombre' solo si existe
            if 'mes_nombre' in filtered_df.columns:
                display_columns.insert(2, 'mes_nombre')
            
            # Crear DataFrame para mostrar
            display_df = filtered_df[display_columns]
            
            # Ordenar solo por columnas que existen
            sort_columns = []
            if 'anio' in filtered_df.columns:
                sort_columns.append('anio')
            if 'mes' in filtered_df.columns:
                sort_columns.append('mes')
                
            if sort_columns:
                display_df = display_df.sort_values(
                    sort_columns, 
                    ascending=[False] * len(sort_columns)
                )
            
            st.dataframe(display_df, use_container_width=True)
            st.write(f"Mostrando {len(display_df)} de {len(filtered_df)} registros")
        else:
            st.info("No hay datos disponibles que coincidan con los filtros seleccionados.")
        
        # Información sobre los datos
        with st.expander("Acerca de los datos"):
            min_date = "No disponible"
            max_date = "No disponible"
            
            if 'fecha' in df.columns and not df['fecha'].isna().all():
                min_date = df['fecha'].min().strftime('%Y-%m') if not pd.isna(df['fecha'].min()) else "No disponible"
                max_date = df['fecha'].max().strftime('%Y-%m') if not pd.isna(df['fecha'].max()) else "No disponible"
            
            st.write(f"""
            ### Información del dataset
            
            Estos datos muestran la cantidad de residuos (en kilogramos) recolectados en los ecocentros de Montevideo.
            
            **Características del dataset:**
            - **Ecocentros disponibles**: {", ".join(df['ecocentro'].unique())}
            - **Tipos de residuos**: {len(df['residuo'].unique())}
            - **Rango de fechas**: {min_date} a {max_date}
            - **Total de registros**: {len(df)}
            
            **Fuente original:**
            Los datos se obtienen del [Catálogo de Datos Abiertos de Montevideo]({DATASET_PAGE_URL}).
            """)
    else:
        st.error("No se pudieron cargar los datos y no se seleccionó usar los datos de ejemplo.")
        
        # Información de solución de problemas
        st.markdown("### Solución de problemas")
        st.markdown(f"""
        El acceso directo a los datos mediante programación está bloqueado por el servidor (Error 403 Forbidden).
        
        ### Opciones para obtener los datos:
        
        1. **Descarga manual**: Visita la [página del dataset]({DATASET_PAGE_URL}) y descarga el archivo CSV manualmente.
           - Luego sube el archivo usando el cargador proporcionado arriba.
        
        2. **Usa datos de ejemplo**: Puedes probar la funcionalidad del dashboard con datos de ejemplo haciendo clic en el botón "Usar datos de ejemplo para demostración".
        
        3. **Solución técnica**: Si eres administrador, puedes modificar este código para:
           - Alojar una copia del CSV en tu propio servidor
           - Crear una API proxy que obtenga los datos y evite las restricciones CORS
           - Configurar un proceso de ETL que extraiga los datos periódicamente
        """)

if __name__ == "__main__":
    main()