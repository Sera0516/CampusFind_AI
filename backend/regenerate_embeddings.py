
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.item import Item
from app.services.embedding_service import generate_embedding


def regenerate_all_embeddings():
    db: Session = SessionLocal()

    try:
        items = db.query(Item).order_by(Item.id).all()

        print(f"Found {len(items)} reports.")

        for item in items:
            item.embedding = generate_embedding(
                title=item.title,
                description=item.description,
                category=item.category,
                location=item.location,
                item_type=item.item_type
            )

            print(f"Updated embedding for item ID: {item.id}")

        db.commit()

        print("\nAll embeddings regenerated successfully.")

    except Exception as error:
        db.rollback()
        print(f"Embedding regeneration failed: {error}")
        raise

    finally:
        db.close()


if __name__ == "__main__":
    regenerate_all_embeddings()
