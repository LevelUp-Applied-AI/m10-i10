"""RAG composer — retrieve -> assemble -> generate -> cite -> grounding check.

Grounding contract: when `answer` is not the empty-retrieval sentinel,
`len(citations) > 0` is required. Every cited `chunk_id` corresponds to
a chunk in the top-`k` retrieved from Weaviate.

The Chunk class in Weaviate uses `vectorizer: none` and is seeded with
pre-computed sentence-transformers embeddings (`all-MiniLM-L6-v2`).
Queries therefore encode the question on the server side and use
`with_near_vector`, not `with_near_text` (which requires a configured
vectorizer module).

Generator called with `do_sample=False` for reproducibility.
"""
import re
from typing import Tuple

PROMPT_TEMPLATE = """\
You are answering a recipe question. Use ONLY the numbered sources below.
Cite each claim with the source number in square brackets, e.g. [1].
If the sources do not contain the answer, say: I cannot answer this from the available sources.

Sources:
{sources}

Question: {question}
Answer:"""

SENTINEL = "I cannot answer this from the available sources"
CITATION_PATTERN = re.compile(r"\[(\d+)\]")
EMBEDDER_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# Lazy-loaded module-level embedder. Loaded on first call; cached after.
# This matches the seeder's model (see api/seed_weaviate.py). Kept at
# module scope rather than lifespan because the embedder is internal to
# the RAG composer; the lifespan-managed resources (Neo4j driver,
# Weaviate client, spaCy pipeline, flan-t5 generator) are the ones
# requiring per-request `Depends()` injection.
_embedder = None


def _get_embedder():
    global _embedder
    if _embedder is None:
        from sentence_transformers import SentenceTransformer
        _embedder = SentenceTransformer(EMBEDDER_MODEL)
    return _embedder


def assemble_prompt(question: str, chunks: list[dict]) -> Tuple[str, dict[int, dict]]:
    """Number the retrieved chunks 1..k and substitute into the prompt template.

    Returns (prompt_str, {citation_index: chunk_dict}). Index starts at 1.
    """
    numbered: dict[int, dict] = {}
    lines = []
    for i, chunk in enumerate(chunks, start=1):
        numbered[i] = chunk
        lines.append(f"[{i}] {chunk['text']}")
    sources = "\n".join(lines)
    return PROMPT_TEMPLATE.format(sources=sources, question=question), numbered


def extract_citations(answer: str, numbered: dict[int, dict]) -> list[dict]:
    """Pull [N]-style markers from `answer` and resolve to retrieved chunks.

    Returns one {"chunk_id", "score"} dict per unique resolvable index.
    """
    cited: list[dict] = []
    seen: set[int] = set()
    for match in CITATION_PATTERN.finditer(answer):
        idx = int(match.group(1))
        if idx in numbered and idx not in seen:
            seen.add(idx)
            chunk = numbered[idx]
            cited.append({"chunk_id": chunk["chunk_id"], "score": chunk["score"]})
    return cited


def compose_rag(question: str, weaviate_client, generator, k: int = 4) -> dict:
    """Run the four-stage RAG pipeline.

    Returns {"answer": str, "citations": list[dict], "confidence": float}.
    """
    embedder = _get_embedder()
    vec = embedder.encode(question).tolist()
    raw_query = (
        weaviate_client.query.get("Chunk", ["chunk_id", "text"])
        .with_near_vector({"vector": vec})
        .with_limit(k)
        .with_additional(["distance"])
        .do()
    )
    retrieved = [
        {
            "chunk_id": c["chunk_id"],
            "text": c["text"],
            "score": 1.0 - c["_additional"]["distance"],
        }
        for c in raw_query["data"]["Get"]["Chunk"]
    ]
    if not retrieved:
        return {"answer": SENTINEL, "citations": [], "confidence": 0.0}

    prompt, numbered = assemble_prompt(question, retrieved)
    raw = generator(prompt, max_new_tokens=256, do_sample=False)[0]["generated_text"]
    citations = extract_citations(raw, numbered)
    if not citations:
        return {"answer": SENTINEL, "citations": [], "confidence": 0.0}

    confidence = sum(c["score"] for c in citations) / len(citations)
    confidence = max(0.0, min(1.0, confidence))
    return {"answer": raw, "citations": citations, "confidence": confidence}
