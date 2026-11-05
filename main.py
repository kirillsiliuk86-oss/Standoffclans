from fastapi import FastAPI, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from sqlalchemy.orm import relationship
import uvicorn
import os
import uuid

# Настройка базы данных (SQLite)
SQLALCHEMY_DATABASE_URL = "sqlite:///./standoff.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Player(Base):
    __tablename__ = "players"
    id = Column(Integer, primary_key=True, index=True)
    nickname = Column(String, unique=True, index=True)
    game_id = Column(String)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    clan_id = Column(Integer, ForeignKey("clans.id"), nullable=True)
    clan = relationship("Clan", back_populates="members")

class Clan(Base):
    __tablename__ = "clans"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    tag = Column(String)
    invite_link = Column(String, unique=True, default=lambda: str(uuid.uuid4())[:8])
    rating = Column(Integer, default=0)
    members = relationship("Player", back_populates="clan")

Base.metadata.create_all(bind=engine)

app = FastAPI()
templates = Jinja2Templates(directory=".")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/", response_class=HTMLResponse)
async def index(request: Request, db: Session = Depends(get_db)):
    clans = db.query(Clan).all()
    return templates.TemplateResponse("index.html", {"request": request, "clans": clans})

@app.post("/register")
async def register(nickname: str = Form(...), game_id: str = Form(...), email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    if db.query(Player).filter((Player.nickname == nickname) | (Player.email == email)).first():
        return HTMLResponse("<h2>Этот ник или почта уже заняты! <a href='/'>Назад</a></h2>")
    new_player = Player(nickname=nickname, game_id=game_id, email=email, password=password)
    db.add(new_player)
    db.commit()
    return RedirectResponse(url="/", status_code=303)

@app.post("/create_clan")
async def create_clan(name: str = Form(...), tag: str = Form(...), db: Session = Depends(get_db)):
    new_clan = Clan(name=name, tag=tag)
    db.add(new_clan)
    db.commit()
    return RedirectResponse(url="/", status_code=303)

@app.get("/privacy", response_class=HTMLResponse)
async def privacy():
    with open("privacy.html", "r", encoding="utf-8") as f: return HTMLResponse(f.read())

@app.get("/terms", response_class=HTMLResponse)
async def terms():
    with open("terms.html", "r", encoding="utf-8") as f: return HTMLResponse(f.read())

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
