# Catálogo de Documentos (`documents.json`)

`data/metadata/documents.json` es la **fuente oficial** de información sobre todos los documentos planificados y existentes del corpus.

## Esquema de cada documento

- `id`: Identificador único global y consecutivo (`D001`, `D002`, ..., `D074`). No depende de bloques fijos por subcategoría.
- `title`: Título descriptivo del documento.
- `filename`: Nombre del archivo HTML (`<id>_<slug>.html`).
- `category_id`, `category_code`, `category`: Referencia a la categoría en `categories.json`.
- `slug`: Identificador textual único en `snake_case`.
- `path`: Ruta relativa (`data/corpus/<dir_name>/<filename>`).
- `description`: Resumen del alcance y contenido del documento.
- `tags`: Lista de palabras clave relevantes (3 a 8).
- `document_type`: `category_hub` o `specialized`.
- `hub_ids`: Lista con el ID del hub de la categoría.
- `planned_links`: Lista de IDs de documentos relacionados (coherente con `links.json`).
- `status`: `created` (archivo HTML presente) o `planned` (pendiente de generación).

## Asignación de IDs

Los IDs `D001`–`D010` se conservan para los 10 documentos HTML ya creados en `data/corpus/01_fundamentos/`. Los documentos restantes (`D011`–`D074`) se asignan de forma consecutiva y estable.
