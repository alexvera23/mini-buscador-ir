# Arquitectura del Corpus de Recuperación de Información (RI)

Este directorio documenta la arquitectura, taxonomía, catálogo, grafo de enlaces y estado de planificación del corpus de documentos HTML5 del proyecto **mini-buscador-ir**.

## Visión general

- **Categorías principales**: 10 (`C01` a `C10`).
- **Subcategorías**: Eliminadas como unidad organizativa del corpus.
- **Distribución de documentos**: Variable por categoría (objetivo recomendado de 5 a 10 documentos por categoría según relevancia y amplitud temática).
- **Total actual planificado**: 74 documentos (`D001`–`D074`).
- **Estructura física**: `data/corpus/<dir_name>/<id>_<slug>.html`, almacenando los documentos directamente dentro de su categoría.

## Documentos de referencia

- [taxonomy.md](taxonomy.md): Definición de las 10 categorías principales y su distribución temática.
- [catalog.md](catalog.md): Estructura del catálogo oficial (`data/metadata/documents.json`) y asignación de IDs.
- [graph_design.md](graph_design.md): Diseño del grafo de relaciones (`data/metadata/links.json`) y métricas para PageRank.
- [metadata.md](metadata.md): Esquema de metadata (`data/metadata/metadata_schema.json`) y validadores.
- [planning_status.md](planning_status.md): Estado actual de la planificación y archivos HTML existentes.

## Validación

```bash
python3 scripts/validate_catalog.py
python3 scripts/validate_directories.py
python3 scripts/validate_links.py
python3 scripts/analyze_graph.py
```
