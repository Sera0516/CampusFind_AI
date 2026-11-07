
from functools import lru_cache

from sentence_transformers import SentenceTransformer


MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


@lru_cache(maxsize=1)
def get_embedding_model() -> SentenceTransformer:
    """
    Load the embedding model once and reuse it.
    """
    return SentenceTransformer(MODEL_NAME)


def generate_embedding(
    title: str,
    description: str,
    category: str,
    location: str,
    item_type: str
) -> list[float]:
    """
    Generate a normalized 384-dimensional embedding
    focused on the physical identity of an item.

    Location and report type are intentionally excluded
    because they are contextual metadata, not item identity.
    """

    model = get_embedding_model()

    title = title.strip()
    description = description.strip()
    category = category.strip()

    text = (
        f"Item name: {title}. "
        f"Physical description: {description}. "
        f"Item category: {category}."
    )

    embedding = model.encode(
        text,
        normalize_embeddings=True,
        convert_to_numpy=True
    )

    return embedding.tolist()
