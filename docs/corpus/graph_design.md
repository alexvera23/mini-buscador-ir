# Diseño del Grafo Documental

## Modelo de grafo

El corpus se modela como un **grafo dirigido** $G = (V, E)$ donde:

- $|V| = 500$ nodos correspondientes a los documentos `D001`–`D500`.
- $|E| = 3{,}239$ aristas dirigidas sin duplicados ni autoenlaces, almacenadas en `data/metadata/links.json`.
- Cada arista incluye `source_id`, `target_id`, `relation_type` y una `justification` semántica explícita.

## Roles de documentos (Niveles de jerarquía)

Todos los hubs forman parte de los 500 documentos reales:

1. **`category_hub` (10 documentos):** Puntos de entrada principales de cada categoría (`D001`, `D081`, `D141`, `D151`, `D201`, `D251`, `D301`, `D351`, `D401`, `D451`). También actúan como hub de su propia subcategoría para evitar crear nodos artificiales.
2. **`subcategory_hub` (40 documentos):** Puntos de entrada de las 40 subcategorías restantes. Conectan bidireccionalmente con su `category_hub` y enlazan a los documentos especializados de su temática.
3. **`reference` (11 documentos):** Documentos de referencia técnica o especificación (e.g., `D009`, `D013`, `D022`, `D032`, `D085`, `D096`, `D132`, `D152`, `D202`, `D222`, `D242`, `D312`, `D352`, `D387`, `D402`, `D452` — 16 documentos en total).
4. **`specialized` (434 documentos):** Documentos temáticos profundos que se enlazan entre sí dentro de la misma subcategoría, entre subcategorías relacionadas y entre categorías afines.

## Tipos de relación (`relation_type`)

| Tipo | Conteo | Significado |
|---|---|---|
| `related_concept` | 964 | Relación conceptual directa entre temas de distintas subcategorías o categorías |
| `category_navigation` | 930 | Enlace estructural entre hubs de categoría/subcategoría y sus documentos |
| `intra_subcategory` | 810 | Continuidad temática dentro de una misma subcategoría |
| `architecture_relation` | 286 | Integración arquitectónica, patrón de diseño o topología de sistema |
| `security_relation` | 189 | Implicación de seguridad, vulnerabilidad o mecanismo de mitigación |
| `implementation` | 38 | Relación entre un concepto general y su implementación o herramienta concreta |
| `comparison` | 11 | Alternativas técnicas o trade-offs comparables |
| `prerequisite` | 11 | Conocimiento previo necesario para comprender el documento origen |

## Reglas de topología y conectividad

- **Grado de salida:** Entre 5 y 12 enlaces por documento (promedio: `6.48`).
- **Grado de entrada:** Entre 2 y 20 enlaces por documento (promedio: `6.48`).
- **Sin nodos aislados ni sumideros (dangling nodes):** 0 nodos con grado de salida 0 y 0 nodos con grado de entrada 0. Esto evita el problema clásico de pérdida de masa de probabilidad en PageRank por nodos sin enlaces salientes.
- **Conectividad global:** 1 única componente débilmente conexa (500 nodos) y 1 única componente fuertemente conexa (500 nodos); todos los 500 documentos son alcanzables desde los 10 hubs de categoría.
- **Densidad:** `0.01298` (grafo disperso realista, adecuado para PageRank).

## Matriz conceptual entre categorías (aristas observadas)

Los enlaces inter-categoría siguen la matriz conceptual definida para el proyecto (`C01→C02/C03`, `C02→C06/C07`, `C03→C04/C08/C06`, `C04→C03`, `C05→C09/C06/C07`, `C06→C02/C03/C07`, `C07→C06/C09/C02`, `C08→C03/C09`, `C09→C03/C08/C05`, `C10→C02/C03/C09`), complementada con puentes semánticos específicos donde existe afinidad técnica real.
