from fastapi import FastAPI, Form, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta


app = FastAPI()


class Flower(BaseModel):
    name: str
    color: str
    price: float


class FlowersRepository:
    flowers = []
    current_id = 0

    @classmethod
    def add_flower(cls, flower: dict):
        cls.current_id += 1
        flower["id"] = cls.current_id
        cls.flowers.append(flower)
        return flower["id"]

    @classmethod
    def get_flower_by_id(cls, flower_id: int):
        return next((f for f in cls.flowers if f["id"] == flower_id), None)

    @classmethod
    def get_all_flowers(cls):
        return cls.flowers


class CartRepository:
    cart = []

    @classmethod
    def add_item(cls, flower_id: int):
        cls.cart.append(flower_id)

    @classmethod
    def get_cart_items(cls):
        return cls.cart

FlowersRepository.add_flower({"name": "Rose", "color": "Red", "price": 10.0})
FlowersRepository.add_flower({"name": "Tulip", "color": "Yellow", "price": 7.5})

class UsersRepository:
    users = []

    @classmethod
    def add_user(cls, user: dict):
        cls.users.append(user)

    @classmethod
    def get_user_by_email(cls, email: str):
        return next((u for u in cls.users if u["email"] == email), None)


SECRET_KEY = "supersecretkey"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class Token(BaseModel):
    access_token: str
    token_type: str


class User(BaseModel):
    username: str
    email: str
    hashed_password: str

class UserInDB(User):
    password: str


class UserProfile(BaseModel):
    username: str
    email: str


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = UsersRepository.get_user_by_email(email=email)
    if user is None:
        raise credentials_exception
    return user


@app.post("/signup")
def signup(username: str, email: str, password: str):
    hashed_password = get_password_hash(password)
    UsersRepository.add_user({"username": username, "email": email, "password": hashed_password})
    return {"message": "User registered successfully"}


@app.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = UsersRepository.get_user_by_email(form_data.username)
    if not user or not verify_password(form_data.password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user["email"]}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/profile", response_model=UserProfile)
def profile(current_user: User = Depends(get_current_user)):
    return {
        "username": current_user["username"],
        "email": current_user["email"]
    }


@app.get("/flowers", response_model=list[Flower])
def get_flowers():
    return FlowersRepository.get_all_flowers()


@app.post("/flowers")
def add_flower(flower: Flower):
    flower_id = FlowersRepository.add_flower(flower.dict())
    return {"id": flower_id}


@app.post("/cart/items")
def add_to_cart(flower_id: int = Form()):
    flower = FlowersRepository.get_flower_by_id(flower_id)
    if not flower:
        raise HTTPException(status_code=404, detail="Flower not found")

    CartRepository.add_item(flower_id)
    return {"message": "Item added to cart"}



@app.get("/cart/items")
def get_cart_items():
    cart_items = CartRepository.get_cart_items()
    flowers = FlowersRepository.get_all_flowers()

    cart_details = []
    total_price = 0.0

    for flower_id in cart_items:
        flower = next((f for f in flowers if f["id"] == flower_id), None)
        if flower:
            cart_details.append({
                "id": flower["id"],
                "name": flower["name"],
                "price": flower["price"]
            })
            total_price += flower["price"]

    return {"items": cart_details, "total_price": total_price}