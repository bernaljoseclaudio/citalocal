#!/usr/bin/env python3
"""
literatura.py - Buscador y resumidor de literatura científica
Fuentes: PubMed, Europe PMC, Crossref, Semantic Scholar, DOAJ (MDPI/OA),
         Springer Nature, ScienceDirect (Elsevier), Google Scholar (opcional)
Resúmenes generados con modelo local vía Ollama
Salida: CSV, RIS, BIB, Markdown
"""

import argparse
import os
import re
import csv
import time
import subprocess
from datetime import datetime
import requests
import xml.etree.ElementTree as ET

SPRINGER_API_KEY = os.getenv("SPRINGER_API_KEY", "")
ELSEVIER_API_KEY = os.getenv("ELSEVIER_API_KEY", "")
NCBI_API_KEY = os.getenv("NCBI_API_KEY", "")

OLLAMA_MODEL = "phi3:mini"
MAX_RESULTS = 10
PAUSA = 0.4  # segundos entre requests, para no saturar APIs gratuitas


# ---------- PUBMED ----------
def search_pubmed(query, max_results=MAX_RESULTS):
    base = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    params = {"db": "pubmed", "term": query, "retmax": max_results,
              "retmode": "json", "sort": "relevance"}
    if NCBI_API_KEY:
        params["api_key"] = NCBI_API_KEY
    r = requests.get(f"{base}/esearch.fcgi", params=params)
    ids = r.json()["esearchresult"].get("idlist", [])
    if not ids:
        return []
    fparams = {"db": "pubmed", "id": ",".join(ids), "retmode": "xml"}
    if NCBI_API_KEY:
        fparams["api_key"] = NCBI_API_KEY
    r2 = requests.get(f"{base}/efetch.fcgi", params=fparams)
    return parse_pubmed_xml(r2.text)


def parse_pubmed_xml(xml_text):
    root = ET.fromstring(xml_text)
    results = []
    for art in root.findall(".//PubmedArticle"):
        title = art.findtext(".//ArticleTitle") or ""
        abstract = " ".join(a.text or "" for a in art.findall(".//AbstractText"))
        journal = art.findtext(".//Journal/Title") or ""
        year = art.findtext(".//PubDate/Year") or art.findtext(".//PubDate/MedlineDate") or ""
        authors = []
        for au in art.findall(".//Author"):
            last, fore = au.findtext("LastName"), au.findtext("ForeName")
            if last:
                authors.append(f"{last}, {fore or ''}".strip())
        doi = next((i.text for i in art.findall(".//ArticleId") if i.get("IdType") == "doi"), "")
        results.append({"source": "PubMed", "title": title, "abstract": abstract,
                         "journal": journal, "year": year, "authors": authors, "doi": doi})
    return results


# ---------- EUROPE PMC ----------
def search_europepmc(query, max_results=MAX_RESULTS):
    url = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
    params = {"query": query, "format": "json", "pageSize": max_results}
    data = requests.get(url, params=params).json()
    results = []
    for it in data.get("resultList", {}).get("result", []):
        results.append({
            "source": "EuropePMC", "title": it.get("title", ""),
            "abstract": it.get("abstractText", ""), "journal": it.get("journalTitle", ""),
            "year": it.get("pubYear", ""),
            "authors": it.get("authorString", "").split(", ") if it.get("authorString") else [],
            "doi": it.get("doi", "")
        })
    return results


# ---------- CROSSREF ----------
def search_crossref(query, max_results=MAX_RESULTS):
    url = "https://api.crossref.org/works"
    data = requests.get(url, params={"query": query, "rows": max_results}).json()
    results = []
    for it in data.get("message", {}).get("items", []):
        title = it.get("title", [""])[0] if it.get("title") else ""
        abstract = re.sub("<[^<]+?>", "", it.get("abstract", "")) if it.get("abstract") else ""
        authors = [f"{a.get('family','')}, {a.get('given','')}" for a in it.get("author", [])]
        year = ""
        for k in ("published-print", "published-online"):
            if k in it:
                year = str(it[k]["date-parts"][0][0]); break
        results.append({
            "source": "Crossref", "title": title, "abstract": abstract,
            "journal": (it.get("container-title") or [""])[0], "year": year,
            "authors": authors, "doi": it.get("DOI", "")
        })
    return results


# ---------- SEMANTIC SCHOLAR ----------
def search_semanticscholar(query, max_results=MAX_RESULTS):
    url = "https://api.semanticscholar.org/graph/v1/paper/search"
    params = {"query": query, "limit": max_results,
              "fields": "title,abstract,year,venue,authors,externalIds"}
    data = requests.get(url, params=params).json()
    results = []
    for it in data.get("data", []):
        results.append({
            "source": "SemanticScholar", "title": it.get("title", ""),
            "abstract": it.get("abstract") or "", "journal": it.get("venue", ""),
            "year": str(it.get("year", "")),
            "authors": [a["name"] for a in it.get("authors", [])],
            "doi": it.get("externalIds", {}).get("DOI", "")
        })
    return results


# ---------- DOAJ (cubre MDPI y otras revistas Open Access) ----------
def search_doaj(query, max_results=MAX_RESULTS):
    url = f"https://doaj.org/api/v3/search/articles/{requests.utils.quote(query)}"
    params = {"pageSize": max_results}
    try:
        data = requests.get(url, params=params, timeout=15).json()
    except Exception:
        return []
    results = []
    for it in data.get("results", []):
        bib = it.get("bibjson", {})
        title = bib.get("title", "")
        abstract = bib.get("abstract", "")
        journal = bib.get("journal", {}).get("title", "")
        year = bib.get("year", "")
        authors = [a.get("name", "") for a in bib.get("author", [])]
        doi = next((i.get("id") for i in bib.get("identifier", [])
                    if i.get("type") == "doi"), "")
        results.append({"source": "DOAJ/MDPI", "title": title, "abstract": abstract,
                         "journal": journal, "year": str(year), "authors": authors, "doi": doi})
    return results


# ---------- SPRINGER NATURE ----------
def search_springer(query, max_results=MAX_RESULTS):
    if not SPRINGER_API_KEY:
        print("  [Springer] Sin API key configurada, se omite.")
        return []
    url = "https://api.springernature.com/metadata/json"
    params = {"q": query, "p": max_results, "api_key": SPRINGER_API_KEY}
    try:
        data = requests.get(url, params=params, timeout=15).json()
    except Exception as e:
        print(f"  [Springer] Error: {e}")
        return []
    results = []
    for it in data.get("records", []):
        authors = [c.get("creator", "") for c in it.get("creators", [])]
        results.append({
            "source": "Springer/Nature", "title": it.get("title", ""),
            "abstract": it.get("abstract", ""), "journal": it.get("publicationName", ""),
            "year": it.get("publicationDate", "")[:4] if it.get("publicationDate") else "",
            "authors": authors, "doi": it.get("doi", "")
        })
    return results


# ---------- SCIENCEDIRECT (Elsevier) ----------
def search_sciencedirect(query, max_results=MAX_RESULTS):
    if not ELSEVIER_API_KEY:
        print("  [ScienceDirect] Sin API key configurada, se omite.")
        return []
    url = "https://api.elsevier.com/content/search/sciencedirect"
    headers = {"X-ELS-APIKey": ELSEVIER_API_KEY, "Accept": "application/json"}
    params = {"query": query, "count": max_results}
    try:
        data = requests.get(url, headers=headers, params=params, timeout=15).json()
    except Exception as e:
        print(f"  [ScienceDirect] Error: {e}")
        return []
    results = []
    entries = data.get("search-results", {}).get("entry", [])
    for it in entries:
        title = it.get("dc:title", "")
        abstract = it.get("dc:description", "")  # a menudo vacío sin acceso institucional
        journal = it.get("prism:publicationName", "")
        year = (it.get("prism:coverDate", "") or "")[:4]
        doi = it.get("prism:doi", "")
        authors = []
        creator = it.get("dc:creator", "")
        if creator:
            authors = [creator]
        results.append({"source": "ScienceDirect", "title": title, "abstract": abstract,
                         "journal": journal, "year": year, "authors": authors, "doi": doi})
    return results


# ---------- GOOGLE SCHOLAR (no oficial, usar con moderación) ----------
def search_google_scholar(query, max_results=MAX_RESULTS):
    try:
        from scholarly import scholarly
    except ImportError:
        print("  [Scholar] Falta instalar: pip install scholarly")
        return []
    results = []
    try:
        search_gen = scholarly.search_pubs(query)
        for i, pub in enumerate(search_gen):
            if i >= max_results:
                break
            bib = pub.get("bib", {})
            results.append({
                "source": "GoogleScholar",
                "title": bib.get("title", ""),
                "abstract": bib.get("abstract", ""),
                "journal": bib.get("venue", ""),
                "year": str(bib.get("pub_year", "")),
                "authors": bib.get("author", []) if isinstance(bib.get("author"), list) else [bib.get("author", "")],
                "doi": ""
            })
            time.sleep(1)  # evitar bloqueo
    except Exception as e:
        print(f"  [Scholar] Bloqueado o error: {e}")
    return results


# ---------- DEDUPLICAR ----------
def deduplicar(resultados):
    vistos, unicos = set(), []
    for r in resultados:
        clave = r["doi"].lower() if r["doi"] else r["title"].lower().strip()[:60]
        if clave and clave not in vistos:
            vistos.add(clave)
            unicos.append(r)
    return unicos


# ---------- RESUMEN LOCAL CON OLLAMA ----------
def resumir_con_ollama(texto, modelo=OLLAMA_MODEL):
    if not texto or len(texto.strip()) < 20:
        return "Sin resumen disponible (no hay abstract)."
    prompt = (f"Resume en español, máximo 3 líneas, lenguaje sencillo, "
              f"indicando objetivo, método y hallazgo principal:\n\n{texto}\n\nResumen:")
    try:
        result = subprocess.run(["ollama", "run", modelo], input=prompt,
                                 capture_output=True, text=True, timeout=90)
        return result.stdout.strip()
    except Exception as e:
        return f"Error: {e}"


# ---------- EXPORTAR RIS ----------
def exportar_ris(resultados, filename="literatura.ris"):
    with open(filename, "w", encoding="utf-8") as f:
        for r in resultados:
            f.write("TY  - JOUR\n")
            f.write(f"TI  - {r['title']}\n")
            for a in r["authors"]:
                f.write(f"AU  - {a}\n")
            f.write(f"PY  - {r['year']}\nJO  - {r['journal']}\n")
            if r["doi"]:
                f.write(f"DO  - {r['doi']}\n")
            f.write(f"AB  - {r['abstract']}\nER  - \n\n")
    print(f"RIS generado: {filename}")


# ---------- EXPORTAR BIBTEX ----------
def exportar_bib(resultados, filename="literatura.bib"):
    with open(filename, "w", encoding="utf-8") as f:
        for r in resultados:
            autor = re.sub(r"[^a-zA-Z]", "", r["authors"][0].split(",")[0]) if r["authors"] else "anon"
            key = f"{autor}{r['year']}"
            autores = " and ".join(r["authors"]) if r["authors"] else "Unknown"
            f.write(f"@article{{{key},\n  title = {{{r['title']}}},\n"
                     f"  author = {{{autores}}},\n  year = {{{r['year']}}},\n"
                     f"  journal = {{{r['journal']}}},\n")
            if r["doi"]:
                f.write(f"  doi = {{{r['doi']}}},\n")
            f.write(f"  abstract = {{{r['abstract']}}}\n}}\n\n")
    print(f"BibTeX generado: {filename}")


# ---------- EXPORTAR CSV ----------
def exportar_csv(resultados, filename="literatura.csv"):
    with open(filename, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Fuente", "Autores", "Año", "Título", "Revista", "DOI", "Resumen"])
        for r in resultados:
            w.writerow([r["source"], "; ".join(r["authors"]), r["year"],
                        r["title"], r["journal"], r["doi"], r.get("resumen", "")])
    print(f"CSV generado: {filename}")


# ---------- EXPORTAR MARKDOWN ----------
def exportar_markdown(resultados, filename="resumenes.md", query=""):
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"# Revisión de literatura: {query}\n\n")
        f.write(f"Generado: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
        for r in resultados:
            f.write(f"## {r['title']}\n")
            f.write(f"**Fuente:** {r['source']} | **Autores:** {'; '.join(r['authors'])}\n\n")
            f.write(f"**Año:** {r['year']} | **Revista:** {r['journal']} | **DOI:** {r['doi']}\n\n")
            f.write(f"**Resumen:** {r.get('resumen','N/A')}\n\n---\n\n")
    print(f"Markdown generado: {filename}")


# ---------- MAIN ----------
def main():
    p = argparse.ArgumentParser(description="Buscador local de literatura científica")
    p.add_argument("query", help="Término de búsqueda")
    p.add_argument("--max", type=int, default=MAX_RESULTS)
    p.add_argument("--modelo", default=OLLAMA_MODEL)
    p.add_argument("--sin-resumen", action="store_true")
    p.add_argument("--incluir-scholar", action="store_true",
                   help="Incluye Google Scholar (no oficial, puede bloquearse)")
    args = p.parse_args()

    print(f"Buscando: {args.query}\n")

    fuentes = [search_pubmed, search_europepmc, search_crossref,
               search_semanticscholar, search_doaj, search_springer,
               search_sciencedirect]
    if args.incluir_scholar:
        fuentes.append(search_google_scholar)

    todos_raw = []
    for fn in fuentes:
        try:
            res = fn(args.query, args.max)
            print(f"  {fn.__name__}: {len(res)} resultados")
            todos_raw += res
            time.sleep(PAUSA)
        except Exception as e:
            print(f"  {fn.__name__} falló: {e}")

    todos = deduplicar(todos_raw)
    print(f"\nTotal único: {len(todos)} artículos")

    if not args.sin_resumen:
        print("Generando resúmenes locales...")
        for i, r in enumerate(todos):
            print(f"  [{i+1}/{len(todos)}] {r['title'][:60]}")
            r["resumen"] = resumir_con_ollama(r["abstract"], args.modelo)

    exportar_csv(todos)
    exportar_ris(todos)
    exportar_bib(todos)
    exportar_markdown(todos, query=args.query)
    print("\n✅ Listo: literatura.csv / literatura.ris / literatura.bib / resumenes.md")


if __name__ == "__main__":
    main()