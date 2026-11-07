
import re
from difflib import SequenceMatcher


# Category aliases help accommodate inconsistent student selections.
CATEGORY_GROUPS = {
    "electronics": {
        "electronics", "electronic", "gadgets", "devices"
    },
    "accessories": {
        "accessories", "personal accessories"
    },
    "personal": {
        "personal items", "personal belongings",
        "personal item", "personal belongings"
    },
    "documents": {
        "documents", "document", "id cards", "cards"
    },
    "clothing": {
        "clothing", "apparel", "wearables"
    },
    "books": {
        "books", "book", "stationery"
    },
}

# Common item identities.
ITEM_IDENTITIES = {
    "laptop": {"laptop", "notebook computer"},
    "phone": {"phone", "smartphone", "mobile", "cellphone"},
    "wallet": {"wallet", "purse"},
    "bottle": {"bottle", "water bottle", "flask"},
    "umbrella": {"umbrella", "parasol"},
    "mouse": {"mouse", "computer mouse"},
    "headphones": {"headphones", "earphones", "headset"},
    "watch": {"watch", "wristwatch"},
    "keys": {"keys", "key", "keychain"},
}

COLORS = {
    "black", "white", "blue", "red", "green",
    "yellow", "brown", "silver", "gold", "grey",
    "gray", "pink", "purple", "orange"
}

MATERIALS = {
    "leather", "plastic", "metal", "stainless steel",
    "wooden", "fabric", "cotton", "nylon", "rubber"
}


def normalize_text(value: str) -> str:
    """Normalize text for consistent comparisons."""
    return re.sub(
        r"[^a-z0-9\s]",
        " ",
        (value or "").lower()
    ).strip()


def get_category_group(category: str) -> str:
    """Map category aliases to a common category group."""
    normalized = normalize_text(category)

    for group, aliases in CATEGORY_GROUPS.items():
        if normalized in aliases:
            return group

    return normalized


def get_item_identity(text: str) -> str | None:
    """Identify the physical item from its title and description."""
    normalized = normalize_text(text)

    for identity, aliases in ITEM_IDENTITIES.items():
        for alias in aliases:
            pattern = rf"\b{re.escape(alias)}\b"

            if re.search(pattern, normalized):
                return identity

    return None


def extract_attributes(text: str, vocabulary: set[str]) -> set[str]:
    """Extract known physical attributes."""
    normalized = normalize_text(text)

    return {
        attribute
        for attribute in vocabulary
        if re.search(
            rf"\b{re.escape(attribute)}\b",
            normalized
        )
    }


def text_similarity(first: str, second: str) -> float:
    """Calculate normalized text similarity."""
    first = normalize_text(first)
    second = normalize_text(second)

    if not first or not second:
        return 0.0

    return SequenceMatcher(None, first, second).ratio()


def calculate_hybrid_score(source, candidate, semantic_score: float):
    """
    Calculate a hybrid relevance score.

    Components:
    - Semantic similarity: 50%
    - Item identity: 25%
    - Physical attributes: 15%
    - Category compatibility: 10%

    Returns a score from 0 to 100.
    """

    source_text = f"{source.title} {source.description}"
    candidate_text = f"{candidate.title} {candidate.description}"

    source_identity = get_item_identity(source_text)
    candidate_identity = get_item_identity(candidate_text)

    # Reject clearly different known physical item identities.
    if (
        source_identity
        and candidate_identity
        and source_identity != candidate_identity
    ):
        return 0.0

    if source_identity and candidate_identity:
        identity_score = 100.0
    elif source_identity or candidate_identity:
        identity_score = 0.0
    else:
        identity_score = text_similarity(
            source.title,
            candidate.title
        ) * 100

    source_attributes = (
        extract_attributes(source_text, COLORS)
        | extract_attributes(source_text, MATERIALS)
    )

    candidate_attributes = (
        extract_attributes(candidate_text, COLORS)
        | extract_attributes(candidate_text, MATERIALS)
    )

    if source_attributes and candidate_attributes:
        intersection = source_attributes & candidate_attributes
        union = source_attributes | candidate_attributes

        attribute_score = (
            len(intersection) / len(union)
        ) * 100
    else:
        attribute_score = 50.0

    source_category = get_category_group(source.category)
    candidate_category = get_category_group(candidate.category)

    category_score = (
        100.0
        if source_category == candidate_category
        else 0.0
    )

    final_score = (
        semantic_score * 0.50
        + identity_score * 0.25
        + attribute_score * 0.15
        + category_score * 0.10
    )

    return round(final_score, 2)
