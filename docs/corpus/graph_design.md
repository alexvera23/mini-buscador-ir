# Diseño del Grafo de Relaciones (`links.json`)

El grafo dirigido de documentos (`data/metadata/links.json`) modela enlaces semánticos y de navegación entre los documentos del corpus para permitir la evaluación de algoritmos de Recuperación de Información, incluyendo **PageRank**.

## Tipos de relación permitidos

- `category_navigation`: Navegación bidireccional entre el `category_hub` y los documentos de su categoría.
- `related_concept`: Relación conceptual o temática directa entre documentos.
- `prerequisite`: Dependencia conceptual previa.
- `implementation`: Relación entre un concepto/arquitectura y su implementación práctica.
- `architecture_relation`: Conexión entre categorías o decisiones arquitectónicas.
- `security_relation`: Vínculo relacionado con seguridad web.
- `comparison`: Comparación entre tecnologías o enfoques.

## Propiedades estructurales actuales

- **Nodos**: 74 (variable según el catálogo).
- **Aristas**: 236.
- **Componentes conexos**: 1 (débil y fuertemente conexo).
- **Nodos aislados / dangling nodes**: 0.
- **Autorreferencias y duplicados**: 0.
