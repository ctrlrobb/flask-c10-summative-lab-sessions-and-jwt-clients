from flask import session, request
from flask_restful import Resource
from config import db
from models import User, Note


def get_current_user():
    return User.query.get(session.get('user_id'))


class Signup(Resource):
    def post(self):
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '')

        if not username or not password:
            return {'errors': ['Username and password required']}, 422

        if User.query.filter_by(username=username).first():
            return {'errors': ['Username already taken']}, 422

        user = User(username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        session['user_id'] = user.id
        return user.to_dict(), 201


class Login(Resource):
    def post(self):
        data = request.get_json()
        user = User.query.filter_by(username=data.get('username')).first()

        if not user or not user.check_password(data.get('password', '')):
            return {'errors': ['Invalid username or password']}, 401

        session['user_id'] = user.id
        return user.to_dict(), 200


class Logout(Resource):
    def delete(self):
        if not get_current_user():
            return {'errors': ['Not logged in']}, 401
        session.pop('user_id', None)
        return {}, 204


class CheckSession(Resource):
    def get(self):
        user = get_current_user()
        if user:
            return user.to_dict(), 200
        return {'errors': ['Not logged in']}, 401


class NoteList(Resource):
    def get(self):
        user = get_current_user()
        if not user:
            return {'errors': ['Unauthorized']}, 401

        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 5, type=int)
        paginated = Note.query.filter_by(user_id=user.id).paginate(
            page=page, per_page=per_page, error_out=False
        )
        return {
            'notes': [n.to_dict() for n in paginated.items],
            'total': paginated.total,
            'pages': paginated.pages,
            'current_page': paginated.page
        }, 200

    def post(self):
        user = get_current_user()
        if not user:
            return {'errors': ['Unauthorized']}, 401

        data = request.get_json()
        title = data.get('title', '').strip()
        content = data.get('content', '').strip()

        if not title or not content:
            return {'errors': ['Title and content are required']}, 422

        note = Note(title=title, content=content, user_id=user.id)
        db.session.add(note)
        db.session.commit()
        return note.to_dict(), 201


class NoteDetail(Resource):
    def patch(self, id):
        user = get_current_user()
        if not user:
            return {'errors': ['Unauthorized']}, 401

        note = Note.query.get(id)
        if not note:
            return {'errors': ['Note not found']}, 404
        if note.user_id != user.id:
            return {'errors': ['Forbidden']}, 403

        data = request.get_json()
        if 'title' in data:
            note.title = data['title']
        if 'content' in data:
            note.content = data['content']

        db.session.commit()
        return note.to_dict(), 200

    def delete(self, id):
        user = get_current_user()
        if not user:
            return {'errors': ['Unauthorized']}, 401

        note = Note.query.get(id)
        if not note:
            return {'errors': ['Note not found']}, 404
        if note.user_id != user.id:
            return {'errors': ['Forbidden']}, 403

        db.session.delete(note)
        db.session.commit()
        return {}, 204