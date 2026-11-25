# Mini Buscador RI

Mini buscador web desarrollado como proyecto académico de Recuperación de Información.

## Stack

- Python 3.11
- FastAPI
- React
- Vite
- Tailwind CSS
- Docker
- Docker Compose

## Arquitectura

- Backend: FastAPI
- Frontend: React + Vite + Tailwind
- Corpus: documentos HTML locales
- Ranking textual: Índice Invertido + TF-IDF
- Ranking estructural: PageRank
- Evaluación: Precision, Recall, F1 y Precision@K

## Ejecución

```bash
docker compose up --build