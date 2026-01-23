# TheBestBookOn.com

<p align="center">
  <img src="static/logo.png" alt="The Best Book On logo" width="400">
</p>

A community-curated platform for discovering the best books on any topic, powered by collective wisdom and Internet Archive integration.

## What is TheBestBookOn.com?

**TheBestBookOn** is a web application that helps people find the definitive books on any subject through community curation. Instead of algorithmic recommendations, we rely on thoughtful human judgment to surface books that truly matter.

### Philosophy

Book preference is a matter of taste, and many people share similar tastes. While one book may be perceived as better than another in several ways, it often makes more sense to compare books within specific contexts or criteria. TheBestBookOn creates curated "prompts" - topical questions like "Managing Complex Projects" or "Designing Effective Cities" - where the community can submit and vote on the books that best answer each question.

This project is part of the [Open Book Genome Project](https://bookgenomeproject.org), an initiative to create structured metadata about books that goes beyond traditional cataloging.

### Why TheBestBookOn?

- **Community-Driven Quality**: Leverages collective wisdom rather than algorithms
- **Rich Context**: Each book recommendation includes detailed justifications
- **Integration with Internet Archive**: Seamless authentication and access to ebook availability
- **Tag-Based Discovery**: Find books across related topics and genres
- **Transparent Voting**: See who voted for what and why

## Technologies

TheBestBookOn is built with:

- **Backend**: [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework with async support
- **Database**: SQLite with [SQLAlchemy](https://www.sqlalchemy.org/) ORM
- **Templates**: [Jinja2](https://jinja.palletsprojects.com/) for server-side rendering
- **Authentication**: Internet Archive OAuth integration
- **Book Data**: [OpenLibrary API](https://openlibrary.org/developers/api) for book metadata and covers
- **Session Management**: Starlette SessionMiddleware with secure cookie-based sessions

## Installation & Setup

### Prerequisites

- Python 3.7 or higher
- pip (Python package manager)
- Git

### 1. Clone the Repository

```bash
git clone https://github.com/Open-Book-Genome-Project/TheBestBookOn.com.git
cd TheBestBookOn.com
```

### 2. Set Up Python Virtual Environment (Recommended)

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On Linux/Mac:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install fastapi uvicorn sqlalchemy httpx requests python-dotenv jinja2 internetarchive
```

**Note**: For production use, consider creating a `requirements.txt` file with pinned versions for better reproducibility.

**Required Python packages:**
- `fastapi` - Web framework
- `uvicorn` - ASGI server for FastAPI
- `sqlalchemy` - Database ORM
- `httpx` - Async HTTP client
- `requests` - HTTP library
- `python-dotenv` - Environment variable management
- `jinja2` - Template engine
- `internetarchive` - Internet Archive authentication

### 4. Initialize the Database

The application comes with a pre-populated seed database (`thebestbookon_seed.db`) containing curated prompts and book recommendations.

**Option A: Use the Seed Database (Recommended)**

```bash
# Copy the seed database to create your working database
cp thebestbookon_seed.db thebestbookon.db
```

**Option B: Create a Fresh Database**

If you want to start from scratch:

```bash
# The database will be created automatically on first run
# To populate it with seed data:
python populate_db.py
```

**Option C: Patch/Update Existing Database**

To apply updates to an existing database:

```bash
python patch_db.py
```

### 5. Configure Environment

The application automatically generates a `.env` file with a secure `SECRET_KEY` on first run. No manual configuration is needed for basic usage.

**Optional**: If you want to customize settings, create a `.env` file:

```bash
SECRET_KEY=your-secret-key-here
```

Generate a secure secret key with Python:

```python
import secrets
print(secrets.token_urlsafe(32))
```

### 6. Run the Application

```bash
# Development mode with auto-reload
uvicorn main:app --reload --host 0.0.0.0 --port 8080

# Or production mode
uvicorn main:app --host 0.0.0.0 --port 8080
```

The application will be available at: **http://localhost:8080**

### 7. Login with Internet Archive

To submit books, vote, or create prompts, you'll need to log in with your Internet Archive credentials. If you don't have an account, create one at [archive.org/account/signup](https://archive.org/account/signup).

## Architecture Overview

### Application Structure

```
TheBestBookOn.com/
├── main.py                    # FastAPI application (routes, models, logic)
├── populate_db.py             # Database seed script with curated content
├── patch_db.py                # Database update/patch script
├── thebestbookon.db           # SQLite database (working copy)
├── thebestbookon_seed.db      # Pre-populated database template
├── .env                       # Environment variables (auto-generated)
├── templates/                 # Jinja2 HTML templates
│   ├── base.html              # Base template with navigation
│   ├── index.html             # Homepage (prompt list)
│   ├── prompt_detail.html     # Prompt page with book submissions
│   ├── user_profile.html      # User activity page
│   └── login.html             # Login page
└── static/                    # Static assets
    ├── style.css              # Application styles
    └── logo.png               # Logo image
```

### Database Schema

The application uses a relational database with the following core entities:

**Prompts**: Questions or topics for book recommendations
- Each prompt has a title, description, and creator
- Contains multiple book submissions
- Can be favorited by users

**Submissions**: Book recommendations submitted to prompts
- Linked to a specific prompt
- Contains OpenLibrary metadata (edition key, cover, ebook access)
- Can have multiple votes and tags

**Votes**: User votes on submissions (+1 or -1)
- Each user can vote once per submission
- Includes optional comment/justification
- Used to calculate submission scores

**Tags**: Categorization labels
- Many-to-many relationship with submissions
- Used for filtering and discovery

**Favorites**: User bookmarks for prompts
- Tracks which prompts a user has favorited

### Key Features

1. **Prompts**: Create topical questions that ask for the best books
2. **Book Submission**: Submit books from OpenLibrary with justifications
3. **Voting System**: Upvote (+1) or downvote (-1) submissions with comments
4. **Tag-Based Discovery**: Filter by topics like "Philosophy", "Biography", "Science"
5. **User Profiles**: View user activity (prompts created, books submitted, votes cast)
6. **Favorites**: Bookmark prompts of interest
7. **OpenLibrary Integration**: Automatic book metadata and cover images
8. **Internet Archive Auth**: Secure login using existing IA credentials

### API Endpoints

**Public Pages:**
- `GET /` - Homepage with prompt list
- `GET /prompts/{id}` - Prompt detail page
- `GET /users/{username}` - User profile page
- `GET /login` - Login page

**Authenticated Actions:**
- `POST /prompts` - Create new prompt
- `POST /prompts/{id}/submit` - Submit book to prompt
- `POST /vote` - Vote on submission
- `POST /api/prompts/{id}/toggle_favorite` - Favorite/unfavorite prompt

**AJAX APIs:**
- `GET /api/search_books?q=query` - Search OpenLibrary
- `GET /api/tags?q=query` - Autocomplete tag search
- `GET /api/prompts/{id}/voters` - Get prompt voters
- `GET /api/submissions/{id}/voters` - Get submission voters

**Admin Only:**
- `DELETE /api/prompts/{id}` - Delete prompt
- `DELETE /api/submissions/{id}` - Delete submission

## Development

### Running Tests

The project includes basic tests that verify core functionality:
- OpenLibrary search API integration
- Authentication requirements for API endpoints
- Production database protection (tests use temporary databases)

**Install test dependencies:**
```bash
pip install -r requirements.txt
```

**Run the test suite:**
```bash
# Run all tests
pytest test_main.py -v

# Run specific test classes
pytest test_main.py::TestOpenLibrarySearch -v
pytest test_main.py::TestAuthenticationRequired -v

# Run with coverage
pytest test_main.py --cov=main --cov-report=term-missing
```

**Important:** Tests never write to the production database (`thebestbookon.db`). Each test uses a temporary test database that is created and destroyed automatically.

### Database Management

**View database contents:**
```bash
sqlite3 thebestbookon.db
sqlite> .tables
sqlite> SELECT * FROM prompts;
sqlite> .quit
```

**Reset to seed data:**
```bash
rm thebestbookon.db
cp thebestbookon_seed.db thebestbookon.db
```

**Add new curated content:**
Edit `populate_db.py` or `patch_db.py` with new prompts and books, then run:
```bash
python populate_db.py  # Full repopulation
# or
python patch_db.py     # Targeted updates
```

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

### Areas for Contribution

- Add more curated prompts and book recommendations
- Improve UI/UX design
- Add automated testing
- Enhance search and filtering
- Add book recommendation algorithms
- Improve mobile responsiveness

## License

See the repository for license information.

## Related Projects

- [Open Book Genome Project](https://bookgenomeproject.org) - Parent project for structured book metadata
- [Internet Archive](https://archive.org) - Digital library and authentication provider
- [OpenLibrary](https://openlibrary.org) - Open book data and covers

## Support

For questions or issues, please open a GitHub issue or contact the Open Book Genome Project community.
