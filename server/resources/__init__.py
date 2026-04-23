from .auth import CheckSessionResource, LoginResource, LogoutResource, SignupResource
from .notes import NoteByIDResource, NotesResource


def register_resources(api):
    api.add_resource(SignupResource, "/signup")
    api.add_resource(LoginResource, "/login")
    api.add_resource(CheckSessionResource, "/check_session")
    api.add_resource(LogoutResource, "/logout")
    api.add_resource(NotesResource, "/notes")
    api.add_resource(NoteByIDResource, "/notes/<int:note_id>")
