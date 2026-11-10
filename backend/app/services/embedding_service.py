
import math
import httpx

from app.core.config import (
    CLOUDFLARE_ACCOUNT_ID,
    CLOUDFLARE_API_TOKEN
)

EMBEDDING_DIMENSION = 384
MODEL_NAME = "@cf/baai/bge-small-en-v1.5"


def generate_embedding(
    title: str,
    description: str,
    category: str,
    location: str,
    item_type: str
) -> list[float]:
    """
    Generate a normalized 384-dimensional embedding
    using Cloudflare Workers AI.
    """

    account_id = CLOUDFLARE_ACCOUNT_ID
    api_token = CLOUDFLARE_API_TOKEN

    if not account_id or not api_token:
        raise RuntimeError(
            "Cloudflare AI credentials are not configured."
        )

    # Build text using the same format as existing item embeddings.
    text_parts = []

    if title and title.strip():
        text_parts.append(f"Item name: {title.strip()}.")

    if description and description.strip():
        text_parts.append(
            f"Physical description: {description.strip()}."
        )

    if category and category.strip():
        text_parts.append(
            f"Item category: {category.strip()}."
        )

    text = " ".join(text_parts)

    if not text:
        raise ValueError(
            "At least one embedding field must contain text."
        )

    url = (
        f"https://api.cloudflare.com/client/v4/accounts/"
        f"{account_id}/ai/run/{MODEL_NAME}"
    )

    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }

    payload = {
        "text": [text]
    }

    try:
        response = httpx.post(
            url,
            headers=headers,
            json=payload,
            timeout=60.0
        )

        print(
            "Cloudflare embedding HTTP status:",
            response.status_code
        )

        response.raise_for_status()

        result = response.json()

    except httpx.HTTPStatusError as exc:
        print(
            "Cloudflare HTTP Status:",
            exc.response.status_code
        )
        print(
            "Cloudflare Response:",
            exc.response.text
        )

        raise RuntimeError(
            "Cloudflare embedding request failed."
        ) from exc

    except httpx.RequestError as exc:
        print(
            "Cloudflare Connection Error:",
            str(exc)
        )

        raise RuntimeError(
            "Could not connect to Cloudflare."
        ) from exc

    if not result.get("success"):
        print(
            "Cloudflare API Errors:",
            result.get("errors")
        )

        raise RuntimeError(
            "Cloudflare embedding generation failed."
        )

    embedding_data = (
        result.get("result", {}).get("data", [])
    )

    if not embedding_data:
        raise RuntimeError(
            "Cloudflare returned an empty embedding."
        )

    embedding = embedding_data[0]

    print(
        "Cloudflare embedding dimensions:",
        len(embedding)
    )

    if len(embedding) != EMBEDDING_DIMENSION:
        raise ValueError(
            f"Expected {EMBEDDING_DIMENSION} dimensions, "
            f"received {len(embedding)}."
        )

    norm = math.sqrt(
        sum(float(value) ** 2 for value in embedding)
    )

    if norm == 0:
        raise ValueError(
            "Cloudflare returned a zero vector."
        )

    return [
        float(value) / norm
        for value in embedding
    ]
