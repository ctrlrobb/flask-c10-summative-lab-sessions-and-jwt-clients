from flask import session, request
from flask_restful import Resource
from config import db, limiter, logger
from models import User, Note
from schemas import user_schema, note_schema, note_update_schema
from marshmallow import ValidationError
from decorators import validate_json, handle_errors, log_request
from datetime import datetime
 
def get_current_user():
    """
    Retrieve the currently authenticated user from session.
    
    Returns:
        User: User object if authenticated, None otherwise
    """
    user_id = session.get('user_id')
    if user_id:
        user = User.query.get(user_id)
        if user:
            logger.debug(f"Retrieved user {user.username} from session")
            return user
    return None
 
 
class Signup(Resource):
    """
    POST /signup
    Register a new user account.
    """
    
    @handle_errors
    @log_request
    @limiter.limit("5 per hour")
    def post(self):
        """
        Register a new user.
        
        Request JSON:
            - username (str): Unique username, 3-80 characters, alphanumeric, underscore, hyphen
            - password (str): Password, minimum 6 characters
            
        Returns:
            201: User successfully created
            400: Invalid JSON format
            422: Validation failed (missing fields, invalid format, username taken)
        """
        data = request.get_json()
        
        if not data:
            logger.warning(f"Signup attempt with empty body from {request.remote_addr}")
            return {'errors': ['Request body cannot be empty']}, 400
        
        # Validate input
        try:
            validated_data = user_schema.load(data)
        except ValidationError as err:
            logger.warning(f"Signup validation failed: {err.messages}")
            return {'errors': err.messages}, 422
        
        username = validated_data['username'].strip()
        password = validated_data['password']
        
        # Check if username already exists
        if User.query.filter_by(username=username).first():
            logger.warning(f"Signup failed: username '{username}' already taken")
            return {'errors': ['Username already taken']}, 422
        
        try:
            user = User(username=username)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            session['user_id'] = user.id
            session.permanent = True
            
            logger.info(f"New user registered: {username}")
            return user.to_dict(), 201
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating user: {str(e)}")
            return {'errors': ['Error creating user. Please try again.']}, 500
 
 
class Login(Resource):
    """
    POST /login
    Authenticate user and create session.
    """
    
    @handle_errors
    @log_request
    @limiter.limit("10 per minute")
    def post(self):
        """
        Authenticate user with username and password.
        
        Request JSON:
            - username (str): User's username
            - password (str): User's password
            
        Returns:
            200: User successfully authenticated
            400: Invalid JSON format
            401: Invalid username or password
        """
        data = request.get_json()
        
        if not data:
            logger.warning(f"Login attempt with empty body from {request.remote_addr}")
            return {'errors': ['Request body cannot be empty']}, 400
        
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        if not username or not password:
            logger.warning(f"Login attempt with missing credentials from {request.remote_addr}")
            return {'errors': ['Username and password required']}, 422
        
        user = User.query.filter_by(username=username).first()
        
        if not user or not user.check_password(password):
            logger.warning(f"Failed login attempt for username '{username}' from {request.remote_addr}")
            return {'errors': ['Invalid username or password']}, 401
        
        session['user_id'] = user.id
        session.permanent = True
        logger.info(f"User {username} logged in from {request.remote_addr}")
        return user.to_dict(), 200
 
 
class Logout(Resource):
    """
    DELETE /logout
    Clear user session.
    """
    
    @handle_errors
    @log_request
    def delete(self):
        """
        Logout current user by clearing session.
        
        Returns:
            204: User successfully logged out
            401: User not logged in
        """
        user = get_current_user()
        if not user:
            logger.warning(f"Logout attempt when not authenticated from {request.remote_addr}")
            return {'errors': ['Not logged in']}, 401
        
        username = user.username
        session.pop('user_id', None)
        logger.info(f"User {username} logged out from {request.remote_addr}")
        return {}, 204
 
 
class CheckSession(Resource):
    """
    GET /check_session
    Verify current user's authentication status.
    """
    
    @handle_errors
    @log_request
    def get(self):
        """
        Get current authenticated user.
        
        Returns:
            200: User data if authenticated
            401: No active session
        """
        user = get_current_user()
        if user:
            return user.to_dict(), 200
        
        logger.debug(f"Session check from unauthenticated request from {request.remote_addr}")
        return {'errors': ['Not logged in']}, 401
 
 
class NoteList(Resource):
    """
    GET /notes
    POST /notes
    List and create notes for authenticated user.
    """
    
    @handle_errors
    @log_request
    def get(self):
        """
        Retrieve paginated list of user's notes.
        
        Query Parameters:
            - page (int, default=1): Page number (1-indexed)
            - per_page (int, default=5): Items per page
            
        Returns:
            200: List of notes with pagination metadata
            401: User not authenticated
        """
        user = get_current_user()
        if not user:
            logger.warning(f"Note list access attempt when not authenticated from {request.remote_addr}")
            return {'errors': ['Unauthorized']}, 401
        
        try:
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 5, type=int)
            
            # Validate pagination parameters
            if page < 1:
                page = 1
            if per_page < 1 or per_page > 100:
                per_page = 5
            
            paginated = Note.query.filter_by(user_id=user.id).order_by(
                Note.created_at.desc()
            ).paginate(
                page=page, per_page=per_page, error_out=False
            )
            
            logger.info(f"User {user.username} retrieved notes - Page {page}, {per_page} per page")
            
            return {
                'notes': [n.to_dict() for n in paginated.items],
                'total': paginated.total,
                'pages': paginated.pages,
                'current_page': paginated.page
            }, 200
        except Exception as e:
            logger.error(f"Error retrieving notes: {str(e)}")
            return {'errors': ['Error retrieving notes']}, 500
    
    @handle_errors
    @log_request
    @limiter.limit("30 per minute")
    def post(self):
        """
        Create a new note for authenticated user.
        
        Request JSON:
            - title (str): Note title, 1-100 characters, non-empty
            - content (str): Note content, minimum 1 character, non-empty
            
        Returns:
            201: Note successfully created
            400: Invalid JSON format
            401: User not authenticated
            422: Validation failed
        """
        user = get_current_user()
        if not user:
            logger.warning(f"Note creation attempt when not authenticated from {request.remote_addr}")
            return {'errors': ['Unauthorized']}, 401
        
        data = request.get_json()
        
        if not data:
            logger.warning(f"Note creation with empty body from {request.remote_addr}")
            return {'errors': ['Request body cannot be empty']}, 400
        
        # Validate input
        try:
            validated_data = note_schema.load(data)
        except ValidationError as err:
            logger.warning(f"Note validation failed: {err.messages}")
            return {'errors': err.messages}, 422
        
        title = validated_data['title'].strip()
        content = validated_data['content'].strip()
        
        try:
            note = Note(title=title, content=content, user_id=user.id)
            db.session.add(note)
            db.session.commit()
            
            logger.info(f"User {user.username} created note: {title}")
            return note.to_dict(), 201
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating note: {str(e)}")
            return {'errors': ['Error creating note']}, 500
 
 
class NoteDetail(Resource):
    """
    PATCH /notes/<id>
    DELETE /notes/<id>
    Update and delete individual notes.
    """
    
    @handle_errors
    @log_request
    @limiter.limit("30 per minute")
    def patch(self, id):
        """
        Update a note (partial update).
        
        URL Parameters:
            - id (int): Note ID
            
        Request JSON:
            - title (str, optional): New title, 1-100 characters
            - content (str, optional): New content, minimum 1 character
            
        Returns:
            200: Note successfully updated
            400: Invalid JSON format
            401: User not authenticated
            403: User is not note owner
            404: Note not found
            422: Validation failed
        """
        user = get_current_user()
        if not user:
            logger.warning(f"Note update attempt when not authenticated from {request.remote_addr}")
            return {'errors': ['Unauthorized']}, 401
        
        note = Note.query.get(id)
        if not note:
            logger.warning(f"Update attempt on non-existent note {id}")
            return {'errors': ['Note not found']}, 404
        
        if note.user_id != user.id:
            logger.warning(f"User {user.username} attempted to update note {id} owned by user {note.user_id}")
            return {'errors': ['Forbidden']}, 403
        
        data = request.get_json()
        
        if not data:
            logger.warning(f"Note update with empty body from {request.remote_addr}")
            return {'errors': ['Request body cannot be empty']}, 400
        
        # Validate input (both fields optional for PATCH)
        try:
            validated_data = note_update_schema.load(data)
        except ValidationError as err:
            logger.warning(f"Note update validation failed: {err.messages}")
            return {'errors': err.messages}, 422
        
        try:
            if 'title' in validated_data and validated_data['title'] is not None:
                note.title = validated_data['title'].strip()
            
            if 'content' in validated_data and validated_data['content'] is not None:
                note.content = validated_data['content'].strip()
            
            note.updated_at = datetime.utcnow()
            db.session.commit()
            
            logger.info(f"User {user.username} updated note {id}")
            return note.to_dict(), 200
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating note: {str(e)}")
            return {'errors': ['Error updating note']}, 500
    
    @handle_errors
    @log_request
    @limiter.limit("30 per minute")
    def delete(self, id):
        """
        Delete a note.
        
        URL Parameters:
            - id (int): Note ID
            
        Returns:
            204: Note successfully deleted
            401: User not authenticated
            403: User is not note owner
            404: Note not found
        """
        user = get_current_user()
        if not user:
            logger.warning(f"Note deletion attempt when not authenticated from {request.remote_addr}")
            return {'errors': ['Unauthorized']}, 401
        
        note = Note.query.get(id)
        if not note:
            logger.warning(f"Deletion attempt on non-existent note {id}")
            return {'errors': ['Note not found']}, 404
        
        if note.user_id != user.id:
            logger.warning(f"User {user.username} attempted to delete note {id} owned by user {note.user_id}")
            return {'errors': ['Forbidden']}, 403
        
        try:
            db.session.delete(note)
            db.session.commit()
            
            logger.info(f"User {user.username} deleted note {id}")
            return {}, 204
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error deleting note: {str(e)}")
            return {'errors': ['Error deleting note']}, 500
 






