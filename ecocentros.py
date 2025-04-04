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
    
    # Cargar datos desde Google Drive
    with st.spinner("Cargando datos desde Google Drive..."):
        df, error_message = load_data_from_gdrive()
    
    if df is not None:
        # Preprocesar datos
        df = create_date_column(df)
        
        # Sidebar con filtros
        st.sidebar.title("Filtros")
        
        # Obtener opciones únicas para filtros
        ecocentros = ["Todos"] + sorted(df['ecocentro'].unique().tolist())
        residuos = ["Todos"] + sorted(df['residuo'].unique().tolist())
        anios = ["Todos"] + sorted(df['anio'].unique().astype(str).tolist(), reverse=True)  # Años más recientes primero
        
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
        
        # Primer gráfico: Evolución Mensual
        st.markdown("### Evolución Mensual de Residuos")
        if not filtered_df.empty:
            time_df = filtered_df.groupby(['fecha'])['kg'].sum().reset_index()
            time_df = time_df.sort_values('fecha')  # Ordenar cronológicamente
            st.line_chart(time_df.set_index('fecha'))
        else:
            st.info("No hay datos disponibles para el gráfico de evolución temporal.")
        
        # Segundo gráfico: Comparación Anual
        st.markdown("### Comparación Anual")
        if not filtered_df.empty:
            anual_df = filtered_df.groupby('anio')['kg'].sum().reset_index()
            # Ordenar por año (cronológicamente)
            anual_df = anual_df.sort_values('anio')
            # Gráfico de barras nativo de Streamlit
            st.bar_chart(anual_df.set_index('anio'))
        else:
            st.info("No hay datos disponibles para el gráfico de comparación anual.")
        
        # Tercer gráfico: Top 10 Residuos 
        st.markdown("### Top 10 Tipos de Residuos")
        if not filtered_df.empty:
            # Preparar datos para Top 10 de residuos
            residuo_df = filtered_df.groupby('residuo')['kg'].sum().reset_index()
            residuo_df = residuo_df.sort_values('kg', ascending=False).head(10)
            # Gráfico de barras nativo de Streamlit
            st.bar_chart(residuo_df.set_index('residuo'))
        else:
            st.info("No hay datos disponibles para el gráfico de tipos de residuos.")
        
        # Cuarto gráfico: Comparación entre Ecocentros
        st.markdown("### Comparación entre Ecocentros")
        if not filtered_df.empty:
            # Preparar datos para el gráfico
            ecocentro_df = filtered_df.groupby('ecocentro')['kg'].sum().reset_index()
            
            # Calcular porcentajes
            total_kg = ecocentro_df['kg'].sum()
            ecocentro_df['porcentaje'] = (ecocentro_df['kg'] / total_kg * 100).round(1)
            
            # Ordenar de mayor a menor
            ecocentro_df = ecocentro_df.sort_values('kg', ascending=False)
            
            # Crear representación visual simple
            # Dividir en columnas
            cols = st.columns(len(ecocentro_df))
            
            # Para cada ecocentro, mostrar un contenedor colorido
            for i, (_, row) in enumerate(ecocentro_df.iterrows()):
                with cols[i]:
                    container = st.container()
                    container.markdown(f"<div style='background-color:rgba(0,100,200,{row['porcentaje']/100}); padding:10px; border-radius:5px; height:200px; text-align:center;'>", unsafe_allow_html=True)
                    container.markdown(f"<h3 style='color:white;'>{row['ecocentro']}</h3>", unsafe_allow_html=True)
                    container.markdown(f"<h4 style='color:white;'>{row['kg']:,.0f} kg</h4>", unsafe_allow_html=True)
                    container.markdown(f"<h4 style='color:white;'>{row['porcentaje']}%</h4>", unsafe_allow_html=True)
                    container.markdown("</div>", unsafe_allow_html=True)
            
            # Tabla con información detallada
            st.markdown("#### Detalle por Ecocentro")
            detail_table = ecocentro_df[['ecocentro', 'kg', 'porcentaje']]
            detail_table.columns = ['Ecocentro', 'Kilogramos', 'Porcentaje (%)']
            st.dataframe(detail_table, use_container_width=True)
            
            # Mostrar también un gráfico de barras nativo
            st.bar_chart(ecocentro_df.set_index('ecocentro')['kg'])
            
        else:
            st.info("No hay datos disponibles para el gráfico de comparación de ecocentros.")
        
        # Datos detallados
        st.markdown("### Datos Detallados")
        if not filtered_df.empty:
            # Mostrar los datos ordenados por año y mes (más reciente primero)
            display_df = filtered_df[['ecocentro', 'anio', 'mes_nombre', 'residuo', 'kg']]
            # No ordenamos para evitar errores
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
            st.error("""
            ## Configuración necesaria
            
            Para que este dashboard funcione, debes configurar el ID de archivo de Google Drive:
            
            1. Sube el archivo CSV a Google Drive
            2. Compártelo con "Cualquier persona con el enlace puede ver"
            3. Del enlace compartido (https://drive.google.com/file/d/XXXX/view?usp=sharing), extrae el ID (XXXX)
            4. Reemplaza "TU_ID_DE_ARCHIVO" en el código (línea 14) con el ID obtenido
            """)
        else:
            st.error(f"""
            ## Error al cargar datos
            
            No se pudieron cargar los datos desde Google Drive.
            
            Error: {error_message}
            
            Verifica que:
            1. El ID del archivo ({GDRIVE_FILE_ID}) es correcto
            2. El archivo está compartido públicamente
            3. El formato del archivo es CSV
            """)

if __name__ == "__main__":
    main()