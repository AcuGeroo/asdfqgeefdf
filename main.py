from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

DATABASE_URL = "sqlite:///./database.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()



class UserTable(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String, unique=True)


Base.metadata.create_all(bind=engine)


class UserCreate(BaseModel):
    name: str
    email: EmailStr


class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr

    class Config:
        orm_mode = True

app = FastAPI(title="Users API")


def get_db():
    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()


@app.get("/")
def home():
    return {"message": "Server works"}

@app.get("/users", response_model=list[UserResponse])
def get_users(db: Session = Depends(get_db)):
    users = db.query(UserTable).all()

    return users

@app.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(UserTable).filter(
        UserTable.id == user_id
    ).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    return user

@app.post("/users", response_model=UserResponse)
def create_user(
    user_in: UserCreate,
    db: Session = Depends(get_db)
):
    existing_user = db.query(UserTable).filter(
        UserTable.email == user_in.email
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already exists"
        )

    new_user = UserTable(
        name=user_in.name,
        email=user_in.email
    )

    db.add(new_user)

    db.commit()

    db.refresh(new_user)

    return new_user

@app.delete("/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(UserTable).filter(
        UserTable.id == user_id
    ).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    db.delete(user)

    db.commit()

    return {"message": "User deleted"}