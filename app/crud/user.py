from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user import UserCreate
from typing import Optional, List

def get_user(db: Session, user_id: int) -> Optional[User]:
    """Get user by internal ID"""
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Get user by email"""
    return db.query(User).filter(User.email == email).first()

def get_user_by_supabase_id(db: Session, supabase_user_id: str) -> Optional[User]:
    """Get user by Supabase user ID"""
    return db.query(User).filter(User.supabase_user_id == supabase_user_id).first()

def get_users(db: Session, skip: int = 0, limit: int = 100):
    """Get all users with pagination"""
    return db.query(User).offset(skip).limit(limit).all()

def create_user(db: Session, user_data: dict) -> User:
    """Create a new user record"""
    db_user = User(**user_data)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user(db: Session, user_id: int, user_data: dict) -> Optional[User]:
    """Update user information (only application fields)"""
    db_user = get_user(db, user_id)
    if not db_user:
        return None
    
    # Only allow updating application fields
    allowed_fields = ["is_active", "is_superuser"]
    for field, value in user_data.items():
        if field in allowed_fields and value is not None:
            setattr(db_user, field, value)
    
    db.commit()
    db.refresh(db_user)
    return db_user

def delete_user(db: Session, user_id: int) -> bool:
    """Delete a user record"""
    db_user = get_user(db, user_id)
    if not db_user:
        return False
    
    db.delete(db_user)
    db.commit()
    return True

class UserCRUD:
    def get_by_id(self, db: Session, user_id: int) -> Optional[User]:
        """Get user by internal ID"""
        return db.query(User).filter(User.id == user_id).first()

    def get_by_email(self, db: Session, email: str) -> Optional[User]:
        """Get user by email"""
        return db.query(User).filter(User.email == email).first()

    def get_by_supabase_id(self, db: Session, supabase_user_id: str) -> Optional[User]:
        """Get user by Supabase user ID"""
        return db.query(User).filter(User.supabase_user_id == supabase_user_id).first()

    def get_all(self, db: Session, skip: int = 0, limit: int = 100) -> List[User]:
        """Get all users with pagination"""
        return db.query(User).offset(skip).limit(limit).all()

    def create(self, db: Session, user_data: dict) -> User:
        """Create a new user record"""
        db_user = User(**user_data)
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user

    def update(self, db: Session, user_id: int, user_data: dict) -> Optional[User]:
        """Update user information (only application fields)"""
        db_user = self.get_by_id(db, user_id)
        if not db_user:
            return None
        
        # Only allow updating application fields
        allowed_fields = ["is_active", "is_superuser"]
        for field, value in user_data.items():
            if field in allowed_fields and value is not None:
                setattr(db_user, field, value)
        
        db.commit()
        db.refresh(db_user)
        return db_user

    def delete(self, db: Session, user_id: int) -> bool:
        """Delete a user record"""
        db_user = self.get_by_id(db, user_id)
        if not db_user:
            return False
        
        db.delete(db_user)
        db.commit()
        return True

# Create instance
user_crud = UserCRUD() 