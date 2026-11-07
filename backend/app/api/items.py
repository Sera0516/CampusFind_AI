
from pathlib import Path
from uuid import uuid4
from io import BytesIO
import warnings
from app.services.matching_service import calculate_hybrid_score
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    UploadFile,
    File,
    Query
)
from sqlalchemy.orm import Session

from PIL import Image, UnidentifiedImageError

from app.db.session import get_db
from app.models.item import Item
from app.models.user import User
from app.schemas.item import ItemCreate, ItemUpdate, ItemResponse

from app.services.item_service import (
    create_item,
    get_all_items,
    get_item_by_id,
    search_items,
    update_item,
    delete_item
)

from app.services.embedding_service import generate_embedding
from app.api.dependencies import get_current_user


router = APIRouter(prefix="/items", tags=["Items"])


# Image storage directory
UPLOAD_DIR = Path(__file__).resolve().parents[2] / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Allowed image formats
ALLOWED_TYPES = {
    ".jpg": ("image/jpeg", "JPEG"),
    ".jpeg": ("image/jpeg", "JPEG"),
    ".png": ("image/png", "PNG"),
    ".webp": ("image/webp", "WEBP")
}

MAX_FILE_SIZE = 5 * 1024 * 1024
MAX_IMAGE_PIXELS = 20_000_000


def validate_image(contents: bytes, extension: str, content_type: str):
    """Validate the actual image content using Pillow."""

    expected_type, expected_format = ALLOWED_TYPES[extension]

    if content_type != expected_type:
        raise HTTPException(
            status_code=400,
            detail="File extension and image type do not match"
        )

    try:
        with warnings.catch_warnings():
            warnings.simplefilter(
                "error",
                Image.DecompressionBombWarning
            )

            image = Image.open(BytesIO(contents))

            detected_format = image.format
            width, height = image.size

            if detected_format != expected_format:
                raise HTTPException(
                    status_code=400,
                    detail="The uploaded file is not a valid image of the selected format"
                )

            if width <= 0 or height <= 0:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid image dimensions"
                )

            if width * height > MAX_IMAGE_PIXELS:
                raise HTTPException(
                    status_code=400,
                    detail="Image dimensions must not exceed 20 megapixels"
                )

            image.verify()

    except HTTPException:
        raise

    except (
        UnidentifiedImageError,
        Image.DecompressionBombError,
        Image.DecompressionBombWarning,
        OSError,
        SyntaxError,
        ValueError
    ):
        raise HTTPException(
            status_code=400,
            detail="Invalid or corrupted image file"
        )


def get_existing_upload_path(image_url: str | None):
    """Return an existing upload path safely inside the uploads directory."""

    if not image_url or not image_url.startswith("/uploads/"):
        return None

    filename = image_url.removeprefix("/uploads/")

    if not filename or Path(filename).name != filename:
        return None

    candidate = (UPLOAD_DIR / filename).resolve()

    try:
        candidate.relative_to(UPLOAD_DIR.resolve())
    except ValueError:
        return None

    if candidate.is_file():
        return candidate

    return None


# ==========================================
# CREATE ITEM - Login required
# ==========================================

@router.post("/", response_model=ItemResponse, status_code=201)
def create_new_item(
    data: ItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        new_item = create_item(db, data, current_user.id)
        return new_item

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Unable to create item"
        )


# ==========================================
# MY REPORTS - Login required
# ==========================================

@router.get("/my-reports", response_model=list[ItemResponse])
def get_my_reports(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    reports = (
        db.query(Item)
        .filter(Item.owner_id == current_user.id)
        .order_by(Item.id.desc())
        .all()
    )

    return reports


# ==========================================
# UPLOAD OR REPLACE IMAGE - Owner only
# ==========================================

@router.post("/{item_id}/image", response_model=ItemResponse)
async def upload_item_image(
    item_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    destination = None

    try:
        item = get_item_by_id(db, item_id)

        if item is None:
            raise HTTPException(
                status_code=404,
                detail="Item not found"
            )

        if item.owner_id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="You can only upload images to your own reports"
            )

        extension = Path(file.filename or "").suffix.lower()

        if extension not in ALLOWED_TYPES:
            raise HTTPException(
                status_code=400,
                detail="Only JPG, JPEG, PNG and WebP images are allowed"
            )

        contents = await file.read(MAX_FILE_SIZE + 1)

        if len(contents) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail="Image size must not exceed 5 MB"
            )

        if not contents:
            raise HTTPException(
                status_code=400,
                detail="Uploaded image is empty"
            )

        validate_image(
            contents,
            extension,
            file.content_type or ""
        )

        old_image_path = get_existing_upload_path(item.image_url)

        filename = f"{uuid4().hex}{extension}"
        destination = UPLOAD_DIR / filename

        destination.write_bytes(contents)

        item.image_url = f"/uploads/{filename}"

        db.commit()
        db.refresh(item)

        if old_image_path and old_image_path != destination:
            try:
                old_image_path.unlink(missing_ok=True)
            except OSError:
                pass

        return item

    except HTTPException:
        if destination and destination.exists():
            destination.unlink(missing_ok=True)
        raise

    except Exception:
        db.rollback()

        if destination and destination.exists():
            destination.unlink(missing_ok=True)

        raise HTTPException(
            status_code=500,
            detail="Unable to upload image"
        )

    finally:
        await file.close()


# ==========================================
# VIEW ALL ITEMS - Public
# ==========================================

@router.get("/", response_model=list[ItemResponse])
def read_all_items(
    db: Session = Depends(get_db)
):
    return get_all_items(db)


# ==========================================
# SEARCH ITEMS - Public
# ==========================================

@router.get("/search", response_model=list[ItemResponse])
def search_item_reports(
    keyword: str | None = None,
    item_type: str | None = None,
    category: str | None = None,
    location: str | None = None,
    db: Session = Depends(get_db)
):
    return search_items(
        db,
        keyword,
        item_type,
        category,
        location
    )


# ==========================================
# AI SEMANTIC MATCHING - Public
# ==========================================


@router.get("/{item_id}/matches")
def find_semantic_matches(
    item_id: int,
    limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """
    Find potential lost-and-found matches using hybrid scoring.
    """

    try:
        source_item = get_item_by_id(db, item_id)

        if source_item is None:
            raise HTTPException(
                status_code=404,
                detail="Item not found"
            )

        if source_item.item_type not in ("lost", "found"):
            raise HTTPException(
                status_code=400,
                detail="Invalid item type"
            )

        # Backfill embeddings for older reports.
        missing_embeddings = (
            db.query(Item)
            .filter(Item.embedding.is_(None))
            .all()
        )

        for item in missing_embeddings:
            item.embedding = generate_embedding(
                title=item.title,
                description=item.description,
                category=item.category,
                location=item.location,
                item_type=item.item_type
            )

        if missing_embeddings:
            db.commit()

        db.refresh(source_item)

        if source_item.embedding is None:
            source_item.embedding = generate_embedding(
                title=source_item.title,
                description=source_item.description,
                category=source_item.category,
                location=source_item.location,
                item_type=source_item.item_type
            )
            db.commit()
            db.refresh(source_item)

        opposite_type = (
            "found" if source_item.item_type == "lost" else "lost"
        )

        distance = Item.embedding.cosine_distance(
            source_item.embedding
        )

        candidates = (
            db.query(Item, distance.label("distance"))
            .filter(
                Item.id != source_item.id,
                Item.item_type == opposite_type,
                Item.embedding.isnot(None)
            )
            .order_by(distance.asc())
            .all()
        )

        matches = []

        for candidate, cosine_distance in candidates:

            semantic_score = max(
                0.0,
                min(100.0, (1.0 - float(cosine_distance)) * 100)
            )

            hybrid_score = calculate_hybrid_score(
                source=source_item,
                candidate=candidate,
                semantic_score=semantic_score
            )

            # Suppress weak candidates.
            if hybrid_score < 55:
                continue

            matches.append({
                "id": candidate.id,
                "title": candidate.title,
                "description": candidate.description,
                "item_type": candidate.item_type,
                "category": candidate.category,
                "location": candidate.location,
                "event_date": candidate.event_date,
                "image_url": candidate.image_url,
                "similarity_score": hybrid_score
            })

        matches.sort(
            key=lambda match: match["similarity_score"],
            reverse=True
        )

        matches = matches[:limit]

        return {
            "source_item_id": source_item.id,
            "source_title": source_item.title,
            "source_type": source_item.item_type,
            "compared_against": opposite_type,
            "total_matches": len(matches),
            "matches": matches
        }

    except HTTPException:
        raise

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Unable to find semantic matches"
        )



# ==========================================
# VIEW INDIVIDUAL ITEM - Public
# ==========================================

@router.get("/{item_id}", response_model=ItemResponse)
def read_item(
    item_id: int,
    db: Session = Depends(get_db)
):
    item = get_item_by_id(db, item_id)

    if item is None:
        raise HTTPException(
            status_code=404,
            detail="Item not found"
        )

    return item


# ==========================================
# UPDATE ITEM - Owner only
# ==========================================

@router.put("/{item_id}", response_model=ItemResponse)
def update_existing_item(
    item_id: int,
    data: ItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    item = get_item_by_id(db, item_id)

    if item is None:
        raise HTTPException(
            status_code=404,
            detail="Item not found"
        )

    if item.owner_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You can only update your own reports"
        )

    try:
        return update_item(db, item_id, data)

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Unable to update item"
        )


# ==========================================
# DELETE ITEM - Owner only
# ==========================================

@router.delete("/{item_id}")
def remove_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    item = get_item_by_id(db, item_id)

    if item is None:
        raise HTTPException(
            status_code=404,
            detail="Item not found"
        )

    if item.owner_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You can only delete your own reports"
        )

    if not delete_item(db, item_id):
        raise HTTPException(
            status_code=404,
            detail="Item not found"
        )

    return {
        "message": "Item deleted successfully",
        "item_id": item_id
    }
