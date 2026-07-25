# =====================================================================
# app.py - CitaLocal
# ---------------------------------------------------------------------
# INTERFAZ VISUAL del buscador y sintetizador de literatura científica.
# =====================================================================
# Copyright (C) 2026 jbnen3
# Este programa es software libre: puedes redistribuirlo y/o modificarlo
# bajo los términos de la Licencia Pública General de GNU (GPLv3),
# publicada por la Free Software Foundation.
# Ver el archivo LICENSE para más detalles.
import os
import time
import streamlit as st
from core import (
    buscar_literatura, exportar_csv, exportar_ris, exportar_bib, exportar_markdown,
    generar_analisis_imrad, exportar_analisis_md, exportar_analisis_txt, exportar_analisis_docx,
    listar_modelos_ollama, ollama_disponible, TODAS_LAS_FUENTES,
    guardar_busqueda, listar_busquedas_recientes, cargar_busqueda,
    PLANTILLA_NARRATIVA
)
import branding

_icon = branding.ICON_PATH if os.path.exists(branding.ICON_PATH) else "🔬"
st.set_page_config(page_title=branding.APP_NAME, page_icon=_icon, layout="wide")


# =====================================================================
# ESTADO INICIAL
# =====================================================================
for key, default in {
    "resultados": [], "analisis_imrad": None, "busy": False,
    "done_locked": False, "tema": ""
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

INTERFAZ_BLOQUEADA = st.session_state.busy or st.session_state.done_locked


# =====================================================================
# ESTILOS: colores de marca (solo tema claro)
# =====================================================================
BRAND_CSS = f"""
<style>
.stButton button {{ background-color: {branding.COLOR_PRIMARY} !important; color: white !important; border: none; }}
.stButton button:hover {{ background-color: {branding.COLOR_ACCENT} !important; }}
.stButton button:disabled {{ background-color: #b0b0b0 !important; color: #eee !important; }}
</style>
"""
st.markdown(BRAND_CSS, unsafe_allow_html=True)


# =====================================================================
# ENCABEZADO: logo + nombre
# =====================================================================
if os.path.exists(branding.LOGO_PATH):
    st.image(branding.LOGO_PATH, width=280)
else:
    st.title(f"🔬 {branding.APP_NAME}")
st.caption(branding.APP_TAGLINE)


# =====================================================================
# VERIFICACIÓN DE OLLAMA
# =====================================================================
if not ollama_disponible():
    st.error("⚠️ No se detecta Ollama activo. Abre una terminal y ejecuta: `ollama serve`, "
              "luego recarga esta página.")

modelos_disponibles = listar_modelos_ollama()

if st.session_state.done_locked:
    st.warning("🔒 El análisis ha finalizado. La interfaz está bloqueada. "
               "Presiona **'🔄 Nueva búsqueda'** al final de la página para continuar.")


# =====================================================================
# PANEL LATERAL
# =====================================================================
with st.sidebar:
    if os.path.exists(branding.LOGO_PATH):
        st.image(branding.LOGO_PATH, width=180)
    st.header("Parámetros de búsqueda")

    tema_input = st.text_input("Tema de búsqueda", value=st.session_state.tema,
                                placeholder="ej: resistencia a insulina",
                                disabled=INTERFAZ_BLOQUEADA)

    col1, col2 = st.columns(2)
    with col1:
        anio_desde = st.number_input("Año desde", min_value=1950, max_value=2025,
                                      value=2019, disabled=INTERFAZ_BLOQUEADA)
    with col2:
        anio_hasta = st.number_input("Año hasta", min_value=1950, max_value=2025,
                                      value=2025, disabled=INTERFAZ_BLOQUEADA)
    max_por_fuente = st.slider("Resultados máximos por fuente", 5, 50, 20,
                               disabled=INTERFAZ_BLOQUEADA)
    terminos_excluir = st.text_input(
        "Términos a excluir (separados por coma)",
        placeholder="ej: skin, surgical, wound, transplant",
        disabled=INTERFAZ_BLOQUEADA
    )
    st.subheader("Fuentes a consultar")
    st.caption("Todas las fuentes disponibles son gratuitas y de acceso abierto.")
    fuentes_seleccionadas = []
    for nombre in TODAS_LAS_FUENTES.keys():
        if st.checkbox(nombre, value=True, disabled=INTERFAZ_BLOQUEADA, key=f"chk_{nombre}"):
            fuentes_seleccionadas.append(nombre)

    if "CORE" in fuentes_seleccionadas:
        st.caption("CORE requiere una API key gratuita (variable CORE_API_KEY).")

    generar_resumen = False

    buscar = st.button("🔍 Buscar", type="primary", width="stretch",
                        disabled=INTERFAZ_BLOQUEADA)

    st.divider()
    st.subheader("🕑 Búsquedas recientes")
    recientes = listar_busquedas_recientes()
    if not recientes:
        st.caption("Aún no hay búsquedas guardadas.")
    else:
        for item in recientes:
            etiqueta_btn = f"{item['tema'][:28]}  ({item['total']} art.)"
            if st.button(etiqueta_btn, key=item["path"], width="stretch",
                         disabled=INTERFAZ_BLOQUEADA, help=item["fecha"]):
                datos = cargar_busqueda(item["path"])
                st.session_state.resultados = datos["resultados"]
                st.session_state.tema = datos["tema"]
                st.session_state.analisis_imrad = None
                st.session_state.busy = False
                st.session_state.done_locked = False
                st.rerun()


# =====================================================================
# EJECUCIÓN DE LA BÚSQUEDA
# =====================================================================
if buscar and not INTERFAZ_BLOQUEADA:
    if not tema_input.strip():
        st.error("Escribe un tema de búsqueda.")
    else:
        st.session_state.busy = True
        modelo_para_resumen = modelos_disponibles[0]
        estado = st.empty()
        with st.spinner("Buscando..."):
            terminos = [t.strip() for t in terminos_excluir.split(",") if t.strip()]
            resultados = buscar_literatura(
                query=tema_input, max_results=max_por_fuente,
                fuentes_activas=fuentes_seleccionadas,
                year_from=int(anio_desde), year_to=int(anio_hasta),
                generar_resumen=generar_resumen, modelo=modelo_para_resumen,
                excluir=terminos,
                progreso_callback=lambda msg, frac=None: estado.text(msg)
            )
        st.session_state.resultados = resultados
        st.session_state.tema = tema_input
        st.session_state.analisis_imrad = None
        st.session_state.busy = False

        if resultados:
            guardar_busqueda(tema_input, resultados, int(anio_desde), int(anio_hasta))

        estado.text(f"Listo: {len(resultados)} artículos encontrados.")
        st.rerun()

resultados = st.session_state.resultados


# =====================================================================
# TABLA DE RESULTADOS Y DESCARGAS
# =====================================================================
if resultados:
    st.success(f"{len(resultados)} artículos únicos encontrados — Tema: *{st.session_state.tema}*")

    tabla = [{
        "✓": False,
        "Área": r.get("area", "Otras áreas"),
        "Año": r["year"], "Título": r["title"],
        "Revista": r["journal"], "DOI": r["doi"],
        "Acceso Abierto": r.get("url_oa", "") or "No disponible"
    } for r in resultados]

    tabla_editada = st.data_editor(
        tabla,
        column_config={
            "✓": st.column_config.CheckboxColumn("Incluir", default=True),
            "Acceso Abierto": st.column_config.LinkColumn("Acceso Abierto"),
        },
        use_container_width=True,
        height=400,
        hide_index=True
    )
    resultados_seleccionados = [
        r for r, fila in zip(resultados, tabla_editada) if fila.get("✓", True)
    ]
    st.caption(f"{len(resultados_seleccionados)} de {len(resultados)} artículos seleccionados para el análisis.")

    exportar_csv(resultados)
    exportar_ris(resultados)
    exportar_bib(resultados)
    exportar_markdown(resultados, query=st.session_state.tema)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        with open("literatura.csv", "rb") as f:
            st.download_button("⬇️ CSV", f, "literatura.csv", width="stretch", disabled=INTERFAZ_BLOQUEADA)
    with c2:
        with open("literatura.ris", "rb") as f:
            st.download_button("⬇️ RIS (Zotero)", f, "literatura.ris", width="stretch", disabled=INTERFAZ_BLOQUEADA)
    with c3:
        with open("literatura.bib", "rb") as f:
            st.download_button("⬇️ BibTeX", f, "literatura.bib", width="stretch", disabled=INTERFAZ_BLOQUEADA)
    with c4:
        with open("resumenes.md", "rb") as f:
            st.download_button("⬇️ Markdown", f, "resumenes.md", width="stretch", disabled=INTERFAZ_BLOQUEADA)

    # -------------------------------------------------------------
    # ANÁLISIS IMRAD
    # -------------------------------------------------------------
    st.divider()
    st.subheader("🧠 Síntesis de la literatura (formato IMRAD)")
    st.caption("Analiza TODOS los artículos encontrados y genera un resumen narrativo estructurado.")

    tamano_lote = st.slider(
        "Artículos por lote de análisis", min_value=3, max_value=15, value=6,
        disabled=INTERFAZ_BLOQUEADA
    )
    n_lotes_estimado = -(-len(resultados) // tamano_lote)
    st.caption(f"Se procesarán aproximadamente {n_lotes_estimado} bloques + 1 paso final de síntesis.")

    with st.expander("⚙️ Opciones avanzadas de redacción"):
        st.caption("Puedes usar un modelo rápido para el análisis por lotes, y uno de mejor "
                   "calidad solo para la redacción final.")
        st.info("ℹ️ **Nota:** el formato de salida (párrafos vs. viñetas) depende en gran medida "
                "del modelo elegido. Modelos más grandes (ej. llama3.2:3b o superiores) siguen "
                "mejor las instrucciones de redacción narrativa. Modelos pequeños (ej. phi3:mini) "
                "tienden a producir listas incluso cuando se les pide prosa. Si necesitas texto "
                "en párrafos, prueba con un modelo más grande en 'Modelo para redacción final', "
                "o usa el estilo 'Estructurado' para aprovechar las viñetas de forma ordenada.")
        colm1, colm2 = st.columns(2)
        with colm1:
            modelo_lotes = st.selectbox("Modelo para análisis por lotes (rápido)",
                                          options=modelos_disponibles,
                                          index=modelos_disponibles.index("llama3.2:3b") if "llama3.2:3b" in modelos_disponibles else 0,
                                          disabled=INTERFAZ_BLOQUEADA)
        with colm2:
            modelo_final = st.selectbox("Modelo para redacción final (recomendado: uno más grande)",
                                          options=modelos_disponibles,
                                          index=modelos_disponibles.index("citalocal-quality:latest") if "citalocal-quality:latest" in modelos_disponibles else min(1, len(modelos_disponibles)-1),
                                          disabled=INTERFAZ_BLOQUEADA)

        estilo = st.radio("Estilo de redacción final",
                           options=["narrativo", "estructurado"],
                           format_func=lambda x: "Narrativo (párrafos)" if x == "narrativo" else "Estructurado (viñetas por sección)",
                           disabled=INTERFAZ_BLOQUEADA)

        usar_personalizado = st.checkbox("Escribir mis propias instrucciones (prompt)",
                                          disabled=INTERFAZ_BLOQUEADA)
        prompt_personalizado = None
        if usar_personalizado:
            st.caption("Debes incluir los marcadores `{tema}` y `{combinado}` en tu texto; "
                       "serán reemplazados automáticamente.")
            prompt_personalizado = st.text_area("Prompt personalizado",
                                                 value=PLANTILLA_NARRATIVA,
                                                 height=250, disabled=INTERFAZ_BLOQUEADA)

    generar_btn = st.button("🧠 Generar análisis IMRAD", width="stretch", disabled=INTERFAZ_BLOQUEADA)

    if generar_btn and not INTERFAZ_BLOQUEADA:
        st.session_state.busy = True
        estado2 = st.empty()
        barra = st.progress(0.0)
        info_tiempo = st.empty()
        inicio = time.time()

        def formatear(segundos):
            segundos = max(int(segundos), 0)
            m, s = divmod(segundos, 60)
            return f"{m:02d}:{s:02d}"

        def callback_progreso(msg, frac=None):
            estado2.text(msg)
            if frac is not None:
                barra.progress(min(max(frac, 0.0), 1.0))
                transcurrido = time.time() - inicio
                if frac > 0.02:
                    total_estimado = transcurrido / frac
                    restante = total_estimado - transcurrido
                    info_tiempo.text(f"⏱ Transcurrido: {formatear(transcurrido)}  |  "
                                     f"Restante estimado: {formatear(restante)}")
                else:
                    info_tiempo.text(f"⏱ Transcurrido: {formatear(transcurrido)}  |  Calculando...")

        analisis = generar_analisis_imrad(
            resultados_seleccionados, st.session_state.tema,
            modelo_lotes=modelo_lotes, modelo_final=modelo_final,
            progreso_callback=callback_progreso, tamano_lote=tamano_lote,
            estilo=estilo, prompt_personalizado=prompt_personalizado
        )
        total = time.time() - inicio
        st.session_state.analisis_imrad = analisis
        st.session_state.busy = False
        st.session_state.done_locked = True
        estado2.text(f"✅ Análisis completado en {formatear(total)} (mm:ss).")
        st.rerun()

    if st.session_state.analisis_imrad:
        st.markdown(st.session_state.analisis_imrad)

        tema_actual = st.session_state.tema
        exportar_analisis_md(st.session_state.analisis_imrad, tema=tema_actual)
        exportar_analisis_txt(st.session_state.analisis_imrad, tema=tema_actual)
        exportar_analisis_docx(st.session_state.analisis_imrad, tema=tema_actual)

        d1, d2, d3 = st.columns(3)
        with d1:
            with open("analisis_imrad.md", "rb") as f:
                st.download_button("⬇️ Markdown (.md)", f, "analisis_imrad.md", width="stretch")
        with d2:
            with open("analisis_imrad.txt", "rb") as f:
                st.download_button("⬇️ Texto (.txt)", f, "analisis_imrad.txt", width="stretch")
        with d3:
            with open("analisis_imrad.docx", "rb") as f:
                st.download_button("⬇️ Word (.docx)", f, "analisis_imrad.docx", width="stretch")

        st.divider()
        if st.button("🔄 Nueva búsqueda", type="primary", width="stretch"):
            st.session_state.resultados = []
            st.session_state.analisis_imrad = None
            st.session_state.busy = False
            st.session_state.done_locked = False
            st.session_state.tema = ""
            st.rerun()
else:
    st.info("Configura los parámetros en el panel izquierdo y presiona Buscar.")