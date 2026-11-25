# Estado de Planificación del Corpus

## Completado en esta fase

- [x] Taxonomía oficial fijada: 10 categorías, 50 subcategorías y distribución de rangos `D001`–`D500`.
- [x] Estructura física de 50 directorios de subcategorías creada en `data/corpus/`.
- [x] Catálogo maestro definido en `data/metadata/documents.json` con 500 títulos únicos, slugs únicos, rutas previstas y descripciones de alcance.
- [x] Registro de categorías y subcategorías en `data/metadata/categories.json`.
- [x] Grafo dirigido planificado en `data/metadata/links.json` (`3,239` aristas justificadas, sin nodos aislados ni sumideros).
- [x] Esquema de validación en `data/metadata/metadata_schema.json`.
- [x] Scripts de validación y análisis ejecutados desde la raíz del proyecto (`scripts/validate_catalog.py`, `scripts/validate_links.py`, `scripts/validate_directories.py`, `scripts/analyze_graph.py`).
- [x] Documentación técnica completa en `docs/corpus/`.
- [x] Preservación intacta de `data/html_docs/D01..D24`, aplicación backend/frontend y configuración Docker.

## Pendiente para fases posteriores

- [ ] Redacción de los 500 documentos HTML (~1,000 palabras por artículo) siguiendo el alcance de `documents.json` y materializando los enlaces de `links.json`.
- [ ] Actualización progresiva del campo `status` (`planned` → `drafted` → `reviewed` → `published`).
- [ ] Implementación del pipeline de extracción HTML, tokenización, índice invertido, TF-IDF y PageRank en el backend.
- [ ] Comparación entre el grafo planificado (`links.json`) y el grafo real extraído de los HTML.
- [ ] Construcción de juicios de relevancia (`data/relevance_judgments.json`) y evaluación experimental (Precision, Recall, F1, Precision@K).
