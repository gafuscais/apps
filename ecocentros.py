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

# URLs para los datos
DATASET_PAGE_URL = "https://catalogodatos.gub.uy/dataset/ecocentros/resource/9eb3e81c-b916-4c6d-9f40-31dabebc708d"

# Función para cargar datos de ejemplo
def load_sample_data():
    # Datos de ejemplo simplificados
    data = {
        'ecocentro': ['Buceo', 'Buceo', 'Prado', 'Prado', 'Móviles'],
        'mes': [1, 2, 3, 4, 5],
        'anio': [2023, 2023, 2023, 2024, 2024],
        'residuo': ['Electrónicos', 'Muebles', 'Escombros', 'Poda', 'Papel'],
        'kg': [5600, 4800, 8900, 12500, 3200]
    }
    return pd.DataFrame(data)

# Función para cargar los datos
@st.cache_data(ttl=3600)
def load_data():
    # Primero intentamos el archivo cargado por el usuario
    uploaded_file = st.file_uploader("Sube el archivo CSV:", type=['csv'])
    
    if uploaded_file is not None:
        try:
            # Intentar diferentes codificaciones
            encodings = ['utf-8', 'latin1', 'ISO-8859-1', 'cp1252']
            df = None
            
            for encoding in encodings:
                try:
                    # Reiniciar el puntero del archivo antes de cada intento
                    uploaded_file.seek(0)
                    df = pd.read_csv(uploaded_file, encoding=encoding)
                    st.success(f'Archivo cargado correctamente con codificación {encoding}.')
                    break
                except UnicodeDecodeError:
                    continue
            
            if df is None:
                st.error("No se pudo determinar la codificación del archivo.")
                return None
                
            return df
        except Exception as upload_error:
            st.error(f"Error al procesar el archivo: {upload_error}")
            return None
    
    # Si no hay archivo cargado, ofrecer usar datos de ejemplo
    if st.button("Usar datos de ejemplo para demostración"):
        st.info("Usando datos de ejemplo para demostración. Estos NO son los datos reales.")
        return load_sample_data()
    
    # Si no hay archivo ni se eligió usar datos de ejemplo
    return None

# Función para filtrar datos de manera segura
def safe_filter_dataframe(df, ecocentro, residuo, anio):
    if df is None or df.empty:
        return pd.DataFrame()
    
    # Crear una copia para no modificar el original    
    filtered_df = df.copy()
    
    # Filtrar solo si las columnas existen
    if 'ecocentro' in filtered_df.columns and ecocentro != "Todos":
        filtered_df = filtered_df[filtered_df['ecocentro'] == ecocentro]
    
    if 'residuo' in filtered_df.columns and residuo != "Todos":
        filtered_df = filtered_df[filtered_df['residuo'] == residuo]
    
    if 'anio' in filtered_df.columns and anio != "Todos":
        # Convertir a numérico si es posible
        if filtered_df['anio'].dtype == 'object':
            try:
                filtered_df['anio'] = pd.to_numeric(filtered_df['anio'], errors='coerce')
                filtered_df = filtered_df.dropna(subset=['anio'])
            except:
                pass
                
        # Filtrar solo si la conversión fue exitosa
        if pd.api.types.is_numeric_dtype(filtered_df['anio']):
            try:
                anio_val = int(anio)
                filtered_df = filtered_df[filtered_df['anio'] == anio_val]
            except:
                pass
            
    return filtered_df

# Función principal
def main():
    # Título y descripción
    st.title("Dashboard de Ecocentros - Montevideo")
    st.markdown("Visualización de datos de residuos recolectados en los ecocentros de Montevideo")
    
    # Información sobre la fuente de datos
    st.markdown(f"**Fuente de datos:** [Catálogo de Datos Abiertos de Montevideo]({DATASET_PAGE_URL})")
    
    # Instrucciones
    st.info("""
    **Instrucciones:**
    1. Descarga manualmente el archivo CSV desde el [Catálogo de Datos de Montevideo](https://ckan-data.montevideo.gub.uy/dataset/ecocentros)
    2. Sube el archivo usando el cargador de archivos a continuación
    3. O utiliza los datos de ejemplo para probar la funcionalidad
    """)
    
    # Cargar datos
    df = load_data()
    
    if df is not None:
        # Mostrar información sobre las columnas disponibles
        st.sidebar.markdown("### Columnas detectadas:")
        st.sidebar.write(", ".join(df.columns.tolist()))
        
        # Sidebar con filtros
        st.sidebar.title("Filtros")
        
        # Determinar opciones de filtros de manera segura
        ecocentros = ["Todos"]
        residuos = ["Todos"]
        anios = ["Todos"]
        
        if 'ecocentro' in df.columns:
            ecocentros += sorted(df['ecocentro'].unique().tolist())
        
        if 'residuo' in df.columns:
            residuos += sorted(df['residuo'].unique().tolist())
        
        if 'anio' in df.columns:
            # Convertir a numérico si es posible
            if df['anio'].dtype == 'object':
                try:
                    anio_values = pd.to_numeric(df['anio'], errors='coerce')
                    anio_values = anio_values.dropna().unique()
                    anios += sorted([str(int(x)) for x in anio_values])
                except:
                    anios += sorted(df['anio'].unique().astype(str).tolist())
            else:
                anios += sorted(df['anio'].unique().astype(str).tolist())
        
        # Crear filtros
        selected_ecocentro = st.sidebar.selectbox("Ecocentro", ecocentros)
        selected_residuo = st.sidebar.selectbox("Tipo de Residuo", residuos)
        selected_anio = st.sidebar.selectbox("Año", anios)
        
        # Aplicar filtros de manera segura
        filtered_df = safe_filter_dataframe(df, selected_ecocentro, selected_residuo, selected_anio)
        
        # Mostrar KPIs
        if 'kg' in filtered_df.columns:
            st.markdown("### Indicadores Clave")
            col1, col2, col3, col4 = st.columns(4)
            
            # Total recolectado
            total_kg = filtered_df['kg'].sum()
            with col1:
                st.metric("Total Recolectado", f"{total_kg:,.0f} kg")
            
            # Promedio
            promedio = 0
            if 'anio' in filtered_df.columns and 'mes' in filtered_df.columns:
                try:
                    monthly_data = filtered_df.groupby(['anio', 'mes'])['kg'].sum().reset_index()
                    promedio = monthly_data['kg'].mean()
                except:
                    promedio = filtered_df['kg'].mean()
            else:
                promedio = filtered_df['kg'].mean()
                
            with col2:
                st.metric("Promedio", f"{promedio:,.0f} kg")
            
            # Residuo más frecuente
            residuo_max = "N/A"
            if 'residuo' in filtered_df.columns:
                try:
                    residuo_counts = filtered_df.groupby('residuo')['kg'].sum()
                    residuo_max = residuo_counts.idxmax() if not residuo_counts.empty else "N/A"
                except:
                    pass
                
            with col3:
                st.metric("Residuo Principal", residuo_max)
            
            # Ecocentro más activo
            ecocentro_max = "N/A"
            if 'ecocentro' in filtered_df.columns:
                try:
                    ecocentro_counts = filtered_df.groupby('ecocentro')['kg'].sum()
                    ecocentro_max = ecocentro_counts.idxmax() if not ecocentro_counts.empty else "N/A"
                except:
                    pass
                
            with col4:
                st.metric("Ecocentro Principal", ecocentro_max)
        
        # Visualizaciones - Solo si existen las columnas necesarias
        if not filtered_df.empty and 'kg' in filtered_df.columns:
            # Primera fila de gráficos
            st.markdown("### Visualización de Datos")
            col1, col2 = st.columns(2)
            
            # Gráfico por año/mes si están disponibles
            with col1:
                if 'anio' in filtered_df.columns and 'mes' in filtered_df.columns:
                    st.subheader("Evolución Temporal")
                    try:
                        # Intentar agrupar por año y mes
                        filtered_df['periodo'] = filtered_df['anio'].astype(str) + "-" + filtered_df['mes'].astype(str).str.zfill(2)
                        time_df = filtered_df.groupby('periodo')['kg'].sum().reset_index()
                        time_df = time_df.sort_values('periodo')
                        st.line_chart(time_df.set_index('periodo'))
                    except Exception as e:
                        st.warning(f"No se pudo generar el gráfico temporal: {e}")
                else:
                    st.info("No hay datos suficientes para mostrar evolución temporal (se requieren columnas 'anio' y 'mes').")
            
            # Gráfico por tipo de residuo si está disponible
            with col2:
                if 'residuo' in filtered_df.columns:
                    st.subheader("Distribución por Tipo de Residuo")
                    try:
                        # Top 10 tipos de residuo
                        residuo_df = filtered_df.groupby('residuo')['kg'].sum().reset_index()
                        residuo_df = residuo_df.sort_values('kg', ascending=False).head(10)
                        st.bar_chart(residuo_df.set_index('residuo'))
                    except Exception as e:
                        st.warning(f"No se pudo generar el gráfico de residuos: {e}")
                else:
                    st.info("No hay datos suficientes para mostrar distribución por residuo (se requiere columna 'residuo').")
            
            # Segunda fila de gráficos
            col1, col2 = st.columns(2)
            
            # Gráfico por ecocentro si está disponible
            with col1:
                if 'ecocentro' in filtered_df.columns:
                    st.subheader("Comparación entre Ecocentros")
                    try:
                        ecocentro_df = filtered_df.groupby('ecocentro')['kg'].sum().reset_index()
                        st.bar_chart(ecocentro_df.set_index('ecocentro'))
                    except Exception as e:
                        st.warning(f"No se pudo generar el gráfico de ecocentros: {e}")
                else:
                    st.info("No hay datos suficientes para mostrar comparación entre ecocentros (se requiere columna 'ecocentro').")
            
            # Gráfico por año si está disponible
            with col2:
                if 'anio' in filtered_df.columns:
                    st.subheader("Comparación Anual")
                    try:
                        anual_df = filtered_df.groupby('anio')['kg'].sum().reset_index()
                        anual_df['anio'] = anual_df['anio'].astype(str)  # Convertir a string para graficación
                        st.bar_chart(anual_df.set_index('anio'))
                    except Exception as e:
                        st.warning(f"No se pudo generar el gráfico anual: {e}")
                else:
                    st.info("No hay datos suficientes para mostrar comparación anual (se requiere columna 'anio').")
        
        # Datos detallados
        st.markdown("### Datos Detallados")
        if not filtered_df.empty:
            # Mostrar todas las columnas disponibles sin intentar ordenarlas
            st.dataframe(filtered_df, use_container_width=True)
            st.write(f"Mostrando {len(filtered_df)} de {len(df)} registros")
        else:
            st.info("No hay datos disponibles que coincidan con los filtros seleccionados.")
    else:
        st.warning("No se han cargado datos. Por favor, sube un archivo CSV o usa los datos de ejemplo.")

if __name__ == "__main__":
    main()