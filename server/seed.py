from config import app, db
from models import User, Note
from faker import Faker

fake = Faker()

with app.app_context():
    print('Deleting old data...')
    Note.query.delete()
    User.query.delete()
    db.session.commit()

    print('Creating users and notes...')
    for i in range(3):
        user = User(username=fake.unique.user_name())
        user.set_password('password123')
        db.session.add(user)
        db.session.flush()

        for j in range(4):
            note = Note(
                title=fake.sentence(nb_words=4),
                content=fake.paragraph(nb_sentences=2),
                user_id=user.id
            )
            db.session.add(note)

    db.session.commit()
    print('Done! Seeded 3 users with 4 notes each.')