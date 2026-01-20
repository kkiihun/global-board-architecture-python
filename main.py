# main.py (교육용 최종 버전)
from fastapi import FastAPI, Depends, HTTPException, status, Response, Cookie, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.orm import sessionmaker, Session, relationship, declarative_base
from passlib.context import CryptContext
from jose import JWTError, jwt
from typing import List, Optional

# ==========================================
# 1. 환경 설정 (Configuration)
# ==========================================
# [주의] 실무에서는 이 키들을 코드에 적지 말고 .env 파일에서 불러와야 함!
SECRET_KEY = "education_demo_secret_key" 
ALGORITHM = "HS256"

# DB 연결 설정 (SQLite는 파일 하나로 DB 역할 수행)
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
# check_same_thread=False: SQLite를 쓰레드 환경(웹서버)에서 쓸 때 필수 옵션
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 비밀번호 암호화 도구 (bcrypt 알고리즘 사용)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTML 템플릿 폴더 지정
templates = Jinja2Templates(directory="templates")

# ==========================================
# 2. 데이터베이스 모델 (ORM)
# ==========================================
# DB 테이블을 파이썬 클래스로 정의하는 과정
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String) # [보안] 비밀번호는 절대 평문으로 저장 금지
    
    # 관계 설정: 유저가 쓴 글들을 posts로 접근 가능
    posts = relationship("Post", back_populates="owner")

class Post(Base):
    __tablename__ = "posts"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    content = Column(String)
    owner_id = Column(Integer, ForeignKey("users.id")) # 외래키(FK)
    
    owner = relationship("User", back_populates="posts")

# 정의한 모델대로 DB 테이블 자동 생성
Base.metadata.create_all(bind=engine)

# ==========================================
# 3. Pydantic 스키마 (데이터 검증)
# ==========================================
# API 요청/응답 시 데이터의 형식을 검사하는 역할
class UserCreate(BaseModel):
    email: str
    password: str

class PostCreate(BaseModel):
    title: str
    content: str

class PostResponse(BaseModel):
    id: int
    title: str
    content: str
    owner_id: int
    class Config:
        from_attributes = True # ORM 객체를 Pydantic 모델로 변환 허용

# ==========================================
# 4. 의존성 함수 (Dependencies)
# ==========================================
# [핵심] DB 세션을 열고, 일이 끝나면 반드시 닫아주는 함수
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# JWT 토큰 생성 함수
def create_access_token(data: dict):
    to_encode = data.copy()
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# [핵심] 쿠키에서 토큰을 꺼내 유저를 찾는 함수 (모든 보호된 API에서 사용)
def get_current_user(access_token: str = Cookie(None), db: Session = Depends(get_db)):
    if not access_token:
        # API 요청일 때는 401 에러를 던지는 게 맞지만, 
        # 여기서는 Depends로 재사용하기 위해 None 반환 처리도 고려해야 함.
        # 교육 편의상 에러 발생시킴
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")
    
    try:
        payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="유효하지 않은 토큰")
    except JWTError:
        raise HTTPException(status_code=401, detail="토큰 만료/오류")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="유저를 찾을 수 없음")
    return user

# UI 전용: 에러를 내지 않고 유저가 없으면 None을 주는 버전 (화면 렌더링용)
def get_current_user_optional(access_token: str = Cookie(None), db: Session = Depends(get_db)):
    if not access_token: return None
    try:
        payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        return db.query(User).filter(User.id == user_id).first()
    except:
        return None

# ==========================================
# 5. 라우터 (Controller)
# ==========================================
app = FastAPI()

# --- 화면(UI) 라우터 ---
@app.get("/", response_class=HTMLResponse)
def read_root(request: Request, db: Session = Depends(get_db), access_token: str = Cookie(None)):
    # 화면을 그릴 때는 로그인이 안 되어 있어도 에러가 나면 안 됨 (None 처리)
    user = get_current_user_optional(access_token, db)
    posts = db.query(Post).all()
    return templates.TemplateResponse("index.html", {"request": request, "user": user, "posts": posts})

@app.get("/login-page", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

# --- API 라우터 ---

@app.post("/signup")
def signup(user: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(status_code=400, detail="이미 가입된 이메일")
    
    hashed_pw = pwd_context.hash(user.password) # 비밀번호 해싱 필수
    new_user = User(email=user.email, hashed_password=hashed_pw)
    db.add(new_user)
    db.commit()
    return {"msg": "가입 완료"}

@app.post("/login")
def login(user: UserCreate, response: Response, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if not db_user or not pwd_context.verify(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="로그인 실패")
    
    token = create_access_token({"sub": str(db_user.id)})
    # [보안] HttpOnly=True: 자바스크립트로 쿠키 탈취 불가능하게 설정
    response.set_cookie(key="access_token", value=token, httponly=True)
    return {"msg": "로그인 성공"}

@app.post("/logout")
def logout(response: Response):
    response.delete_cookie("access_token")
    return {"msg": "로그아웃"}

# [정석 패턴] Depends(get_current_user)를 사용하여 중복 코드 제거
@app.post("/posts", response_model=PostResponse)
def create_post(post: PostCreate, 
                db: Session = Depends(get_db), 
                current_user: User = Depends(get_current_user)):
    # 위 Depends에서 이미 로그인 체크가 끝남. 여기선 로직만 집중.
    new_post = Post(title=post.title, content=post.content, owner_id=current_user.id)
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    return new_post

@app.put("/posts/{post_id}", response_model=PostResponse)
def update_post(post_id: int, post: PostCreate, 
                db: Session = Depends(get_db), 
                current_user: User = Depends(get_current_user)):
    
    existing_post = db.query(Post).filter(Post.id == post_id).first()
    if not existing_post:
        raise HTTPException(404, "글 없음")
    if existing_post.owner_id != current_user.id:
        raise HTTPException(403, "권한 없음")
    
    existing_post.title = post.title
    existing_post.content = post.content
    db.commit()
    return existing_post # refresh 불필요 (객체가 이미 메모리에 있음)

@app.delete("/posts/{post_id}")
def delete_post(post_id: int, 
                db: Session = Depends(get_db), 
                current_user: User = Depends(get_current_user)):
    
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(404, "글 없음")
    if post.owner_id != current_user.id:
        raise HTTPException(403, "권한 없음")
        
    db.delete(post)
    db.commit()
    return {"msg": "삭제 완료"}