from functools import wraps
from flask import request
import logging
 
logger = logging.getLogger(__name__)
 
def validate_json(*expected_args):
    """
    Decorator to validate that request contains JSON with required fields.
    
    Args:
        *expected_args: Field names that must be present in JSON body
        
    Returns:
        function: Decorated function
        
    Example:
        @validate_json('title', 'content')
        def post(self):
            # request.get_json() is guaranteed to have title and content
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not request.is_json:
                logger.warning(f"Request missing JSON content-type from {request.remote_addr}")
                return {'errors': ['Request body must be JSON']}, 400
            
            data = request.get_json()
            if data is None:
                logger.warning(f"Empty request body from {request.remote_addr}")
                return {'errors': ['Request body cannot be empty']}, 400
            
            missing_fields = [field for field in expected_args if field not in data or data.get(field) is None]
            if missing_fields:
                logger.warning(f"Missing fields {missing_fields} in request from {request.remote_addr}")
                return {'errors': [f'Missing required fields: {", ".join(missing_fields)}']}, 422
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator
 
def handle_errors(f):
    """
    Decorator to catch and log unhandled exceptions.
    
    Returns:
        function: Decorated function with error handling
        
    Example:
        @handle_errors
        def post(self):
            # Any exception will be caught and logged
            pass
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except ValueError as e:
            logger.error(f"ValueError in {f.__name__}: {str(e)}")
            return {'errors': ['Invalid input data']}, 422
        except Exception as e:
            logger.error(f"Unhandled error in {f.__name__}: {str(e)}", exc_info=True)
            return {'errors': ['Internal server error']}, 500
    return decorated_function
 
def require_auth(f):
    """
    Decorator to require authentication for a resource.
    Should be used with get_current_user() to verify session.
    
    Returns:
        function: Decorated function
        
    Example:
        @require_auth
        def get(self):
            user = get_current_user()
            # user is guaranteed to exist
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from resources import get_current_user
        user = get_current_user()
        if not user:
            logger.warning(f"Unauthorized access attempt from {request.remote_addr}")
            return {'errors': ['Unauthorized']}, 401
        return f(*args, **kwargs)
    return decorated_function
 
def log_request(f):
    """
    Decorator to log incoming requests with metadata.
    
    Returns:
        function: Decorated function
        
    Example:
        @log_request
        def post(self):
            # Request will be automatically logged
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        logger.info(
            f"{request.method} {request.path} from {request.remote_addr} - "
            f"User-Agent: {request.headers.get('User-Agent', 'Unknown')}"
        )
        return f(*args, **kwargs)
    return decorated_function
 






