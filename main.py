import os
import datetime
from typing import List, Optional
from fastapi import FastAPI, Request, Form, Depends, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, UniqueConstraint, Boolean, Text, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy.orm import sessionmaker, Session, relationship
import httpx
import secrets
from dotenv import load_dotenv
from starlette.middleware.sessions import SessionMiddleware
from internetarchive.config import get_auth_config
from internetarchive.exceptions import AuthenticationError
import requests

# --- Config & Secrets ---
if not os.path.exists(".env"):
    print("Generating new .env file with SECRET_KEY...")
    secret = secrets.token_urlsafe(32)
    with open(".env", "w") as f:
        f.write(f"SECRET_KEY={secret}\n")

load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")

# --- Database Setup ---
SQLALCHEMY_DATABASE_URL = "sqlite:///./thebestbookon.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Association Table for Many-to-Many
submission_tags = Table('submission_tags', Base.metadata,
    Column('submission_id', Integer, ForeignKey('submissions.id')),
    Column('tag_id', Integer, ForeignKey('tags.id'))
)

class Tag(Base):
    __tablename__ = "tags"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)

class Prompt(Base):
    __tablename__ = "prompts"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String)
    creator_username = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    submissions = relationship("Submission", back_populates="prompt")
    favorites = relationship("Favorite", back_populates="prompt")

class Submission(Base):
    __tablename__ = "submissions"
    id = Column(Integer, primary_key=True, index=True)
    prompt_id = Column(Integer, ForeignKey("prompts.id"))
    openlibrary_edition_key = Column(String)  # Should be OL...M
    submitter_username = Column(String)
    # Cached metadata to avoid API hammer
    title = Column(String)
    cover_id = Column(Integer, nullable=True)
    ebook_access = Column(String, nullable=True) # borrowable, printdisabled, public, no_ebook
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    prompt = relationship("Prompt", back_populates="submissions")
    votes = relationship("Vote", back_populates="submission")
    tags = relationship("Tag", secondary=submission_tags, backref="submissions")
    
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

class Favorite(Base):
    __tablename__ = "favorites"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, index=True)
    prompt_id = Column(Integer, ForeignKey("prompts.id"))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    prompt = relationship("Prompt", back_populates="favorites")

    __table_args__ = (
        UniqueConstraint('username', 'prompt_id', name='unique_user_favorite_prompt'),
    )

Base.metadata.create_all(bind=engine)

# --- App Setup ---
app = FastAPI(title="TheBestBookOn")

app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

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

# --- Auth ---
def get_current_user(request: Request):
    return request.session.get("user")

@app.get("/login", response_class=HTMLResponse)
def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
def login(request: Request, email: str = Form(...), password: str = Form(...)):
    try:
        # 1. Authenticate with Internet Archive
        # email might need URL encoding if it has spaces, but usually emails don't.
        # The user snippet suggested: email = email.replace(' ', '+')
        # We'll follow that just in case it's a username/screenname treated as email param.
        email_clean = email.replace(' ', '+')
        
        response = get_auth_config(email_clean, password)
        
        # 2. Resolve OpenLibrary Username
        s3_creds = response.get('s3')
        if not s3_creds:
             raise AuthenticationError("No S3 credentials returned.")

        r = requests.post(
            'https://openlibrary.org/account/login',
            headers={'Content-Type': 'application/json'},
            json=s3_creds
        )
        r.raise_for_status()
        
        # Extract username from session cookie as per snippet
        # Cookie format: "session=/people/USERNAME%2C..." or similar
        session_cookie = r.cookies.get('session')
        if not session_cookie:
             raise HTTPException(status_code=400, detail="Could not resolve OpenLibrary session.")
             
        # Parse: /people/USERNAME%2C...
        # split('/') -> ["", "people", "USERNAME%2C...", ...]
        parts = session_cookie.split('/')
        if len(parts) >= 3:
            username_part = parts[2]
            username = username_part.split('%2C')[0] # Split on comma encoding
        else:
             raise HTTPException(status_code=400, detail="Could not parse username from session.")
        
        # 3. Set Session
        request.session["user"] = username
        return RedirectResponse(url="/", status_code=303)
        
    except AuthenticationError:
        return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid credentials"})
    except Exception as e:
        print(f"Login error: {e}")
        return templates.TemplateResponse("login.html", {"request": request, "error": "Login failed. Please try again."})

@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=303)

# --- Routes ---

@app.get("/", response_class=HTMLResponse)
def read_root(request: Request, db: Session = Depends(get_db), user: str = Depends(get_current_user)):
    prompts = db.query(Prompt).order_by(Prompt.created_at.desc()).all()
    
    # Get user favorites
    user_fav_ids = set()
    if user:
        favs = db.query(Favorite).filter(Favorite.username == user).all()
        user_fav_ids = {f.prompt_id for f in favs}
    
    # Enrich prompts with stats
    prompts_data = []
    for p in prompts:
        subs = p.submissions
        subs.sort(key=lambda s: s.score, reverse=True)
        top_books = subs[:10]
        
        total_votes = sum([s.score for s in subs])
        # Count unique voters
        # This is a bit inefficient (n+1) but fine for "few hundred prompts" limit
        voter_ids = set()
        tag_counts = {}
        
        for s in subs:
            for v in s.votes:
                voter_ids.add(v.voter_username)
            # Aggregate tags
            for t in s.tags:
                tag_counts[t.name] = tag_counts.get(t.name, 0) + 1
                    
        total_voters = len(voter_ids)
        
        # Get top 5 tags
        top_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        display_tags = [t[0] for t in top_tags]
        
        prompts_data.append({
            "id": p.id,
            "title": p.title,
            "description": p.description,
            "creator_username": p.creator_username,
            "display_tags": display_tags,
            "top_books": top_books,
            "total_books": len(subs),
            "total_votes": total_votes,
            "total_voters": total_voters,
            "is_favorited": p.id in user_fav_ids
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
    
    # Check if user voted & Aggregate tags for display on detail page
    tag_counts = {}
    for sub in submissions:
        # Determine user's vote value (1, -1, or None)
        user_vote = next((v for v in sub.votes if v.voter_username == user), None)
        sub.user_vote_value = user_vote.value if user_vote else 0
        
        # Get the original vote comment (from the submitter)
        # We assume the submitter always votes 1 on creation, so find their vote
        submitter_vote = next((v for v in sub.votes if v.voter_username == sub.submitter_username), None)
        sub.comment = submitter_vote.comment if submitter_vote else None
        
        for t in sub.tags:
            tag_counts[t.name] = tag_counts.get(t.name, 0) + 1
    
    top_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:3]
    prompt.display_tags = [t[0] for t in top_tags]
    
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
    db: Session = Depends(get_db),
    user: str = Depends(get_current_user)
):
    new_prompt = Prompt(
        title=title,
        description=description,
        creator_username=user
    )
    db.add(new_prompt)
    db.commit()
    db.refresh(new_prompt)
    return RedirectResponse(url=f"/prompts/{new_prompt.id}", status_code=303)

@app.get("/api/search_books")
async def search_books(q: str):
    async with httpx.AsyncClient() as client:
        # Searching fields=key,title,author_name,cover_i,first_publish_year,edition_key,ebook_access
        url = f"https://openlibrary.org/search.json?q={q}&fields=key,title,author_name,cover_i,first_publish_year,edition_key,ebook_access&limit=10"
        resp = await client.get(url)
        data = resp.json()
        
        # Prioritize results
        def priority_score(doc):
            access = doc.get('ebook_access', 'no_ebook')
            if access in ['borrowable', 'public', 'printdisabled']:
                return 1
            return 0
            
        if 'docs' in data:
            # stable sort: priority first
            data['docs'].sort(key=priority_score, reverse=True)
            # trim to 5 after sorting
            data['docs'] = data['docs'][:5]
            
        return data

@app.post("/prompts/{prompt_id}/submit")
def submit_book(
    prompt_id: int,
    edition_key: str = Form(...),
    title: str = Form(...),
    cover_id: int = Form(None),
    ebook_access: str = Form(None),
    tags: str = Form(""), # Comma separated
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
            ebook_access=ebook_access,
            submitter_username=user
        )
        db.add(submission)
    
    # Process Tags
    if tags:
        tag_names = [t.strip() for t in tags.split(',') if t.strip()]
        for t_name in tag_names:
            # Check if tag exists
            tag_obj = db.query(Tag).filter(Tag.name == t_name).first()
            if not tag_obj:
                tag_obj = Tag(name=t_name)
                db.add(tag_obj)
                db.commit() # Commit to get ID
                
            if tag_obj not in submission.tags:
                submission.tags.append(tag_obj)
    
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

@app.get("/api/tags")
def search_tags(q: str = "", db: Session = Depends(get_db)):
    if not q:
        return []
    tags = db.query(Tag).filter(Tag.name.contains(q)).limit(10).all()
    return [t.name for t in tags]

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

@app.post("/api/prompts/{prompt_id}/toggle_favorite")
def toggle_favorite(
    prompt_id: int,
    db: Session = Depends(get_db),
    user: str = Depends(get_current_user)
):
    existing = db.query(Favorite).filter(
        Favorite.prompt_id == prompt_id,
        Favorite.username == user
    ).first()
    
    if existing:
        db.delete(existing)
        favorited = False
    else:
        fav = Favorite(prompt_id=prompt_id, username=user)
        db.add(fav)
        favorited = True
    
    db.commit()
    return {"favorited": favorited}

