from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user import UserCreate
from typing import Optional, List

def get_user(db: Session, user_id: int) -> Optional[User]:
    """Get user by internal ID"""
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_supabase_id(db: Session, supabase_user_id: str) -> Optional[User]:
    """Get user by Supabase user ID"""
    return db.query(User).filter(User.supabase_user_id == supabase_user_id).first()

def get_user_by_internal_id(db: Session, internal_user_id: str) -> Optional[User]:
    """Get user by internal user ID (for AWS linkage)"""
    return db.query(User).filter(User.internal_user_id == internal_user_id).first()

def get_users(db: Session, skip: int = 0, limit: int = 100):
    """Get all users with pagination"""
    return db.query(User).offset(skip).limit(limit).all()

def create_user(db: Session, supabase_user_id: str, internal_user_id: str, role: str = "patient") -> User:
    """Create a new user record for internal linkage"""
    db_user = User(
        supabase_user_id=supabase_user_id,
        internal_user_id=internal_user_id,
        role=role
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user(db: Session, user_id: int, user_data: dict) -> Optional[User]:
    """Update user information (only non-sensitive fields)"""
    db_user = get_user(db, user_id)
    if not db_user:
        return None
    
    # Only allow updating non-sensitive fields
    allowed_fields = ["role", "is_active", "is_superuser"]
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

def get_user_by_role(db: Session, role: str, skip: int = 0, limit: int = 100):
    """Get users by role"""
    return db.query(User).filter(User.role == role).offset(skip).limit(limit).all()

class UserCRUD:
    def get_by_id(self, db: Session, user_id: int) -> Optional[User]:
        """Get user by internal ID"""
        return db.query(User).filter(User.id == user_id).first()

    def get_by_supabase_id(self, db: Session, supabase_user_id: str) -> Optional[User]:
        """Get user by Supabase user ID"""
        return db.query(User).filter(User.supabase_user_id == supabase_user_id).first()

    def get_by_internal_id(self, db: Session, internal_user_id: str) -> Optional[User]:
        """Get user by internal user ID (for AWS linkage)"""
        return db.query(User).filter(User.internal_user_id == internal_user_id).first()

    def get_all(self, db: Session, skip: int = 0, limit: int = 100) -> List[User]:
        """Get all users with pagination"""
        return db.query(User).offset(skip).limit(limit).all()

    def create(self, db: Session, supabase_user_id: str, internal_user_id: str, role: str = "patient") -> User:
        """Create a new user record for internal linkage"""
        db_user = User(
            supabase_user_id=supabase_user_id,
            internal_user_id=internal_user_id,
            role=role
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user

    def update(self, db: Session, user_id: int, user_data: dict) -> Optional[User]:
        """Update user information (only non-sensitive fields)"""
        db_user = self.get_by_id(db, user_id)
        if not db_user:
            return None
        
        # Only allow updating non-sensitive fields
        allowed_fields = ["role", "is_active", "is_superuser"]
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

    def get_by_role(self, db: Session, role: str, skip: int = 0, limit: int = 100) -> List[User]:
        """Get users by role"""
        return db.query(User).filter(User.role == role).offset(skip).limit(limit).all()

# Create instance
user_crud = UserCRUD() 