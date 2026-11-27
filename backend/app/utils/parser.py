from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from bs4 import BeautifulSoup

SPANISH_STOPWORDS: frozenset[str] = frozenset({
    "a", "acá", "ahí", "al", "algo", "algún", "alguna", "algunas", "alguno", "algunos",
    "allá", "allí", "ambos", "ante", "antes", "aquel", "aquella", "aquellas", "aquello",
    "aquellos", "aquí", "arriba", "así", "atrás", "aun", "aunque", "bajo", "bastante",
    "bien", "cabe", "cada", "casi", "como", "con", "conmigo", "conseguimos", "conseguir",
    "consigo", "consigue", "consiguen", "consigues", "contigo", "contra", "cual", "cuales",
    "cuando", "cuanta", "cuantas", "cuanto", "cuantos", "de", "dejar", "del", "demás",
    "demasiada", "demasiadas", "demasiado", "demasiados", "dentro", "desde", "donde",
    "dos", "el", "él", "ella", "ellas", "ello", "ellos", "empleáis", "emplean", "emplear",
    "empleas", "empleo", "en", "encima", "entonces", "entre", "era", "eramos", "eran",
    "eras", "eres", "es", "esa", "esas", "ese", "eso", "esos", "esta", "estaba",
    "estabais", "estaban", "estabas", "estad", "estada", "estadas", "estado", "estados",
    "estamos", "están", "estando", "estar", "estará", "estarán", "estarás", "estaré",
    "estaréis", "estaría", "estaríais", "estaríamos", "estarían", "estarías", "estas",
    "este", "esté", "estéis", "estemos", "estén", "estés", "esto", "estos", "estoy",
    "estuve", "estuviera", "estuvierais", "estuvieran", "estuvieras", "estuvieron",
    "estuviese", "estuvieseis", "estuviesen", "estuvieses", "estuvimos", "estuviste",
    "estuvisteis", "estuvo", "etc", "fin", "fue", "fuera", "fuerais", "fueran",
    "fueras", "fueron", "fuese", "fueseis", "fuesen", "fueses", "fui", "fuimos",
    "fuiste", "fuisteis", "gran", "grande", "grandes", "ha", "habéis", "haber",
    "había", "habíais", "habíamos", "habían", "habías", "habida", "habidas", "habido",
    "habidos", "habiendo", "habrá", "habrán", "habrás", "habré", "habréis", "habría",
    "habríais", "habríamos", "habrían", "habrías", "hace", "hacéis", "hacemos",
    "hacen", "hacer", "haces", "hacia", "hago", "hasta", "hay", "haya", "hayamos",
    "hayan", "hayas", "hayáis", "he", "hemos", "hube", "hubiera", "hubierais",
    "hubieran", "hubieras", "hubieron", "hubiese", "hubieseis", "hubiesen", "hubieses",
    "hubimos", "hubiste", "hubisteis", "hubo", "incluso", "intenta", "intentáis",
    "intentamos", "intentan", "intentar", "intentas", "intento", "ir", "jamás", "junto",
    "la", "largo", "las", "le", "les", "lo", "los", "luego", "mas", "más", "me",
    "mediante", "menos", "mi", "mí", "mía", "mías", "mientras", "mío", "míos", "mis",
    "misma", "mismas", "mismo", "mismos", "modo", "mucha", "muchas", "mucho", "muchos",
    "muy", "nada", "ni", "ningún", "ninguna", "ningunas", "ninguno", "ningunos", "no",
    "nos", "nosotras", "nosotros", "nuestra", "nuestras", "nuestro", "nuestros",
    "nunca", "o", "os", "otra", "otras", "otro", "otros", "para", "parece", "parte",
    "pero", "poca", "pocas", "poco", "pocos", "podeis", "podemos", "poder", "podría",
    "podríais", "podríamos", "podrían", "podrías", "por", "porque", "primero", "puede",
    "pueden", "puedo", "pues", "que", "qué", "querer", "quien", "quién", "quienes",
    "quienesquiera", "quienquiera", "quizá", "quizás", "sabe", "sabéis", "sabemos",
    "saben", "saber", "sabes", "se", "sea", "seáis", "seamos", "sean", "seas", "según",
    "ser", "será", "serán", "serás", "seré", "seréis", "sería", "seríais", "seríamos",
    "serían", "serías", "si", "sí", "sido", "siempre", "siendo", "siete", "sigue",
    "siguiente", "sin", "sino", "sobre", "sois", "sola", "solamente", "solas", "solo",
    "sólo", "solos", "somos", "son", "soy", "sr", "sra", "sres", "sta", "su", "sus",
    "suya", "suyas", "suyo", "suyos", "tal", "tales", "también", "tampoco", "tan",
    "tanta", "tantas", "tanto", "tantos", "te", "tenéis", "tenemos", "tener", "tengo",
    "ti", "tiempo", "tiene", "tienen", "tienes", "toda", "todas", "todavía", "todo",
    "todos", "tras", "tu", "tú", "tus", "tuve", "tuviera", "tuvierais", "tuvieran",
    "tuvieras", "tuvieron", "tuviese", "tuvieseis", "tuviesen", "tuvieses", "tuvimos",
    "tuviste", "tuvisteis", "tuvo", "tuya", "tuyas", "tuyo", "tuyos", "último", "un",
    "una", "unas", "uno", "unos", "usa", "usáis", "usamos", "usan", "usar", "usas",
    "uso", "usted", "ustedes", "va", "vais", "valor", "vamos", "van", "varias",
    "varios", "vaya", "verdad", "verdadera", "vosotras", "vosotros", "voy", "vuestra",
    "vuestras", "vuestro", "vuestros", "y", "ya", "yo",
})

_NORMALIZED_STOPWORDS: frozenset[str] = frozenset(
    unicodedata.normalize("NFD", w).encode("ascii", "ignore").decode("ascii")
    for w in SPANISH_STOPWORDS
)

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def normalize_text(text: str) -> str:
    """Convierte a minúsculas y elimina diacríticos/acentos de forma consistente."""
    decomposed = unicodedata.normalize("NFD", text.lower())
    return "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")


def tokenize(text: str) -> list[str]:
    """Tokeniza texto en español: normaliza, elimina puntuación, números aislados y stopwords."""
    normalized = normalize_text(text)
    raw_tokens = _TOKEN_RE.findall(normalized)
    return [
        tok
        for tok in raw_tokens
        if len(tok) >= 2 and not tok.isdigit() and tok not in _NORMALIZED_STOPWORDS
    ]


@dataclass
class ParsedDocument:
    doc_id: str
    title: str
    category: str
    path: str
    text: str
    raw_hrefs: list[str] = field(default_factory=list)
    out_links: list[str] = field(default_factory=list)


def _load_category_map(categories_file: Path | None) -> dict[str, str]:
    if categories_file is None or not categories_file.exists():
        return {}
    data = json.loads(categories_file.read_text(encoding="utf-8"))
    mapping: dict[str, str] = {}
    for cat in data.get("categories", []):
        cid = cat.get("category_id")
        name = cat.get("name")
        dir_name = cat.get("dir_name")
        if cid and name:
            mapping[cid] = name
        if dir_name and name:
            mapping[dir_name] = name
    return mapping


def _extract_meta(soup: BeautifulSoup, names: tuple[str, ...]) -> str | None:
    for name in names:
        tag = soup.find("meta", attrs={"name": name})
        if tag and tag.get("content"):
            return str(tag["content"]).strip()
    return None


def parse_corpus(
    corpus_dir: Path,
    categories_file: Path | None = None,
) -> list[ParsedDocument]:
    """Recorre recursivamente corpus_dir, parsea los HTML y resuelve enlaces salientes."""
    if not corpus_dir.exists():
        return []

    cat_map = _load_category_map(categories_file)
    html_files = sorted(corpus_dir.rglob("*.html"))
    corpus_root = corpus_dir.resolve()

    raw_docs: list[tuple[Path, ParsedDocument]] = []
    resolved_path_to_id: dict[Path, str] = {}

    for html_path in html_files:
        content = html_path.read_text(encoding="utf-8")
        soup = BeautifulSoup(content, "lxml")

        article = soup.find("article")

        # 1. doc_id (priorizar prefijo oficial del archivo Dxxx_ si existe para evitar typos en meta)
        file_match = re.match(r"^(D\d+)_", html_path.name)
        meta_id = (
            _extract_meta(soup, ("doc-id", "document-id"))
            or (str(article.get("data-doc-id")).strip() if article and article.get("data-doc-id") else None)
            or (str(article.get("id")).strip() if article and article.get("id") else None)
        )
        doc_id = file_match.group(1) if file_match else (meta_id or html_path.stem)

        # 2. title
        h1_tag = soup.find("h1")
        title_tag = soup.find("title")
        title = (
            (title_tag.get_text(" ", strip=True) if title_tag else "")
            or (h1_tag.get_text(" ", strip=True) if h1_tag else "")
            or doc_id
        )

        # 3. category
        cat_name = _extract_meta(soup, ("doc-category",))
        if not cat_name:
            cat_id = _extract_meta(soup, ("doc-category-id", "category-id")) or (
                str(article.get("data-category-id")).strip() if article and article.get("data-category-id") else None
            )
            if cat_id and cat_id in cat_map:
                cat_name = cat_map[cat_id]
        if not cat_name:
            dir_name = html_path.parent.name
            cat_name = cat_map.get(dir_name, dir_name)

        # 4. raw_hrefs antes de limpiar etiquetas
        raw_hrefs: list[str] = []
        for a_tag in soup.find_all("a", href=True):
            href = str(a_tag["href"]).strip()
            if href:
                raw_hrefs.append(href)

        # 5. Texto limpio (ignorando scripts y estilos)
        for noisy in soup(["script", "style", "noscript"]):
            noisy.decompose()

        target_root = soup.find("article") or soup.find("body") or soup
        clean_text = " ".join(target_root.get_text(" ", strip=True).split())

        rel_path = html_path.resolve().relative_to(corpus_root).as_posix()
        doc = ParsedDocument(
            doc_id=doc_id,
            title=title,
            category=cat_name,
            path=f"data/corpus/{rel_path}",
            text=clean_text,
            raw_hrefs=raw_hrefs,
        )
        raw_docs.append((html_path.resolve(), doc))
        resolved_path_to_id[html_path.resolve()] = doc_id

    # Resolver out_links contra los documentos reales del corpus
    for abs_path, doc in raw_docs:
        seen_targets: set[str] = set()
        out_links: list[str] = []
        for href in doc.raw_hrefs:
            if href.startswith(("http://", "https://", "mailto:", "tel:", "#", "javascript:")):
                continue
            clean_href = href.split("#", 1)[0].split("?", 1)[0]
            if not clean_href:
                continue
            target_abs = (abs_path.parent / clean_href).resolve()
            target_id = resolved_path_to_id.get(target_abs)
            if target_id and target_id != doc.doc_id and target_id not in seen_targets:
                seen_targets.add(target_id)
                out_links.append(target_id)
        doc.out_links = out_links

    return [doc for _, doc in raw_docs]
