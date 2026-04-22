import pytest
import json
from config import app, db
from models import User, Note
 
@pytest.fixture
def client():
    """
    Create a test client with isolated database.
    
    Yields:
        FlaskClient: Test client for making requests
    """
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.session.remove()
            db.drop_all()
 
@pytest.fixture
def auth_user(client):
    """
    Create and authenticate a test user.
    
    Args:
        client: Test client
        
    Returns:
        tuple: (client, user_data, response)
    """
    user_data = {'username': 'testuser', 'password': 'password123'}
    response = client.post('/signup', json=user_data)
    return client, user_data, response
 
# ===== Authentication Tests =====
 
class TestAuth:
    """Test suite for authentication endpoints."""
    
    def test_signup_success(self, client):
        """Test successful user registration."""
        response = client.post('/signup', json={
            'username': 'alice',
            'password': 'secure_password'
        })
        assert response.status_code == 201
        assert response.json['username'] == 'alice'
        assert 'id' in response.json
        assert 'created_at' in response.json
    
    def test_signup_missing_fields(self, client):
        """Test signup with missing required fields."""
        response = client.post('/signup', json={'username': 'alice'})
        assert response.status_code == 422
        assert 'errors' in response.json
    
    def test_signup_duplicate_username(self, client):
        """Test signup with duplicate username."""
        client.post('/signup', json={
            'username': 'alice',
            'password': 'pass123'
        })
        response = client.post('/signup', json={
            'username': 'alice',
            'password': 'different_pass'
        })
        assert response.status_code == 422
        assert 'already taken' in response.json['errors'][0]
    
    def test_signup_invalid_username_format(self, client):
        """Test signup with invalid username format."""
        response = client.post('/signup', json={
            'username': 'user@invalid!',
            'password': 'password123'
        })
        assert response.status_code == 422
        assert 'errors' in response.json
    
    def test_signup_short_password(self, client):
        """Test signup with password too short."""
        response = client.post('/signup', json={
            'username': 'alice',
            'password': 'short'
        })
        assert response.status_code == 422
    
    def test_login_success(self, auth_user):
        """Test successful login."""
        client, user_data, _ = auth_user
        # Clear session
        client.get('/logout')
        
        response = client.post('/login', json=user_data)
        assert response.status_code == 200
        assert response.json['username'] == user_data['username']
    
    def test_login_invalid_password(self, auth_user):
        """Test login with wrong password."""
        client, user_data, _ = auth_user
        client.get('/logout')
        
        response = client.post('/login', json={
            'username': user_data['username'],
            'password': 'wrong_password'
        })
        assert response.status_code == 401
        assert 'Invalid' in response.json['errors'][0]
    
    def test_login_nonexistent_user(self, client):
        """Test login with non-existent user."""
        response = client.post('/login', json={
            'username': 'nonexistent',
            'password': 'password123'
        })
        assert response.status_code == 401
    
    def test_check_session_authenticated(self, auth_user):
        """Test session check for authenticated user."""
        client, user_data, _ = auth_user
        
        response = client.get('/check_session')
        assert response.status_code == 200
        assert response.json['username'] == user_data['username']
    
    def test_check_session_unauthenticated(self, client):
        """Test session check for unauthenticated user."""
        response = client.get('/check_session')
        assert response.status_code == 401
        assert 'Not logged in' in response.json['errors'][0]
    
    def test_logout_success(self, auth_user):
        """Test successful logout."""
        client, _, _ = auth_user
        
        response = client.delete('/logout')
        assert response.status_code == 204
        
        # Verify session is cleared
        response = client.get('/check_session')
        assert response.status_code == 401
    
    def test_logout_unauthenticated(self, client):
        """Test logout when not authenticated."""
        response = client.delete('/logout')
        assert response.status_code == 401
 
# ===== Note CRUD Tests =====
 
class TestNotes:
    """Test suite for note endpoints."""
    
    def test_create_note_success(self, auth_user):
        """Test successful note creation."""
        client, _, _ = auth_user
        
        response = client.post('/notes', json={
            'title': 'Test Note',
            'content': 'This is a test note'
        })
        assert response.status_code == 201
        assert response.json['title'] == 'Test Note'
        assert response.json['content'] == 'This is a test note'
        assert 'id' in response.json
    
    def test_create_note_unauthenticated(self, client):
        """Test note creation without authentication."""
        response = client.post('/notes', json={
            'title': 'Test',
            'content': 'Content'
        })
        assert response.status_code == 401
    
    def test_create_note_missing_title(self, auth_user):
        """Test note creation with missing title."""
        client, _, _ = auth_user
        
        response = client.post('/notes', json={'content': 'Content'})
        assert response.status_code == 422
    
    def test_create_note_empty_content(self, auth_user):
        """Test note creation with empty content."""
        client, _, _ = auth_user
        
        response = client.post('/notes', json={
            'title': 'Title',
            'content': '   '
        })
        assert response.status_code == 422
    
    def test_get_notes_empty(self, auth_user):
        """Test getting notes when none exist."""
        client, _, _ = auth_user
        
        response = client.get('/notes')
        assert response.status_code == 200
        assert response.json['notes'] == []
        assert response.json['total'] == 0
    
    def test_get_notes_with_pagination(self, auth_user):
        """Test note retrieval with pagination."""
        client, _, _ = auth_user
        
        # Create 12 notes
        for i in range(12):
            client.post('/notes', json={
                'title': f'Note {i}',
                'content': f'Content {i}'
            })
        
        # Get first page (5 per page)
        response = client.get('/notes?page=1&per_page=5')
        assert response.status_code == 200
        assert len(response.json['notes']) == 5
        assert response.json['total'] == 12
        assert response.json['pages'] == 3
        assert response.json['current_page'] == 1
        
        # Get second page
        response = client.get('/notes?page=2&per_page=5')
        assert len(response.json['notes']) == 5
        assert response.json['current_page'] == 2
        
        # Get third page
        response = client.get('/notes?page=3&per_page=5')
        assert len(response.json['notes']) == 2
        assert response.json['current_page'] == 3
    
    def test_get_notes_unauthenticated(self, client):
        """Test note retrieval without authentication."""
        response = client.get('/notes')
        assert response.status_code == 401
    
    def test_update_note_success(self, auth_user):
        """Test successful note update."""
        client, _, _ = auth_user
        
        # Create note
        create_response = client.post('/notes', json={
            'title': 'Original Title',
            'content': 'Original Content'
        })
        note_id = create_response.json['id']
        
        # Update note
        update_response = client.patch(f'/notes/{note_id}', json={
            'title': 'Updated Title'
        })
        assert update_response.status_code == 200
        assert update_response.json['title'] == 'Updated Title'
        assert update_response.json['content'] == 'Original Content'
    
    def test_update_note_partial(self, auth_user):
        """Test partial note update."""
        client, _, _ = auth_user
        
        # Create note
        create_response = client.post('/notes', json={
            'title': 'Title',
            'content': 'Content'
        })
        note_id = create_response.json['id']
        
        # Update only content
        update_response = client.patch(f'/notes/{note_id}', json={
            'content': 'New Content'
        })
        assert update_response.status_code == 200
        assert update_response.json['title'] == 'Title'
        assert update_response.json['content'] == 'New Content'
    
    def test_update_nonexistent_note(self, auth_user):
        """Test updating non-existent note."""
        client, _, _ = auth_user
        
        response = client.patch('/notes/999', json={
            'title': 'New Title'
        })
        assert response.status_code == 404
    
    def test_delete_note_success(self, auth_user):
        """Test successful note deletion."""
        client, _, _ = auth_user
        
        # Create note
        create_response = client.post('/notes', json={
            'title': 'To Delete',
            'content': 'Delete me'
        })
        note_id = create_response.json['id']
        
        # Delete note
        delete_response = client.delete(f'/notes/{note_id}')
        assert delete_response.status_code == 204
        
        # Verify deletion
        get_response = client.get('/notes')
        assert len(get_response.json['notes']) == 0
    
    def test_delete_nonexistent_note(self, auth_user):
        """Test deleting non-existent note."""
        client, _, _ = auth_user
        
        response = client.delete('/notes/999')
        assert response.status_code == 404
 
# ===== Authorization Tests =====
 
class TestAuthorization:
    """Test suite for authorization controls."""
    
    def test_cannot_access_others_notes(self, client):
        """Test that users cannot access other users' notes."""
        # Create user 1
        client.post('/signup', json={
            'username': 'alice',
            'password': 'password123'
        })
        
        # Create note
        note_response = client.post('/notes', json={
            'title': "Alice's Secret",
            'content': 'Only for Alice'
        })
        note_id = note_response.json['id']
        
        # Logout
        client.delete('/logout')
        
        # Create user 2
        client.post('/signup', json={
            'username': 'bob',
            'password': 'password123'
        })
        
        # Try to access Alice's note
        response = client.patch(f'/notes/{note_id}', json={
            'title': 'Hacked!'
        })
        assert response.status_code == 403
        assert 'Forbidden' in response.json['errors'][0]
    
    def test_cannot_delete_others_notes(self, client):
        """Test that users cannot delete other users' notes."""
        # Create user 1 and note
        client.post('/signup', json={
            'username': 'alice',
            'password': 'password123'
        })
        note_response = client.post('/notes', json={
            'title': "Alice's Note",
            'content': 'Content'
        })
        note_id = note_response.json['id']
        
        # Logout and create user 2
        client.delete('/logout')
        client.post('/signup', json={
            'username': 'bob',
            'password': 'password123'
        })
        
        # Try to delete Alice's note
        response = client.delete(f'/notes/{note_id}')
        assert response.status_code == 403
    
    def test_users_only_see_own_notes(self, client):
        """Test that users only see their own notes."""
        # Create user 1 with notes
        client.post('/signup', json={
            'username': 'alice',
            'password': 'password123'
        })
        client.post('/notes', json={
            'title': "Alice's Note",
            'content': 'Content'
        })
        
        alice_notes = client.get('/notes').json
        assert alice_notes['total'] == 1
        
        # Logout and create user 2
        client.delete('/logout')
        client.post('/signup', json={
            'username': 'bob',
            'password': 'password123'
        })
        
        # Bob should see no notes
        bob_notes = client.get('/notes').json
        assert bob_notes['total'] == 0
 
# ===== Health Check Tests =====
 
class TestHealth:
    """Test suite for health check endpoints."""
    
    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get('/health')
        assert response.status_code == 200
        assert response.json['status'] == 'healthy'
        assert response.json['database'] == 'connected'
 
# ===== Edge Cases =====
 
class TestEdgeCases:
    """Test suite for edge cases and error conditions."""
    
    def test_invalid_json(self, auth_user):
        """Test request with invalid JSON."""
        client, _, _ = auth_user
        
        response = client.post(
            '/notes',
            data='invalid json',
            content_type='application/json'
        )
        assert response.status_code == 400
    
    def test_empty_json_body(self, auth_user):
        """Test request with empty JSON body."""
        client, _, _ = auth_user
        
        response = client.post('/notes', json={})
        assert response.status_code == 422
    
    def test_whitespace_only_title(self, auth_user):
        """Test note creation with whitespace-only title."""
        client, _, _ = auth_user
        
        response = client.post('/notes', json={
            'title': '   ',
            'content': 'Content'
        })
        assert response.status_code == 422
    
    def test_note_title_max_length(self, auth_user):
        """Test note creation with very long title."""
        client, _, _ = auth_user
        
        long_title = 'a' * 101
        response = client.post('/notes', json={
            'title': long_title,
            'content': 'Content'
        })
        assert response.status_code == 422
 
if __name__ == '__main__':
    pytest.main([__file__, '-v'])
 






