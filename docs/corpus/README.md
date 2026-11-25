# Planificación del Corpus de 500 Documentos — Mini Buscador RI

## Objetivo del corpus

Este directorio documenta la planificación formal del corpus controlado de **500 documentos HTML** sobre desarrollo web para el proyecto académico **Mini Buscador RI**. El corpus está diseñado para experimentar, implementar y evaluar técnicas de Recuperación de Información:

- Extracción y limpieza de contenido HTML.
- Tokenización, normalización y construcción de índice invertido.
- Ponderación TF-IDF y ranking textual.
- Análisis estructural mediante grafos dirigidos y PageRank.
- Combinación de señales textuales y estructurales.
- Evaluación con Precision, Recall, F1 y métricas de ranking.

## Alcance de la fase actual

En esta fase se establece la **arquitectura documental completa** sin redactar aún los 500 artículos HTML completos (~1,000 palabras por documento en la fase posterior) ni modificar el código de la aplicación (`backend/`, `frontend/`, `docker-compose.yml`).

## Resumen estructural

- **Categorías:** 10 (`C01`–`C10`), con 50 documentos cada una.
- **Subcategorías:** 50 (`C01.1`–`C10.5`), con 10 documentos cada una.
- **Identificadores globales:** `D001` a `D500`, permanentes e independientes de ruta o título.
- **Convención de nombres:** `DXXX_slug_descriptivo.html` (ejemplo: `data/corpus/01_fundamentos/03_html/D021_html_semantico_estructura_documentos.html`).
- **Directorios físicos:** 10 carpetas de categoría y 50 subcarpetas de subcategoría bajo `data/corpus/`.
- **Metadatos centrales:** `data/metadata/documents.json`, `data/metadata/categories.json`, `data/metadata/links.json` y `data/metadata/metadata_schema.json`.

## Migración documentada de documentos iniciales (`data/html_docs/D01`–`D24`)

El repositorio conserva intactos los 24 documentos HTML iniciales en `data/html_docs/` (`D01_intro_desarrollo_web.html` a `D24_seguridad_web.html`). No han sido eliminados ni sobrescritos. En la nueva taxonomía `D001`–`D500`, su equivalencia temática queda mapeada para futura migración o referencia:

| ID legado (`data/html_docs/`) | Archivo actual | ID equivalente en corpus 500 |
|---|---|---|
| `D01` | `D01_intro_desarrollo_web.html` | `D001` |
| `D02` | `D02_html.html` | `D021` |
| `D03` | `D03_css.html` | `D031` |
| `D04` | `D04_javascript.html` | `D041` |
| `D05` | `D05_dom_eventos.html` | `D042` / `D043` |
| `D06` | `D06_react.html` | `D051` |
| `D07` | `D07_vue.html` | `D061` |
| `D08` | `D08_angular.html` | `D071` |
| `D09` | `D09_arquitectura_frontend.html` | `D081` |
| `D10` | `D10_backend.html` | `D141` |
| `D11` | `D11_apis_rest.html` | `D131` / `D132` |
| `D12` | `D12_bases_datos.html` | `D151` |
| `D13` | `D13_nodejs.html` | `D101` |
| `D14` | `D14_git.html` | `D201` |
| `D15` | `D15_github.html` | `D211` |
| `D16` | `D16_docker.html` | `D401` |
| `D17` | `D17_entornos.html` | `D150` / `D413` |
| `D18` | `D18_clean_code.html` | `D301` |
| `D19` | `D19_testing.html` | `D311` |
| `D20` | `D20_scrum.html` | `D342` |
| `D21` | `D21_arquitectura_software.html` | `D251` |
| `D22` | `D22_cicd.html` | `D421` |
| `D23` | `D23_despliegue.html` | `D431` |
| `D24` | `D24_seguridad_web.html` | `D351` |

## Ejecución de validadores

Todos los scripts se ejecutan desde la raíz del repositorio con Python 3:

```bash
python3 scripts/validate_catalog.py
python3 scripts/validate_links.py
python3 scripts/validate_directories.py
python3 scripts/analyze_graph.py
```

## Documentación relacionada

- [taxonomy.md](taxonomy.md) — Taxonomía completa de 10 categorías y 50 subcategorías.
- [catalog.md](catalog.md) — Catálogo maestro navegable de los 500 documentos.
- [graph_design.md](graph_design.md) — Diseño del grafo dirigido, hubs y métricas estructurales.
- [metadata.md](metadata.md) — Especificación de archivos JSON y JSON Schema.
- [planning_status.md](planning_status.md) — Estado actual de la planificación y siguientes pasos.
