
import os

# Limit CPU threads to reduce memory overhead.
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

from functools import lru_cache

import torch
from sentence_transformers import SentenceTransformer

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

torch.set_num_threads(1)


@lru_cache(maxsize=1)
def get_embedding_model() -> SentenceTransformer:
    """Load the embedding model once, when first needed."""
    return SentenceTransformer(
        MODEL_NAME,
        device="cpu"
    )


def generate_embedding(
    title: str,
    description: str,
    category: str,
    location: str,
    item_type: str
) -> list[float]:

    model = get_embedding_model()

    text = (
        f"Item name: {title.strip()}. "
        f"Physical description: {description.strip()}. "
        f"Item category: {category.strip()}."
    )

    embedding = model.encode(
        text,
        normalize_embeddings=True,
        convert_to_numpy=True,
        show_progress_bar=False
    )

    return embedding.tolist()
