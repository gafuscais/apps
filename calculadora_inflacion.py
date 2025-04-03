import streamlit as st
import pandas as pd
import numpy as np

# Función para formatear moneda con símbolo $ fijo
def formato_moneda(valor):
    return f"${float(valor):,.2f}"

# Configuración de la página
st.set_page_config(
    page_title="Calculadora de Presupuesto Ajustado por Inflación",
    layout="wide"
)

# Título principal
st.title("Calculadora de Presupuesto Ajustado por Inflación")

# Crear tres columnas para los inputs
col1, col2, col3 = st.columns(3)

with col1:
    presupuesto_actual = st.number_input(
        "Presupuesto Actual ($)",
        min_value=0.0,
        value=10000.0,
        step=100.0,
        format="%.2f"
    )

with col2:
    inflacion_anual = st.number_input(
        "Inflación Anual Proyectada (%)",
        min_value=0.0,
        max_value=100.0,
        value=3.5,
        step=0.1,
        format="%.1f"
    )

with col3:
    periodo_anios = st.number_input(
        "Período (Años)",
        min_value=1,
        max_value=30,
        value=5,
        step=1
    )

# Botón para calcular
calcular = st.button("Calcular Presupuesto Ajustado", type="primary", use_container_width=True)

# Función de cálculo
if calcular or ('resultados' in st.session_state):
    # Calcular resultados
    inflacion = inflacion_anual / 100
    datos_anuales = []
    presupuesto_ajustado = presupuesto_actual
    
    for i in range(periodo_anios + 1):
        if i == 0:
            datos_anuales.append({
                "anio": "Actual",
                "presupuesto": presupuesto_actual,
                "presupuesto_formato": formato_moneda(presupuesto_actual),
                "incremento": 0.0,
                "incremento_formato": formato_moneda(0.0),
                "poder_adquisitivo": "100.00%"
            })
        else:
            incremento_anual = presupuesto_ajustado * inflacion
            presupuesto_ajustado = presupuesto_ajustado + incremento_anual
            
            # Calcular poder adquisitivo si no se ajusta el presupuesto
            if i == periodo_anios and inflacion > 0:
                poder_adquisitivo = "100.00%"
            else:
                poder_adquisitivo = f"{((presupuesto_actual / (presupuesto_actual * pow(1 + inflacion, i))) * 100):.2f}%"
            
            datos_anuales.append({
                "anio": f"Año {i}",
                "presupuesto": presupuesto_ajustado,
                "presupuesto_formato": formato_moneda(presupuesto_ajustado),
                "incremento": incremento_anual,
                "incremento_formato": formato_moneda(incremento_anual),
                "poder_adquisitivo": poder_adquisitivo
            })
    
    # Guardar resultados en session_state para mantenerlos si se recarga la página
    st.session_state.resultados = {
        "presupuesto_final": presupuesto_ajustado,
        "presupuesto_final_formato": formato_moneda(presupuesto_ajustado),
        "incremento_total": (presupuesto_ajustado - presupuesto_actual),
        "incremento_total_formato": formato_moneda(presupuesto_ajustado - presupuesto_actual),
        "datos_anuales": datos_anuales
    }
    
    # Mostrar resultados principales
    col_result1, col_result2 = st.columns(2)
    
    with col_result1:
        st.metric(
            label="Presupuesto Final Ajustado",
            value=st.session_state.resultados['presupuesto_final_formato']
        )
    
    with col_result2:
        st.metric(
            label="Incremento Total Necesario",
            value=st.session_state.resultados['incremento_total_formato']
        )
    
    # Convertir los datos anuales a un DataFrame para mostrarlos
    df = pd.DataFrame([{
        "Período": row["anio"],
        "Presupuesto": row["presupuesto_formato"],
        "Incremento": row["incremento_formato"],
        "Poder Adquisitivo Sin Ajuste": row["poder_adquisitivo"]
    } for row in st.session_state.resultados["datos_anuales"]])
    
    # Mostrar tabla con resultados detallados
    with st.expander("Ver Detalles Anuales", expanded=True):
        st.dataframe(df, use_container_width=True)
    
    # Nota informativa
    st.info("**Nota:** Este cálculo asume una tasa de inflación constante durante todo el período. El presupuesto ajustado representa la cantidad necesaria para mantener el mismo poder adquisitivo que el presupuesto actual tiene hoy.")
    
    # Visualización gráfica de los resultados
    st.subheader("Gráfico de Evolución del Presupuesto")
    
    # Preparar datos para gráfico
    chart_data = pd.DataFrame({
        'Período': [row['anio'] for row in datos_anuales],
        'Presupuesto Ajustado': [row['presupuesto'] for row in datos_anuales],
        'Poder Adquisitivo': [float(row['poder_adquisitivo'].replace('%', '')) for row in datos_anuales]
    })
    
    # Gráfico de líneas para el presupuesto
    st.line_chart(chart_data.set_index('Período')['Presupuesto Ajustado'])
    
    # Gráfico de barras para el poder adquisitivo
    if periodo_anios > 1:
        st.subheader("Poder Adquisitivo Sin Ajuste por Inflación")
        poder_chart = pd.DataFrame({
            'Período': chart_data['Período'],
            'Poder Adquisitivo (%)': chart_data['Poder Adquisitivo']
        }).set_index('Período')
        st.bar_chart(poder_chart)
    
    # Exportar como CSV
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Descargar resultados como CSV",
        data=csv,
        file_name="presupuesto_inflacion.csv",
        mime="text/csv",
    )