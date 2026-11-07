
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.item import Item
from app.schemas.item import ItemCreate, ItemUpdate
from app.services.embedding_service import generate_embedding


def create_item(db: Session, data: ItemCreate, owner_id: int):
    item_data = data.model_dump()

    # Generate AI embedding for the new item
    embedding = generate_embedding(
        title=item_data["title"],
        description=item_data["description"],
        category=item_data["category"],
        location=item_data["location"],
        item_type=item_data["item_type"]
    )

    item = Item(
        **item_data,
        owner_id=owner_id,
        embedding=embedding
    )

    try:
        db.add(item)
        db.commit()
        db.refresh(item)
        return item
    except Exception:
        db.rollback()
        raise


def get_all_items(db: Session):
    return db.query(Item).order_by(Item.created_at.desc()).all()


def get_item_by_id(db: Session, item_id: int):
    return db.query(Item).filter(Item.id == item_id).first()


def search_items(
    db: Session,
    keyword=None,
    item_type=None,
    category=None,
    location=None
):
    query = db.query(Item)

    if keyword:
        term = f"%{keyword}%"
        query = query.filter(
            or_(
                Item.title.ilike(term),
                Item.description.ilike(term)
            )
        )

    if item_type:
        query = query.filter(Item.item_type.ilike(item_type))

    if category:
        query = query.filter(Item.category.ilike(f"%{category}%"))

    if location:
        query = query.filter(Item.location.ilike(f"%{location}%"))

    return query.order_by(Item.created_at.desc()).all()


def update_item(db: Session, item_id: int, data: ItemUpdate):
    item = get_item_by_id(db, item_id)

    if item is None:
        return None

    updates = data.model_dump(exclude_unset=True)

    # Apply the requested changes
    for key, value in updates.items():
        setattr(item, key, value)

    # Regenerate embedding using the updated item information
    item.embedding = generate_embedding(
        title=item.title,
        description=item.description,
        category=item.category,
        location=item.location,
        item_type=item.item_type
    )

    try:
        db.commit()
        db.refresh(item)
        return item
    except Exception:
        db.rollback()
        raise


def delete_item(db: Session, item_id: int):
    item = get_item_by_id(db, item_id)

    if item is None:
        return False

    try:
        db.delete(item)
        db.commit()
        return True
    except Exception:
        db.rollback()
        raise
