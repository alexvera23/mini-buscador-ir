# Sistema de Metadata y Validación

Los archivos de metadata residen en `data/metadata/` y están regidos por `data/metadata/metadata_schema.json`.

## Archivos principales

- `categories.json`: Define las 10 categorías principales (`C01`–`C10`), sus directorios, tags, categorías relacionadas y `category_hub_ids`.
- `documents.json`: Catálogo oficial de documentos sin campos de subcategoría.
- `links.json`: Aristas dirigidas entre documentos con `source_id`, `target_id`, `relation_type` y `justification`.
- `metadata_schema.json`: Esquema JSON Schema (draft 2020-12) que valida tipos, patrones de IDs, rutas planas (`data/corpus/<dir_name>/<filename>`) y ausencia de campos obsoletos.

## Scripts de validación

- `scripts/validate_catalog.py`: Valida unicidad de IDs/slugs, rutas, campos obligatorios, ausencia de campos de subcategoría, conteo por categoría (5–10 recomendado) e integración entre los JSON.
- `scripts/validate_directories.py`: Verifica los 10 directorios de categorías, ausencia de subdirectorios y que los HTML físicos estén catalogados.
- `scripts/validate_links.py`: Verifica integridad referencial, ausencia de duplicados/autorreferencias y nodos aislados.
- `scripts/analyze_graph.py`: Calcula métricas del grafo (nodos, aristas, densidad, grados, componentes conexos, alcanzabilidad y matriz inter-categoría).
