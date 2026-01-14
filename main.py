import os
import datetime
from typing import List, Optional
from fastapi import FastAPI, Request, Form, Depends, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, UniqueConstraint, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
import httpx

# --- Database Setup ---
SQLALCHEMY_DATABASE_URL = "sqlite:///./thebestbookon.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class Prompt(Base):
    __tablename__ = "prompts"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String)
    creator_username = Column(String)
    tag1 = Column(String, nullable=True)
    tag2 = Column(String, nullable=True)
    tag3 = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    submissions = relationship("Submission", back_populates="prompt")

class Submission(Base):
    __tablename__ = "submissions"
    id = Column(Integer, primary_key=True, index=True)
    prompt_id = Column(Integer, ForeignKey("prompts.id"))
    openlibrary_edition_key = Column(String)  # Should be OL...M
    submitter_username = Column(String)
    # Cached metadata to avoid API hammer
    title = Column(String)
    cover_id = Column(Integer, nullable=True) 
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    prompt = relationship("Prompt", back_populates="submissions")
    votes = relationship("Vote", back_populates="submission")
    
    # helper to check total score
    @property
    def score(self):
        return sum([v.value for v in self.votes])

    @property
    def openlibrary_url(self):
        # We always prefer linking to the specific edition now
        return f"https://openlibrary.org/books/{self.openlibrary_edition_key}"

class Vote(Base):
    __tablename__ = "votes"
    id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(Integer, ForeignKey("submissions.id"))
    voter_username = Column(String)
    value = Column(Integer) # 1 or -1
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    submission = relationship("Submission", back_populates="votes")
    
    __table_args__ = (
        UniqueConstraint('voter_username', 'submission_id', name='unique_user_vote_per_submission'),
    )

Base.metadata.create_all(bind=engine)

# --- App Setup ---
app = FastAPI(title="TheBestBookOn")

# Mount static files (css, js)
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
os.makedirs("templates", exist_ok=True)
templates = Jinja2Templates(directory="templates")

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Mock Auth ---
# For now, we simulate a logged-in user. In production, this would read from headers/cookie session.
def get_current_user(request: Request):
    # Retrieve username from query param for easy testing during dev, or default to 'test_user'
    return request.query_params.get("user", "internet_archive_fan")

# --- Routes ---

@app.get("/", response_class=HTMLResponse)
def read_root(request: Request, db: Session = Depends(get_db), user: str = Depends(get_current_user)):
    prompts = db.query(Prompt).order_by(Prompt.created_at.desc()).all()
    
    # Enrich prompts with stats
    prompts_data = []
    for p in prompts:
        subs = p.submissions
        subs.sort(key=lambda s: s.score, reverse=True)
        top_3 = subs[:3]
        
        total_votes = sum([s.score for s in subs])
        # Count unique voters
        # This is a bit inefficient (n+1) but fine for "few hundred prompts" limit
        voter_ids = set()
        for s in subs:
            for v in s.votes:
                voter_ids.add(v.voter_username)
        total_voters = len(voter_ids)
        
        prompts_data.append({
            "id": p.id,
            "title": p.title,
            "description": p.description,
            "creator_username": p.creator_username,
            "tag1": p.tag1, "tag2": p.tag2, "tag3": p.tag3,
            "top_books": top_3,
            "total_books": len(subs),
            "total_votes": total_votes,
            "total_voters": total_voters
        })
        
    return templates.TemplateResponse("index.html", {"request": request, "prompts": prompts_data, "user": user})

@app.get("/prompts/{prompt_id}", response_class=HTMLResponse)
def read_prompt(prompt_id: int, request: Request, db: Session = Depends(get_db), user: str = Depends(get_current_user)):
    prompt = db.query(Prompt).filter(Prompt.id == prompt_id).first()
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")
    
    submissions = prompt.submissions
    # Sort submissions by score
    submissions.sort(key=lambda s: s.score, reverse=True)
    
    # Check if user voted
    for sub in submissions:
        sub.user_has_voted = any(v.voter_username == user for v in sub.votes)
    
    return templates.TemplateResponse("prompt_detail.html", {
        "request": request, 
        "prompt": prompt, 
        "submissions": submissions,
        "user": user
    })

# Form to create a prompt
@app.post("/prompts")
def create_prompt(
    title: str = Form(...),
    description: str = Form(...),
    tag1: str = Form(None),
    tag2: str = Form(None),
    tag3: str = Form(None),
    db: Session = Depends(get_db),
    user: str = Depends(get_current_user)
):
    new_prompt = Prompt(
        title=title,
        description=description,
        creator_username=user,
        tag1=tag1,
        tag2=tag2,
        tag3=tag3
    )
    db.add(new_prompt)
    db.commit()
    db.refresh(new_prompt)
    return RedirectResponse(url=f"/prompts/{new_prompt.id}", status_code=303)

# Search OpenLibrary (Proxy to avoid CORS/simplify client)
@app.get("/api/search_books")
async def search_books(q: str):
    async with httpx.AsyncClient() as client:
        # Searching fields=key,title,author_name,cover_i,first_publish_year,edition_key
        url = f"https://openlibrary.org/search.json?q={q}&fields=key,title,author_name,cover_i,first_publish_year,edition_key&limit=5"
        resp = await client.get(url)
        return resp.json()

@app.post("/prompts/{prompt_id}/submit")
def submit_book(
    prompt_id: int,
    edition_key: str = Form(...),
    title: str = Form(...),
    cover_id: int = Form(None),
    comment: str = Form(None),
    db: Session = Depends(get_db),
    user: str = Depends(get_current_user)
):
    # Check if already submitted?
    existing = db.query(Submission).filter(
        Submission.prompt_id == prompt_id,
        Submission.openlibrary_edition_key == edition_key
    ).first()
    
    submission = existing
    if not existing:
        submission = Submission(
            prompt_id=prompt_id,
            openlibrary_edition_key=edition_key,
            title=title,
            cover_id=cover_id,
            submitter_username=user
        )
        db.add(submission)
        db.commit()
        db.refresh(submission)
    
    # Auto-vote for the submission
    existing_vote = db.query(Vote).filter(
        Vote.submission_id == submission.id,
        Vote.voter_username == user
    ).first()
    
    if not existing_vote:
        vote = Vote(
            submission_id=submission.id,
            voter_username=user,
            value=1,
            comment=comment
        )
        db.add(vote)
        db.commit()
        
    return RedirectResponse(url=f"/prompts/{prompt_id}", status_code=303)

@app.post("/vote")
def vote_submission(
    submission_id: int = Form(...),
    value: int = Form(...), # 1 or -1
    db: Session = Depends(get_db),
    user: str = Depends(get_current_user)
):
    # upsert vote
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
        
    existing_vote = db.query(Vote).filter(
        Vote.submission_id == submission_id,
        Vote.voter_username == user
    ).first()
    
    if existing_vote:
        existing_vote.value = value
    else:
        new_vote = Vote(
            submission_id=submission_id,
            voter_username=user,
            value=value
        )
        db.add(new_vote)
    
    db.commit()
    # Redirect back to the prompt page? We need the prompt id.
    return RedirectResponse(url=f"/prompts/{submission.prompt_id}", status_code=303)

