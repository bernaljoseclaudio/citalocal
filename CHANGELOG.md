# Changelog — CitaLocal

Todos los cambios importantes de cada versión se documentan aquí.

---

## [v1.2.0] - 2026-07-25

### Nuevo
- Clasificación automática de artículos por área temática (Agrícola, Médica, Tecnología, etc.)
- Checkboxes en la tabla de resultados para seleccionar qué artículos incluir en el IMRAD
- Columna "Acceso Abierto" con links directos a versiones gratuitas legales (Unpaywall)
- Nuevas fuentes de búsqueda: AGRIS/FAO, AGRICOLA/USDA, SSRN, ERIC/Educación
- Campo "Términos a excluir" en el sidebar para filtrar resultados irrelevantes
- Modelos correctos seleccionados por defecto (llama3.2:3b + citalocal-quality)

### Mejorado
- instalador automático descarga modelos recomendados y crea citalocal-quality
- instalar.bat actualizado con los mismos pasos para Windows

---

## [v1.1.0] - 2026-07-24

### Nuevo
- Integración con Unpaywall API para detectar acceso abierto por DOI
- Modelo personalizado `citalocal-quality` basado en llama3.1:8b con offloading GPU/CPU
- Campo de términos a excluir en búsquedas
- Filtro nativo NOT en PubMed

### Mejorado
- PLANTILLA_NARRATIVA reescrita con reglas estrictas de prosa académica
- Citas APA en texto: (Autor, año) y agrupadas (Autor1, año; Autor2, año)
- Lista de referencias al final del IMRAD
- Temperature síntesis final: 0.35 → 0.2
- Timeout síntesis final: 240 → 300 segundos
- Columnas "Fuente" y "Resumen" eliminadas de la tabla — tabla más limpia
- Checkbox "Generar resúmenes" eliminado — proceso simplificado

---

## [v1.0.0] - 2026-07-23

### Lanzamiento inicial
- Búsqueda simultánea en 8 bases de datos: PubMed, EuropePMC, Crossref, 
  Semantic Scholar, DOAJ/MDPI, OpenAlex, arXiv, CORE
- Generación de síntesis IMRAD con IA local (Ollama)
- Exportación en CSV, RIS, BibTeX, Markdown, TXT, Word
- Historial local de búsquedas
- Instaladores automáticos para Linux y Windows
- Interfaz visual con Streamlit
- 100% local y privado — sin envío de datos a servidores externos