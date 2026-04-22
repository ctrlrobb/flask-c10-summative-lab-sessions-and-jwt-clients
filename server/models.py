from datetime import datetime
from config import db, bcrypt
 
class User(db.Model):
    """User model for authentication and note ownership."""
    
    __tablename__ = 'users'
 
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    notes = db.relationship('Note', back_populates='user', cascade='all, delete-orphan', lazy='dynamic')
 
    def set_password(self, password):
        """
        Hash and set user password using bcrypt.
        
        Args:
            password (str): Plain text password to hash
        """
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
        self.updated_at = datetime.utcnow()
 
    def check_password(self, password):
        """
        Verify a password against the stored hash.
        
        Args:
            password (str): Plain text password to verify
            
        Returns:
            bool: True if password matches, False otherwise
        """
        return bcrypt.check_password_hash(self.password_hash, password)
 
    def to_dict(self):
        """
        Serialize user to dictionary for JSON response.
        
        Returns:
            dict: User data without sensitive information
        """
        return {
            'id': self.id,
            'username': self.username,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
 
    def __repr__(self):
        return f'<User {self.username}>'
 
 
class Note(db.Model):
    """Note model for user-owned notes."""
    
    __tablename__ = 'notes'
 
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    user = db.relationship('User', back_populates='notes')
 
    def to_dict(self):
        """
        Serialize note to dictionary for JSON response.
        
        Returns:
            dict: Note data including metadata
        """
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'user_id': self.user_id,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
 
    def __repr__(self):
        return f'<Note {self.title}>'
 






