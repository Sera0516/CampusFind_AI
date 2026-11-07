
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.claim import Claim
from app.models.item import Item
from app.models.user import User
from app.models.notification import Notification

from app.schemas.claim import (
    ClaimCreate,
    ClaimResponse,
    ClaimReview
)

from app.api.dependencies import get_current_user


router = APIRouter(
    prefix="/claims",
    tags=["Claims"]
)


# --------------------------------------------------
# 1. Submit a claim for a found item
# --------------------------------------------------

@router.post(
    "/",
    response_model=ClaimResponse,
    status_code=status.HTTP_201_CREATED
)
def create_claim(
    claim_data: ClaimCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    item = db.query(Item).filter(
        Item.id == claim_data.item_id
    ).first()

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found."
        )

    if item.item_type.lower() != "found":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Claims can only be submitted for found items."
        )

    if item.owner_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot claim your own item report."
        )

    existing_claim = db.query(Claim).filter(
        Claim.item_id == claim_data.item_id,
        Claim.claimant_id == current_user.id,
        Claim.status == "pending"
    ).first()

    if existing_claim:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You already have a pending claim for this item."
        )

    new_claim = Claim(
        item_id=claim_data.item_id,
        claimant_id=current_user.id,
        message=claim_data.message,
        status="pending"
    )

    db.add(new_claim)
    db.flush()

    # Create notification for item owner
    owner_notification = Notification(
        user_id=item.owner_id,
        item_id=item.id,
        claim_id=new_claim.id,
        title="New Ownership Claim",
        message=(
            f"{current_user.email} has submitted an ownership "
            f"claim for your found item: {item.title}."
        ),
        notification_type="new_claim",
        is_read=False
    )

    db.add(owner_notification)

    db.commit()
    db.refresh(new_claim)

    return new_claim


# --------------------------------------------------
# 2. View claims received by the logged-in item owner
# --------------------------------------------------

@router.get(
    "/received",
    response_model=list[ClaimResponse]
)
def get_received_claims(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    claims = (
        db.query(Claim)
        .join(Item, Claim.item_id == Item.id)
        .filter(Item.owner_id == current_user.id)
        .order_by(Claim.created_at.desc())
        .all()
    )

    return claims


# --------------------------------------------------
# 3. View claims submitted by the logged-in student
# --------------------------------------------------

@router.get(
    "/my-claims",
    response_model=list[ClaimResponse]
)
def get_my_claims(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    claims = (
        db.query(Claim)
        .filter(
            Claim.claimant_id == current_user.id
        )
        .order_by(Claim.created_at.desc())
        .all()
    )

    return claims




# --------------------------------------------------
# 4. Approve or reject a claim and notify claimant
# --------------------------------------------------

@router.patch(
    "/{claim_id}/review",
    response_model=ClaimResponse
)
def review_claim(
    claim_id: int,
    review_data: ClaimReview,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    claim = db.query(Claim).filter(
        Claim.id == claim_id
    ).first()

    if not claim:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Claim not found."
        )

    item = db.query(Item).filter(
        Item.id == claim.item_id
    ).first()

    if not item or item.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to review this claim."
        )

    if claim.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This claim has already been reviewed."
        )

    claim.status = review_data.status
    claim.owner_response = review_data.owner_response

    # Create notification for the claimant
    if review_data.status == "approved":
        notification_title = "Claim Approved"
        notification_message = (
            f"Your ownership claim for '{item.title}' "
            "has been approved by the item owner."
        )
        notification_type = "claim_approved"

    else:
        notification_title = "Claim Rejected"
        notification_message = (
            f"Your ownership claim for '{item.title}' "
            "has been rejected by the item owner."
        )
        notification_type = "claim_rejected"

    claimant_notification = Notification(
        user_id=claim.claimant_id,
        item_id=item.id,
        claim_id=claim.id,
        title=notification_title,
        message=notification_message,
        notification_type=notification_type,
        is_read=False
    )

    db.add(claimant_notification)

    db.commit()
    db.refresh(claim)

    return claim

