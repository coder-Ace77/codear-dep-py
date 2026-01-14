from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user_schema import RegisterDTO, LoginDTO
from app.core import security
from fastapi import HTTPException

class UserService:
    def __init__(self, db: Session):
        self.db = db

    def register_user(self, data: RegisterDTO):
        # Check if email/username exists
        if self.db.query(User).filter(User.email == data.email).first():
            raise HTTPException(status_code=400, detail="Email already in use")
        
        if self.db.query(User).filter(User.username == data.username).first():
            raise HTTPException(status_code=400, detail="Username already taken")

        hashed_password = security.get_password_hash(data.password)
        
        new_user = User(
            username=data.username,
            name=data.name,
            email=data.email,
            password=hashed_password,
            role="USER",
            daily_streak=0,
            problem_solved_total=0
        )
        
        self.db.add(new_user)
        self.db.commit()
        self.db.refresh(new_user)
        return new_user

    def login_user(self, data: LoginDTO):
        user = self.db.query(User).filter(User.email == data.email).first()
        if not user or not security.verify_password(data.password, user.password):
            return None
        
        # Generate JWT token using user ID as subject
        return security.create_access_token(data={"sub": str(user.id)})

    def get_user_by_id(self, user_id: int):
        return self.db.query(User).filter(User.id == user_id).first()