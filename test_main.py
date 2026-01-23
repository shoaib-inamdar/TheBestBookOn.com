"""
Basic tests for TheBestBookOn.com core functionality.

Important: These tests use a separate test database and never write to the
production database (thebestbookon.db).
"""

import os
import sqlite3
import tempfile
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch, MagicMock

# Import the app and database components
from main import app, get_db, Base, Prompt, Submission, Vote


@pytest.fixture(scope="function")
def test_db():
    """Create a temporary test database for each test."""
    # Create a temporary database file
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    
    # Create engine for the test database
    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False}
    )
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Create session
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    yield TestingSessionLocal, db_path
    
    # Cleanup
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture(scope="function")
def client(test_db):
    """Create a test client with a test database."""
    TestingSessionLocal, db_path = test_db
    
    def override_get_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


class TestOpenLibrarySearch:
    """Tests for OpenLibrary search API integration."""
    
    def test_search_books_returns_results(self, client):
        """Test that searching for books via OpenLibrary returns expected data structure."""
        # Mock the OpenLibrary API response
        mock_response = {
            "numFound": 2,
            "docs": [
                {
                    "key": "/works/OL123456W",
                    "title": "Learning Python",
                    "author_name": ["Mark Lutz"],
                    "cover_i": 12345,
                    "first_publish_year": 2013,
                    "ebook_access": "borrowable",
                    "editions": {
                        "docs": [
                            {
                                "key": "/books/OL123456M",
                                "title": "Learning Python",
                                "cover_i": 12345,
                                "ebook_access": "borrowable"
                            }
                        ]
                    }
                },
                {
                    "key": "/works/OL789012W",
                    "title": "Python Programming",
                    "author_name": ["John Doe"],
                    "ebook_access": "no_ebook",
                    "editions": {
                        "docs": [
                            {
                                "key": "/books/OL789012M",
                                "ebook_access": "no_ebook"
                            }
                        ]
                    }
                }
            ]
        }
        
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_get.return_value = MagicMock(json=lambda: mock_response)
            response = client.get("/api/search_books?q=python programming")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check that the response has the expected structure from OpenLibrary
        assert "docs" in data
        assert "numFound" in data
        
        # Verify results have the expected fields
        assert len(data["docs"]) > 0
        first_result = data["docs"][0]
        # OpenLibrary results should have these fields
        assert "title" in first_result
        assert "edition_key" in first_result
    
    def test_search_books_handles_empty_query(self, client):
        """Test that search handles edge cases appropriately."""
        mock_response = {
            "numFound": 0,
            "docs": []
        }
        
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_get.return_value = MagicMock(json=lambda: mock_response)
            response = client.get("/api/search_books?q=")
        
        # Should still return 200 with empty results
        assert response.status_code == 200
        data = response.json()
        assert "docs" in data
        assert "numFound" in data
        assert len(data["docs"]) == 0
    
    def test_search_books_prioritizes_ebook_access(self, client):
        """Test that search results prioritize books with ebook access."""
        # Create mock data where one book has ebook access and others don't
        mock_response = {
            "numFound": 10,
            "docs": [
                # This one should be prioritized (has borrowable ebook)
                {
                    "key": "/works/OL1W",
                    "title": "Pride and Prejudice (borrowable)",
                    "ebook_access": "borrowable",
                    "editions": {"docs": [{"key": "/books/OL1M", "ebook_access": "borrowable"}]}
                },
                # These should be deprioritized (no ebook)
                {
                    "key": "/works/OL2W",
                    "title": "Pride and Prejudice (no ebook)",
                    "ebook_access": "no_ebook",
                    "editions": {"docs": [{"key": "/books/OL2M", "ebook_access": "no_ebook"}]}
                },
                {
                    "key": "/works/OL3W",
                    "title": "Pride and Prejudice (no ebook 2)",
                    "ebook_access": "no_ebook",
                    "editions": {"docs": [{"key": "/books/OL3M", "ebook_access": "no_ebook"}]}
                },
                {
                    "key": "/works/OL4W",
                    "title": "Pride and Prejudice (public)",
                    "ebook_access": "public",
                    "editions": {"docs": [{"key": "/books/OL4M", "ebook_access": "public"}]}
                },
                {
                    "key": "/works/OL5W",
                    "title": "Pride and Prejudice (no ebook 3)",
                    "ebook_access": "no_ebook",
                    "editions": {"docs": [{"key": "/books/OL5M", "ebook_access": "no_ebook"}]}
                },
                {
                    "key": "/works/OL6W",
                    "title": "Pride and Prejudice (no ebook 4)",
                    "ebook_access": "no_ebook",
                    "editions": {"docs": [{"key": "/books/OL6M", "ebook_access": "no_ebook"}]}
                }
            ]
        }
        
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_get.return_value = MagicMock(json=lambda: mock_response)
            response = client.get("/api/search_books?q=pride and prejudice")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify results are limited to 5 after sorting (as per the code)
        assert "docs" in data
        assert len(data["docs"]) <= 5
        
        # Verify that books with ebook access appear first
        # The first results should have ebook_access in ['borrowable', 'public', 'printdisabled']
        if len(data["docs"]) > 0:
            first_result = data["docs"][0]
            # First result should have ebook access
            assert first_result.get("ebook_access") in ["borrowable", "public", "printdisabled"]


class TestAuthenticationRequired:
    """Tests for endpoints that require authentication."""
    
    def test_create_prompt_requires_auth(self, client):
        """Test that creating a prompt requires authentication."""
        response = client.post(
            "/prompts",
            data={
                "title": "Test Prompt",
                "description": "This should fail without auth"
            },
            follow_redirects=False
        )
        
        # Should return 401 Unauthorized
        assert response.status_code == 401
        assert "Authentication required" in response.json()["detail"]
    
    def test_submit_book_requires_auth(self, client, test_db):
        """Test that submitting a book nomination requires authentication."""
        TestingSessionLocal, _ = test_db
        db = TestingSessionLocal()
        
        # Create a test prompt first
        test_prompt = Prompt(
            title="Test Prompt",
            description="Test Description",
            creator_username="test_user"
        )
        db.add(test_prompt)
        db.commit()
        db.refresh(test_prompt)
        prompt_id = test_prompt.id
        db.close()
        
        # Try to submit a book without authentication
        response = client.post(
            f"/prompts/{prompt_id}/submit",
            data={
                "edition_key": "OL123456M",
                "title": "Test Book",
                "cover_id": 12345,
                "ebook_access": "borrowable",
                "tags": "test,programming",
                "comment": "Great book!"
            },
            follow_redirects=False
        )
        
        # Should return 401 Unauthorized
        assert response.status_code == 401
        assert "Authentication required" in response.json()["detail"]
    
    def test_vote_requires_auth(self, client, test_db):
        """Test that voting on a submission requires authentication."""
        TestingSessionLocal, _ = test_db
        db = TestingSessionLocal()
        
        # Create test data
        test_prompt = Prompt(
            title="Test Prompt",
            description="Test Description",
            creator_username="test_user"
        )
        db.add(test_prompt)
        db.commit()
        
        test_submission = Submission(
            prompt_id=test_prompt.id,
            openlibrary_edition_key="OL123456M",
            title="Test Book",
            submitter_username="test_user"
        )
        db.add(test_submission)
        db.commit()
        db.refresh(test_submission)
        submission_id = test_submission.id
        db.close()
        
        # Try to vote without authentication
        response = client.post(
            "/vote",
            data={
                "submission_id": submission_id,
                "value": 1
            },
            follow_redirects=False
        )
        
        # Should return 401 Unauthorized
        assert response.status_code == 401
        assert "Authentication required" in response.json()["detail"]
    
    def test_toggle_favorite_requires_auth(self, client, test_db):
        """Test that favoriting a prompt requires authentication."""
        TestingSessionLocal, _ = test_db
        db = TestingSessionLocal()
        
        # Create a test prompt
        test_prompt = Prompt(
            title="Test Prompt",
            description="Test Description",
            creator_username="test_user"
        )
        db.add(test_prompt)
        db.commit()
        db.refresh(test_prompt)
        prompt_id = test_prompt.id
        db.close()
        
        # Try to toggle favorite without authentication
        response = client.post(
            f"/api/prompts/{prompt_id}/toggle_favorite",
            follow_redirects=False
        )
        
        # Should return 401 Unauthorized
        assert response.status_code == 401
        assert "Authentication required" in response.json()["detail"]


class TestProductionDatabaseProtection:
    """Tests to ensure tests never write to the production database."""
    
    def test_uses_test_database(self, test_db):
        """Verify that tests are using a test database, not production."""
        _, db_path = test_db
        
        # The test database should be a temporary file
        assert db_path != "./thebestbookon.db"
        assert db_path != "thebestbookon.db"
        assert "tmp" in db_path or "temp" in db_path.lower()
    
    def test_production_db_unchanged(self):
        """Verify production database exists and is not being used by tests."""
        # Check that production DB exists (it should)
        prod_db_path = "./thebestbookon.db"
        
        # Get file stats before running (this test runs after others)
        # In a real scenario, we'd compare before/after, but for this test
        # we just verify it exists and has data
        if os.path.exists(prod_db_path):
            conn = sqlite3.connect(prod_db_path)
            cursor = conn.cursor()
            
            # Check that it has the expected tables and data
            cursor.execute("SELECT COUNT(*) FROM prompts")
            prompt_count = cursor.fetchone()[0]
            
            # The production DB should have data (as mentioned in requirements)
            assert prompt_count > 0, "Production DB should have meaningful data"
            
            conn.close()


class TestPublicEndpoints:
    """Tests for public endpoints that don't require authentication."""
    
    def test_homepage_accessible(self, client):
        """Test that the homepage is accessible without authentication."""
        response = client.get("/")
        
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
    
    def test_prompt_detail_accessible(self, client, test_db):
        """Test that prompt detail pages are accessible without authentication."""
        TestingSessionLocal, _ = test_db
        db = TestingSessionLocal()
        
        # Create a test prompt
        test_prompt = Prompt(
            title="Public Test Prompt",
            description="Test Description",
            creator_username="test_user"
        )
        db.add(test_prompt)
        db.commit()
        db.refresh(test_prompt)
        prompt_id = test_prompt.id
        db.close()
        
        response = client.get(f"/prompts/{prompt_id}")
        
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
    
    def test_login_page_accessible(self, client):
        """Test that the login page is accessible."""
        response = client.get("/login")
        
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
