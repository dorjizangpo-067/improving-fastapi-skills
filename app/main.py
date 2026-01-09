from typing import Annotated

from fastapi import FastAPI, Depends, HTTPException
from sqlmodel import SQLModel, create_engine, Field, Session, select
from pydantic import BaseModel

class HeroBase(SQLModel):
    name: str = Field(index=True)
    age: int | None = None

class Hero(HeroBase, table = True):
    id: int | None = Field(default=None, primary_key=True)
    secret_name: str

class HeroPublic(HeroBase):
    id: int

class HeroCreate(HeroBase):
    secret_name: str

class HeroUpdate(HeroBase):
    name: str | None = None
    age: int | None = None
    secret_name: str | None = None


sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

engine = create_engine(url=sqlite_url, connect_args={"check_same_thread": False})

def create_db_and_tabble():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session


app = FastAPI()

@app.on_event("startup")
def on_startup():
    create_db_and_tabble()

@app.post("/heros/", response_model=HeroPublic)
def create_hero(hero: HeroCreate, session: Annotated[Session, Depends(get_session)]):
    hero = Hero.model_validate(hero)
    session.add(hero)
    session.commit()
    session.refresh(hero)
    return hero

@app.get("/heros/all", response_model=list[HeroPublic])
async def get_all_heros(session: Annotated[Session, Depends(get_session)], offset: int = 0, limit: int = 2) -> list[Hero]:
    heroes = session.exec(
        select(Hero).offset(offset).limit(limit)
    ).all()
    return heroes

@app.get("/heros/{hero_id}", response_model=HeroPublic)
async def get_one_hero(hero_id: int, session: Annotated[Session, Depends(get_session)]) -> Hero:
    hero = session.get(Hero, hero_id)
    if not hero:
        raise HTTPException(status_code=404, detail="Hero not found")
    return hero

@app.delete("/heros/{hero_id}")
def delet_hero(hero_id: int, session: Annotated[Session, Depends(get_session)]) -> dict:
    hero = session.get(Hero, hero_id)
    session.delete(hero)
    session.commit()
    return {"message": "Hero Deleted"}

@app.patch("/heros/{hero_id}", response_model=HeroPublic)
async def update_hero(hero_id: int, form: HeroUpdate, session: Annotated[Session, Depends(get_session)]) -> Hero:
    hero = session.get(Hero, hero_id)
    if not hero:
        raise HTTPException(status_code=404, detail="Hero not found")
    hero_data = form.model_dump(exclude_unset=True)
    hero.sqlmodel_update(hero_data)
    session.commit()
    session.refresh(hero)
    return hero