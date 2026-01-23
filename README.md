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

### Quick Start with Docker Compose (Recommended)

The easiest way to run TheBestBookOn is with Docker Compose, which includes the application server and nginx reverse proxy.

#### Prerequisites

- Docker and Docker Compose
- Git

#### Steps

1. **Clone the Repository**

```bash
git clone https://github.com/Open-Book-Genome-Project/TheBestBookOn.com.git
cd TheBestBookOn.com
```

2. **Start the Application**

```bash
docker compose up -d
```

The application will be available at: **http://localhost:8080**

The setup includes:
- FastAPI application server with pre-populated seed database
- Nginx reverse proxy for production-grade request handling
- Automatic secret key generation
- Persistent data storage

3. **Stop the Application**

```bash
docker compose down
```

4. **View Logs**

```bash
docker compose logs -f
```

### Manual Installation (Alternative)

If you prefer to run the application without Docker:

#### Prerequisites

- Python 3.7 or higher
- pip (Python package manager)
- Git

#### Steps

1. **Clone the Repository**

```bash
git clone https://github.com/Open-Book-Genome-Project/TheBestBookOn.com.git
cd TheBestBookOn.com
```

2. **Set Up Python Virtual Environment**

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On Linux/Mac:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
```

3. **Install Dependencies**

```bash
pip install -r requirements.txt
```

4. **Initialize the Database**

The application comes with a pre-populated seed database (`thebestbookon_seed.db`).

```bash
# Copy the seed database to create your working database
cp thebestbookon_seed.db thebestbookon.db
```

5. **Run the Application**

```bash
# Development mode with auto-reload
uvicorn main:app --reload --host 0.0.0.0 --port 8080

# Or production mode
uvicorn main:app --host 0.0.0.0 --port 8080
```

The application will be available at: **http://localhost:8080**

### Login with Internet Archive

To submit books, vote, or create prompts, you'll need to log in with your Internet Archive credentials. If you don't have an account, create one at [archive.org/account/signup](https://archive.org/account/signup).

## Architecture Overview

### Application Structure

```
TheBestBookOn.com/
├── main.py                    # FastAPI application (routes, models, logic)
├── populate_db.py             # Database seed script with curated content
├── patch_db.py                # Database update/patch script
├── requirements.txt           # Python dependencies with pinned versions
├── Dockerfile                 # Docker container configuration
├── compose.yml                # Docker Compose multi-service setup
├── nginx.conf                 # Nginx reverse proxy configuration
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

Currently, the application does not have a formal test suite. Contributions welcome!

### Database Management

**With Docker:**

```bash
# Access the database in the running container
docker compose exec app sqlite3 thebestbookon.db

# Reset to seed data (requires restart)
docker compose down -v
docker compose up -d
```

**Without Docker:**

```bash
# View database contents
sqlite3 thebestbookon.db
sqlite> .tables
sqlite> SELECT * FROM prompts;
sqlite> .quit

# Reset to seed data
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

### Docker Development

**Rebuild after code changes:**
```bash
docker compose down
docker compose build
docker compose up -d
```

**View application logs:**
```bash
docker compose logs -f app
```

**Access container shell:**
```bash
docker compose exec app /bin/bash
```

## Production Deployment

### Environment Variables

For production deployment, set a custom `SECRET_KEY` in your environment:

```bash
export SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
docker compose up -d
```

Or create a `.env` file:
```
SECRET_KEY=your-secure-secret-key-here
```

### Port Configuration

By default, the application is exposed on port 8080. To change this, modify the `compose.yml` file:

```yaml
services:
  nginx:
    ports:
      - "80:80"  # Change 8080 to 80 for production
```

### HTTPS/SSL

For production, consider adding SSL certificates:

1. Use a reverse proxy like Caddy or Traefik
2. Or modify the nginx configuration to include SSL certificates
3. Or deploy behind a load balancer with SSL termination

### Data Persistence

The Docker setup uses a named volume (`app-data`) to persist the database. To backup:

```bash
# Backup the database
docker compose exec app cp thebestbookon.db /tmp/backup.db
docker cp thebestbookon-app:/tmp/backup.db ./backup.db

# Restore from backup
docker cp ./backup.db thebestbookon-app:/app/thebestbookon.db
docker compose restart app
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
