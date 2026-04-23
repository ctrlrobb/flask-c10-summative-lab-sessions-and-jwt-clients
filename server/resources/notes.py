from flask import request
from flask_restful import Resource

try:
    from ..models import Note, db
except ImportError:
    from models import Note, db

from .helpers import error_response, login_required


class NotesResource(Resource):
    method_decorators = [login_required]

    def get(self, current_user=None):
        page = request.args.get("page", default=1, type=int)
        per_page = request.args.get("per_page", default=10, type=int)
        page = max(page, 1)
        per_page = min(max(per_page, 1), 25)

        pagination = (
            Note.query.filter_by(user_id=current_user.id)
            .order_by(Note.updated_at.desc(), Note.id.desc())
            .paginate(page=page, per_page=per_page, error_out=False)
        )

        return {
            "data": [note.to_dict() for note in pagination.items],
            "pagination": {
                "page": pagination.page,
                "per_page": pagination.per_page,
                "total": pagination.total,
                "pages": pagination.pages,
                "has_next": pagination.has_next,
                "has_prev": pagination.has_prev,
            },
        }, 200

    def post(self, current_user=None):
        data = request.get_json() or {}

        try:
            note = Note(
                title=data.get("title"),
                content=data.get("content"),
                category=data.get("category", "general"),
                user_id=current_user.id,
            )
            db.session.add(note)
            db.session.commit()
        except ValueError as exc:
            db.session.rollback()
            return error_response(str(exc), 422)

        return note.to_dict(), 201


class NoteByIDResource(Resource):
    method_decorators = [login_required]

    def get_note_for_user(self, note_id, current_user):
        return Note.query.filter_by(id=note_id, user_id=current_user.id).first()

    def get(self, note_id, current_user=None):
        note = self.get_note_for_user(note_id, current_user)
        if note is None:
            return error_response("Note not found.", 404)
        return note.to_dict(), 200

    def patch(self, note_id, current_user=None):
        note = self.get_note_for_user(note_id, current_user)
        if note is None:
            return error_response("Note not found.", 404)

        data = request.get_json() or {}
        try:
            for field in ("title", "content", "category"):
                if field in data:
                    setattr(note, field, data[field])
            db.session.commit()
        except ValueError as exc:
            db.session.rollback()
            return error_response(str(exc), 422)

        return note.to_dict(), 200

    def delete(self, note_id, current_user=None):
        note = self.get_note_for_user(note_id, current_user)
        if note is None:
            return error_response("Note not found.", 404)

        db.session.delete(note)
        db.session.commit()
        return {}, 200
