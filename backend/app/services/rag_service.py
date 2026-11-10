
import json
import logging
import random
import re
import time

from difflib import SequenceMatcher

from google import genai
from google.genai import errors

from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.core.config import GEMINI_API_KEY, GEMINI_MODEL
from app.models.item import Item
from app.services.embedding_service import generate_embedding

from app.services.matching_service import (
    normalize_text,
    get_item_identity,
    extract_attributes,
    COLORS,
    MATERIALS,
)


logger = logging.getLogger(__name__)

TOP_K = 20
MAX_RESULTS = 5
MIN_HYBRID_SCORE = 35.0

FALLBACK_MODELS = ["gemini-3.5-flash-lite"]
MAX_RETRIES = 3

STOP_WORDS = {
    "has", "have", "had", "anyone", "someone", "somebody",
    "the", "a", "an", "is", "are", "was", "were",
    "my", "me", "i", "we", "our", "you", "your",
    "any", "been", "being", "near", "at", "in", "on",
    "where", "what", "when", "who", "did", "does",
    "do", "can", "could", "please", "show", "find",
    "search", "for", "report", "reports", "item", "items",
    "lost", "found", "missing", "reported"
}


def detect_report_intent(question: str) -> str:
    """
    Determine which report type the user wants to find.

    A lost item search should look for found reports.
    A found item search should look for lost reports.
    """

    text = normalize_text(question)

    found_patterns = [
        r"\bhas anyone found\b",
        r"\banyone found\b",
        r"\bsomeone found\b",
        r"\bitems found\b",
        r"\breports found\b",
        r"\breported found\b",
        r"\bwhere is my missing\b",
        r"\bi lost\b",
        r"\bmy lost\b",
        r"\bmy missing\b",
        r"\blooking for my\b",
    ]

    lost_patterns = [
        r"\bhas anyone lost\b",
        r"\banyone lost\b",
        r"\bsomeone lost\b",
        r"\bitems lost\b",
        r"\breports lost\b",
        r"\breported losing\b",
        r"\breported lost\b",
        r"\bwho lost\b",
    ]

    wants_found = any(
        re.search(pattern, text)
        for pattern in found_patterns
    )

    wants_lost = any(
        re.search(pattern, text)
        for pattern in lost_patterns
    )

    if wants_found and not wants_lost:
        return "found"

    if wants_lost and not wants_found:
        return "lost"

    return "both"


def extract_query_terms(question: str) -> list[str]:
    """Extract useful words for keyword retrieval."""

    words = re.findall(
        r"[a-z0-9]+",
        normalize_text(question)
    )

    return list(dict.fromkeys(
        word for word in words
        if word not in STOP_WORDS and len(word) > 1
    ))


def calculate_question_item_score(
    question: str,
    item: Item,
    semantic_similarity: float
) -> float:
    """
    Score a free-text question against an item report.

    Components:
    - Semantic similarity: 30%
    - Item identity: 35%
    - Physical attributes: 15%
    - Location matching: 15%
    - Text matching: 5%
    """

    question_text = normalize_text(question)

    item_text = normalize_text(
        f"{item.title or ''} {item.description or ''}"
    )

    # Identify physical item types.
    question_identity = get_item_identity(question_text)
    item_identity = get_item_identity(item_text)

    if (
        question_identity
        and item_identity
        and question_identity != item_identity
    ):
        return 0.0

    if question_identity and question_identity == item_identity:
        identity_score = 100.0
    elif question_identity and not item_identity:
        identity_score = 25.0
    else:
        identity_score = 0.0

    # Compare physical attributes.
    question_attributes = (
        extract_attributes(question_text, COLORS)
        | extract_attributes(question_text, MATERIALS)
    )

    item_attributes = (
        extract_attributes(item_text, COLORS)
        | extract_attributes(item_text, MATERIALS)
    )

    if question_attributes and item_attributes:
        intersection = question_attributes & item_attributes
        union = question_attributes | item_attributes

        attribute_score = (
            len(intersection) / len(union)
        ) * 100.0

    elif question_attributes:
        attribute_score = 0.0
    else:
        attribute_score = 50.0

    # Compare location words.
    question_words = set(extract_query_terms(question))

    location_words = set(
        extract_query_terms(item.location or "")
    )

    location_matches = question_words & location_words

    if location_words and question_words:
        location_score = min(
            100.0,
            (len(location_matches) / len(location_words)) * 100
        )
    else:
        location_score = 50.0

    # Compare question and report text.
    text_score = (
        SequenceMatcher(
            None,
            question_text,
            item_text
        ).ratio() * 100.0
    )

    semantic_score = max(
        0.0,
        min(100.0, semantic_similarity * 100.0)
    )

    final_score = (
        semantic_score * 0.30
        + identity_score * 0.35
        + attribute_score * 0.15
        + location_score * 0.15
        + text_score * 0.05
    )

    return round(final_score, 2)


def group_duplicate_reports(reports: list) -> list:
    """
    Group exact duplicate reports without modifying database records.

    Reports are grouped only when their normalized title,
    description, item type, location and event date match.
    """

    grouped = {}

    for report in reports:

        key = (
            normalize_text(report.get("title")),
            normalize_text(report.get("description")),
            normalize_text(report.get("item_type")),
            normalize_text(report.get("location")),
            report.get("event_date")
        )

        if key not in grouped:

            grouped[key] = {
                **report,
                "report_ids": [report["id"]],
                "duplicate_count": 1
            }

        else:

            existing = grouped[key]

            existing["report_ids"].append(
                report["id"]
            )

            existing["duplicate_count"] += 1

            # Keep the highest ranking score.
            existing["hybrid_score"] = max(
                existing["hybrid_score"],
                report["hybrid_score"]
            )

            existing["similarity"] = max(
                existing["similarity"],
                report["similarity"]
            )

    return list(grouped.values())


def retrieve_relevant_items(
    db: Session,
    question: str
):
    """Retrieve reports using vector and keyword-based hybrid search."""

    print("\n========== RAG RETRIEVAL STARTED ==========")
    print("User question:", question)

    try:
        report_intent = detect_report_intent(question)

        print("Detected report intent:", report_intent)

        # Generate the query embedding.
        query_embedding = generate_embedding(
            title=question,
            description="",
            category="",
            location="",
            item_type=""
        )

        if len(query_embedding) != 384:
            raise ValueError(
                f"Expected 384-dimensional embedding, "
                f"received {len(query_embedding)}."
            )

        distance = Item.embedding.cosine_distance(
            query_embedding
        )

        # --------------------------------------
        # VECTOR SEARCH
        # --------------------------------------

        vector_query = (
            db.query(Item, distance.label("distance"))
            .filter(Item.embedding.isnot(None))
        )

        if report_intent != "both":
            vector_query = vector_query.filter(
                Item.item_type == report_intent
            )

        vector_results = (
            vector_query
            .order_by(distance.asc())
            .limit(TOP_K)
            .all()
        )

        # --------------------------------------
        # KEYWORD SEARCH
        # --------------------------------------

        terms = extract_query_terms(question)

        keyword_query = db.query(Item)

        if report_intent != "both":
            keyword_query = keyword_query.filter(
                Item.item_type == report_intent
            )

        if terms:

            keyword_conditions = []

            for term in terms:

                pattern = f"%{term}%"

                keyword_conditions.extend([
                    Item.title.ilike(pattern),
                    Item.description.ilike(pattern),
                    Item.location.ilike(pattern),
                    Item.category.ilike(pattern),
                ])

            keyword_query = keyword_query.filter(
                or_(*keyword_conditions)
            )

        keyword_results = (
            keyword_query
            .order_by(Item.id.desc())
            .limit(TOP_K)
            .all()
        )

        # --------------------------------------
        # MERGE CANDIDATES
        # --------------------------------------

        candidates = {}

        for item, cosine_distance in vector_results:

            candidates[item.id] = {
                "item": item,
                "similarity": max(
                    0.0,
                    1.0 - float(cosine_distance)
                )
            }

        for item in keyword_results:

            if item.id not in candidates:

                candidates[item.id] = {
                    "item": item,
                    "similarity": 0.0
                }

        print("Vector candidates:", len(vector_results))
        print("Keyword candidates:", len(keyword_results))
        print("Unique candidates:", len(candidates))

        # --------------------------------------
        # HYBRID SCORING
        # --------------------------------------

        ranked_items = []

        for candidate in candidates.values():

            item = candidate["item"]
            similarity = candidate["similarity"]

            hybrid_score = calculate_question_item_score(
                question=question,
                item=item,
                semantic_similarity=similarity
            )

            print(
                f"Candidate ID={item.id}, "
                f"Title={item.title}, "
                f"Type={item.item_type}, "
                f"Similarity={similarity:.4f}, "
                f"Hybrid score={hybrid_score}"
            )

            if hybrid_score < MIN_HYBRID_SCORE:
                continue

            ranked_items.append({
                "id": item.id,
                "title": item.title,
                "description": item.description,
                "item_type": item.item_type,
                "category": item.category,
                "location": item.location,
                "event_date": (
                    item.event_date.isoformat()
                    if item.event_date else None
                ),
                "similarity": round(similarity, 4),
                "hybrid_score": hybrid_score
            })

        # --------------------------------------
        # SORT RESULTS
        # --------------------------------------

        ranked_items.sort(
            key=lambda result: result["hybrid_score"],
            reverse=True
        )

        # --------------------------------------
        # GROUP EXACT DUPLICATES
        # --------------------------------------

        grouped_items = group_duplicate_reports(
            ranked_items
        )

        grouped_items.sort(
            key=lambda result: result["hybrid_score"],
            reverse=True
        )

        # Apply result limit after grouping.
        relevant_items = grouped_items[:MAX_RESULTS]

        print("\n========== RAG RETRIEVAL COMPLETED ==========")
        print("Total unique candidates:", len(candidates))
        print("Reports before grouping:", len(ranked_items))
        print("Reports after grouping:", len(grouped_items))
        print("Final reports returned:", len(relevant_items))
        print("=============================================\n")

        return relevant_items

    except Exception:
        logger.exception("RAG retrieval failed.")
        raise


def generate_rag_answer(
    question: str,
    retrieved_items: list
):
    """Generate a grounded answer using Gemini with retries and fallback."""

    if not GEMINI_API_KEY:
        raise RuntimeError(
            "GEMINI_API_KEY is not configured."
        )

    client = genai.Client(
        api_key=GEMINI_API_KEY
    )

    context = json.dumps(
        retrieved_items,
        ensure_ascii=False,
        indent=2
    )

    prompt = f"""
You are the CampusFind AI assistant for a campus lost and found platform.

Answer the user's question using ONLY the campus reports provided below.

RULES:
1. Never invent reports, items, locations, dates, or people.
2. If no relevant reports are available, clearly say so.
3. Distinguish between lost and found reports.
4. Do not claim that two reports refer to the same physical item.
5. Never reveal owner IDs or private user information.
6. Mention report IDs when referring to specific reports.
7. Be concise, clear, and helpful.
8. Treat hybrid scores as internal ranking information, not proof of a match.
9. Some results may contain report_ids and duplicate_count.
10. When report_ids contains multiple IDs, explain that the reports have identical recorded details.
11. Preserve all report IDs when mentioning a grouped result.
12. Do not claim that identical reports belong to the same person or physical item.

USER QUESTION:
{question}

RETRIEVED CAMPUS REPORTS:
{context}

Provide a natural-language answer grounded in these reports.
"""

    models_to_try = list(dict.fromkeys(
        [GEMINI_MODEL] + FALLBACK_MODELS
    ))

    last_error = None

    for model in models_to_try:

        logger.info(
            "Trying Gemini model: %s",
            model
        )

        for attempt in range(MAX_RETRIES):

            try:

                logger.info(
                    "Generating RAG answer: model=%s attempt=%s/%s",
                    model,
                    attempt + 1,
                    MAX_RETRIES
                )

                response = client.models.generate_content(
                    model=model,
                    contents=prompt
                )

                if response.text and response.text.strip():

                    logger.info(
                        "Gemini generation successful using model=%s",
                        model
                    )

                    return response.text.strip()

                raise RuntimeError(
                    "Gemini returned an empty response."
                )

            except errors.APIError as exc:

                last_error = exc

                if exc.code not in (
                    429, 500, 502, 503, 504
                ):

                    logger.exception(
                        "Non-retryable Gemini API error: model=%s",
                        model
                    )

                    raise

                logger.warning(
                    "Gemini temporary error: "
                    "model=%s status=%s attempt=%s",
                    model,
                    exc.code,
                    attempt + 1
                )

                if attempt < MAX_RETRIES - 1:

                    delay = (
                        min(2 ** attempt, 8)
                        + random.uniform(0, 0.5)
                    )

                    logger.info(
                        "Retrying Gemini request after %.2f seconds",
                        delay
                    )

                    time.sleep(delay)

            except RuntimeError:
                raise

            except Exception as exc:

                logger.exception(
                    "Unexpected Gemini error using model=%s",
                    model
                )

                last_error = exc
                break

    logger.error(
        "All configured Gemini models failed."
    )

    raise RuntimeError(
        "All configured Gemini models failed."
    ) from last_error


def ask_campus_assistant(
    db: Session,
    question: str
):
    """Complete RAG workflow: retrieval followed by generation."""

    logger.info(
        "CampusFind AI question received."
    )

    retrieved_items = retrieve_relevant_items(
        db=db,
        question=question
    )

    answer = generate_rag_answer(
        question=question,
        retrieved_items=retrieved_items
    )

    return {
        "question": question,
        "answer": answer,
        "retrieved_reports": retrieved_items,
        "total_retrieved": len(retrieved_items)
    }
