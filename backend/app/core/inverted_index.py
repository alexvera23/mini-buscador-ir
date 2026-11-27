from __future__ import annotations

import math
from collections import Counter, defaultdict

from app.utils.parser import ParsedDocument, tokenize


class InvertedIndex:
    """Índice invertido y modelo de espacio vectorial TF-IDF con similitud coseno.

    Fórmulas aplicadas:
      - TF(t, d) = f_{t,d} / sum_{t' in d} f_{t',d}  (frecuencia de término normalizada)
      - IDF(t) = ln(N / df_t)  (0.0 si df_t == N o N == 0)
      - TFIDF(t, d) = TF(t, d) * IDF(t)
      - Similitud Coseno: cos(d, q) = (d · q) / (||d||_2 * ||q||_2)
    """

    def __init__(self, documents: list[ParsedDocument]) -> None:
        self.total_documents: int = len(documents)
        self.postings: dict[str, dict[str, float]] = defaultdict(dict)
        self.idf: dict[str, float] = {}
        self.doc_freqs: dict[str, int] = {}
        self.term_total_freqs: Counter[str] = Counter()
        self.doc_norms: dict[str, float] = {}
        self.doc_word_counts: dict[str, int] = {}
        self.doc_term_details: dict[str, list[tuple[str, float, float, float]]] = {}

        self._build(documents)

    def _build(self, documents: list[ParsedDocument]) -> None:
        if self.total_documents == 0:
            return

        doc_tf_maps: dict[str, dict[str, float]] = {}
        df_counter: Counter[str] = Counter()

        # Paso 1: Tokenización y frecuencias de término (TF)
        for doc in documents:
            # Incluir título con peso normal junto al cuerpo para indexación completa
            tokens = tokenize(f"{doc.title} {doc.text}")
            total_terms = len(tokens)
            self.doc_word_counts[doc.doc_id] = total_terms

            if total_terms == 0:
                doc_tf_maps[doc.doc_id] = {}
                continue

            counts = Counter(tokens)
            tf_map: dict[str, float] = {}
            for term, freq in counts.items():
                tf_map[term] = freq / total_terms
                df_counter[term] += 1
                self.term_total_freqs[term] += freq

            doc_tf_maps[doc.doc_id] = tf_map

        # Paso 2: Calcular IDF(t) = ln(N / df_t)
        n = self.total_documents
        for term, df in df_counter.items():
            self.doc_freqs[term] = df
            if df >= n or df <= 0:
                self.idf[term] = 0.0
            else:
                self.idf[term] = math.log(n / df)

        # Paso 3: Calcular pesos TF-IDF, postings y normas L2
        for doc in documents:
            doc_id = doc.doc_id
            tf_map = doc_tf_maps.get(doc_id, {})
            sq_sum = 0.0
            details: list[tuple[str, float, float, float]] = []

            for term, tf_val in tf_map.items():
                idf_val = self.idf[term]
                weight = tf_val * idf_val
                if weight > 0.0:
                    self.postings[term][doc_id] = weight
                    sq_sum += weight * weight
                details.append((term, weight, tf_val, idf_val))

            self.doc_norms[doc_id] = math.sqrt(sq_sum)
            details.sort(key=lambda item: item[1], reverse=True)
            self.doc_term_details[doc_id] = details

    @property
    def vocabulary_size(self) -> int:
        return len(self.doc_freqs)

    def get_top_terms(self, limit: int = 15) -> list[tuple[str, int, int]]:
        """Retorna los términos más frecuentes del corpus: (term, df, total_tf)."""
        most_common = self.term_total_freqs.most_common(limit)
        return [(term, self.doc_freqs.get(term, 0), total) for term, total in most_common]

    def get_document_top_terms(
        self, doc_id: str, limit: int = 15
    ) -> list[tuple[str, float, float, float]]:
        """Retorna [(term, tfidf, tf, idf)] ordenados por peso TF-IDF descendente."""
        return self.doc_term_details.get(doc_id, [])[:limit]

    def search(self, query: str) -> tuple[dict[str, float], dict[str, list[str]], list[str]]:
        """Ejecuta una consulta textual y retorna:
        - scores_norm: dict[doc_id, float] normalizado al rango [0, 1]
        - doc_matched_terms: dict[doc_id, list[str]]
        - query_terms: list[str] únicos en la consulta
        """
        tokens = tokenize(query)
        if not tokens or self.total_documents == 0:
            return {}, {}, []

        q_counts = Counter(tokens)
        q_len = len(tokens)
        query_terms = list(dict.fromkeys(tokens))

        # Vector TF-IDF de la consulta
        q_weights: dict[str, float] = {}
        q_sq_sum = 0.0
        for term, freq in q_counts.items():
            if term not in self.idf:
                continue
            tf_q = freq / q_len
            w_q = tf_q * self.idf[term]
            if w_q > 0.0:
                q_weights[term] = w_q
                q_sq_sum += w_q * w_q

        # Si todos los términos conocidos tenían IDF=0 (presentes en todos los docs),
        # usar pesos uniformes sobre los términos existentes en el vocabulario
        if q_sq_sum == 0.0:
            return {}, {}, query_terms

        q_norm = math.sqrt(q_sq_sum)
        dot_products: dict[str, float] = defaultdict(float)
        matched_terms: dict[str, list[str]] = defaultdict(list)

        for term, w_q in q_weights.items():
            for doc_id, w_d in self.postings.get(term, {}).items():
                dot_products[doc_id] += w_d * w_q
                matched_terms[doc_id].append(term)

        raw_scores: dict[str, float] = {}
        for doc_id, dot in dot_products.items():
            d_norm = self.doc_norms.get(doc_id, 0.0)
            if d_norm > 0.0:
                raw_scores[doc_id] = dot / (d_norm * q_norm)

        if not raw_scores:
            return {}, {}, query_terms

        max_score = max(raw_scores.values())
        if max_score > 0.0:
            norm_scores = {doc_id: score / max_score for doc_id, score in raw_scores.items()}
        else:
            norm_scores = raw_scores

        return norm_scores, dict(matched_terms), query_terms
