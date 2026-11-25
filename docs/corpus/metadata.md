# Sistema de Metadatos del Corpus

Los metadatos centrales residen en `data/metadata/` y constituyen la fuente única de verdad para la planificación del corpus antes de redactar los archivos HTML.

## Archivos de metadatos

### 1. `data/metadata/categories.json`
Registra las 10 categorías (`C01`–`C10`) y sus 50 subcategorías (`C01.1`–`C10.5`), incluyendo:
- `category_id`, `code`, `name`, `dir_name`, `id_range`, `description`, `tags`.
- `related_categories`: categorías relacionadas según la matriz conceptual.
- `category_hub_ids`: hubs principales de la categoría.
- `subcategories`: lista de 5 subcategorías con `subcategory_id`, `code`, `name`, `dir_name`, `id_range` y `hub_id`.

### 2. `data/metadata/documents.json`
Catálogo maestro con exactamente 500 registros documentales. Campos por documento:
- `id`: identificador global permanente (`D001`–`D500`).
- `title`: título específico y único.
- `category_id`, `category_code`, `category`: vinculación a la categoría.
- `subcategory_id`, `subcategory_code`, `subcategory`: vinculación a la subcategoría.
- `slug`: identificador legible en minúsculas con guiones bajos.
- `path`: ruta relativa prevista bajo `data/corpus/<cat>/<subcat>/<ID>_<slug>.html`.
- `description`: descripción de alcance (40–80 palabras) que delimita cobertura, exclusiones, requisitos previos y enlaces afines.
- `tags`: lista de palabras clave normalizadas.
- `document_type`: `category_hub`, `subcategory_hub`, `reference` o `specialized`.
- `hub_ids`: IDs de los hubs asociados.
- `planned_links`: lista de IDs destino planificados (sincronizada con `links.json`).
- `status`: estado editorial (`planned` en esta fase).

### 3. `data/metadata/links.json`
Representa las `3,239` aristas dirigidas del grafo planificado. Cada entrada contiene `source_id`, `target_id`, `relation_type` y `justification`. Este archivo permitirá comparar posteriormente el grafo planificado contra el grafo real extraído de los enlaces `<a>` de los HTML redactados.

### 4. `data/metadata/metadata_schema.json`
Esquema JSON Schema (Draft 2020-12) que define la estructura, tipos, patrones regex y restricciones de unicidad para validar `documents.json`, `categories.json` y `links.json`.
