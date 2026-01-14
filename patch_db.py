import requests
import time
from sqlalchemy.orm import Session
from main import SessionLocal, Prompt, Submission, Vote, Tag, Favorite

USER_ORACLE = "the_oracle"

PATCH_DATA = [
     {
        "prompt": "Managing Complex Projects",
        "query": "The Mythical Man-Month Frederick Brooks", 
        "target_title": "The Mythical Man-Month",
        "justification": "The foundational text of software engineering that applies to all complex systems. Brooks's Law—adding manpower to a late project makes it later—is a counter-intuitive truth that every manager must internalize. It captures the essence of communication overhead and the limits of parallelization.",
        "tags": ["Software Engineering", "Management", "Classics", "Systems Thinking"]
    },
    {
        "prompt": "Creating Public Good",
        "bad_title_fragment": "Summary of",
        "query": "Blueprint for Revolution Srdja Popovic",
        "target_title": "Blueprint for Revolution",
        "justification": "Popovic, a leader of the movement that toppled Milosevic, offers a handbook for non-violent resistance. He treats revolution as a design problem, showing how humor, branding, and low-risk actions can mobilize the public and undermine authoritarian pillars of support.",
        "tags": ["Activism", "Politics", "Strategy", "History"]
    },
    {
        "prompt": "Avoiding Climate Catastrophe",
        "bad_title_fragment": "Summary of",
        "query": "Under a White Sky Elizabeth Kolbert",
        "target_title": "Under a White Sky",
        "justification": "Kolbert explores the 'control of nature.' We have messed up the planet so badly that the only solution might be more intervention (geoengineering, gene drives). It is a report from the cutting edge of the Anthropocene, asking if we can solve problems created by our own ingenuity.",
        "tags": ["Science", "Environment", "Technology", "Journalism"]
    }
]

def get_openlibrary_data(query):
    # Same helper
    try:
        url = "https://openlibrary.org/search.json"
        params = {"q": query, "fields": "key,title,author_name,cover_i,first_publish_year,edition_key", "limit": 1}
        resp = requests.get(url, params=params)
        data = resp.json()
        if not data.get("docs"): return None
        doc = data["docs"][0]
        edition_keys = doc.get("edition_key", [])
        if not edition_keys: return None
        return {"edition_key": edition_keys[0], "title": doc.get("title"), "cover_id": doc.get("cover_i")}
    except: return None

def patch():
    db = SessionLocal()
    print("Patching data...")
    
    for item in PATCH_DATA:
        # 1. Find Prompt
        prompt = db.query(Prompt).filter(Prompt.title == item['prompt']).first()
        if not prompt:
            print(f"Prompt not found: {item['prompt']}")
            continue
            
        # 2. Remove bad submission if defined
        if "bad_title_fragment" in item:
            bad_subs = db.query(Submission).filter(
                Submission.prompt_id == prompt.id,
                Submission.title.contains(item['bad_title_fragment'])
            ).all()
            for sub in bad_subs:
                print(f"Removing bad submission: {sub.title}")
                db.delete(sub)
            db.commit()
            
        # 3. Add new submission
        # Check if already exists (the good one)
        # We don't have the edition key yet, so fetch first
        print(f"Fetching patch: {item['query']}")
        ol_data = get_openlibrary_data(item['query'])
        if not ol_data:
            print(f"Failed to find patch data for {item['query']}")
            continue
            
        existing = db.query(Submission).filter(
            Submission.prompt_id == prompt.id,
#            Submission.openlibrary_edition_key == ol_data['edition_key'] # strict check
             Submission.title == ol_data['title']       
        ).first()
        
        if existing:
            print(f"Submission already exists: {ol_data['title']}")
            continue
            
        submission = Submission(
            prompt_id=prompt.id,
            openlibrary_edition_key=ol_data['edition_key'],
            title=ol_data['title'],
            cover_id=ol_data['cover_id'],
            submitter_username=USER_ORACLE
        )
        db.add(submission)
        
         # Handle Tags
        for tag_name in item['tags']:
            tag_obj = db.query(Tag).filter(Tag.name == tag_name).first()
            if not tag_obj:
                tag_obj = Tag(name=tag_name)
                db.add(tag_obj)
                db.commit()
            
            if tag_obj not in submission.tags:
                submission.tags.append(tag_obj)
        
        db.commit()
        db.refresh(submission)
        
        # Vote
        vote = Vote(
            submission_id=submission.id,
            voter_username=USER_ORACLE,
            value=1,
            comment=item['justification']
        )
        db.add(vote)
        db.commit()
        print(f"Patched: {ol_data['title']}")

    db.close()

if __name__ == "__main__":
    patch()
