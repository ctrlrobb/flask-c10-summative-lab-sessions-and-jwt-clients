from marshmallow import Schema, fields, validate, ValidationError
 
class UserSchema(Schema):
    """Schema for user registration and login validation."""
    
    username = fields.Str(
        required=True,
        validate=validate.And(
            validate.Length(min=3, max=80),
            validate.Regexp(
                r'^[a-zA-Z0-9_-]+$',
                error='Username can only contain letters, numbers, underscores, and hyphens'
            )
        ),
        error_messages={'required': 'Username is required'}
    )
    password = fields.Str(
        required=True,
        validate=validate.Length(min=6, max=200),
        error_messages={'required': 'Password is required'}
    )
 
class NoteSchema(Schema):
    """Schema for note creation and update validation."""
    
    title = fields.Str(
        required=True,
        validate=validate.And(
            validate.Length(min=1, max=100),
            validate.Regexp(
                r'\S',
                error='Title cannot be empty or whitespace only'
            )
        ),
        error_messages={'required': 'Title is required'}
    )
    content = fields.Str(
        required=True,
        validate=validate.And(
            validate.Length(min=1),
            validate.Regexp(
                r'\S',
                error='Content cannot be empty or whitespace only'
            )
        ),
        error_messages={'required': 'Content is required'}
    )
 
class NoteUpdateSchema(Schema):
    """Schema for partial note updates (both fields optional)."""
    
    title = fields.Str(
        validate=validate.Length(min=1, max=100),
        allow_none=True
    )
    content = fields.Str(
        validate=validate.Length(min=1),
        allow_none=True
    )
 
# Instantiate schemas for use throughout the application
user_schema = UserSchema()
note_schema = NoteSchema()
note_update_schema = NoteUpdateSchema()
 






