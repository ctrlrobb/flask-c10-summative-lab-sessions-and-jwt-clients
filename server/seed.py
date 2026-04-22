from config import app, db, logger
from models import User, Note
from faker import Faker
import sys
 
fake = Faker()
 
def seed_database():
    """
    Seed the database with sample data for development and testing.
    
    Raises:
        Exception: If database operations fail
    """
    with app.app_context():
        try:
            logger.info("=" * 60)
            logger.info("Starting database seeding...")
            logger.info("=" * 60)
            
            # Delete existing data
            logger.info("Deleting old data...")
            deleted_notes = Note.query.delete()
            deleted_users = User.query.delete()
            db.session.commit()
            logger.info(f"Deleted {deleted_notes} notes and {deleted_users} users")
            
            # Create sample users and notes
            logger.info("Creating sample users and notes...")
            users_created = 0
            notes_created = 0
            
            test_credentials = []
            
            for i in range(3):
                # Generate unique username
                username = f"testuser_{i+1}_{fake.user_name()}"
                password = "password123"
                
                user = User(username=username)
                user.set_password(password)
                db.session.add(user)
                db.session.flush()  # Get user ID without committing
                
                users_created += 1
                test_credentials.append({
                    'username': username,
                    'password': password,
                    'user_id': user.id
                })
                
                logger.info(f"Created user {i+1}/3: {username}")
                
                # Create notes for this user
                for j in range(4):
                    title = fake.sentence(nb_words=4)
                    content = fake.paragraph(nb_sentences=3)
                    
                    note = Note(
                        title=title,
                        content=content,
                        user_id=user.id
                    )
                    db.session.add(note)
                    notes_created += 1
                
                logger.info(f"Created 4 notes for {username}")
            
            # Commit all changes
            db.session.commit()
            
            logger.info("=" * 60)
            logger.info(f"✓ Database seeding completed successfully!")
            logger.info(f"  - Users created: {users_created}")
            logger.info(f"  - Notes created: {notes_created}")
            logger.info("=" * 60)
            logger.info("\nTest Credentials:")
            logger.info("=" * 60)
            
            for cred in test_credentials:
                logger.info(f"Username: {cred['username']}")
                logger.info(f"Password: {cred['password']}")
                logger.info("-" * 60)
            
            logger.info("\nYou can now test the API with these credentials.")
            logger.info("Example login command:")
            logger.info(f"curl -X POST http://localhost:5555/login \\")
            logger.info(f"  -H 'Content-Type: application/json' \\")
            logger.info(f"  -d '{{\"username\": \"{test_credentials[0]['username']}\", \"password\": \"{test_credentials[0]['password']}\"}}' \\")
            logger.info(f"  -c cookies.txt")
            logger.info("=" * 60)
            
            return True
            
        except Exception as e:
            logger.error(f"Error seeding database: {str(e)}")
            db.session.rollback()
            return False
 
if __name__ == '__main__':
    try:
        success = seed_database()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"Fatal error during seeding: {str(e)}")
        sys.exit(1)
 






