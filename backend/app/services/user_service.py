from sqlalchemy.orm import Session
from app.models.user import User
from app.services.security import hash_password, verify_password, create_access_token

def register_user(db: Session, name: str, email: str, password: str):
    if db.query(User).filter(User.email == email).first():
        return None
    user = User(name=name, email=email, hashed_password=hash_password(password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def authenticate_user(db: Session, email: str, password: str):
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.hashed_password):
        return None
    return {"access_token": create_access_token(str(user.id)), "token_type": "bearer"}
