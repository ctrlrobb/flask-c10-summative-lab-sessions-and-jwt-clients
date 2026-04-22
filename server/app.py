from config import app, db
from flask_restful import Api
from resources import Signup, Login, Logout, CheckSession, NoteList, NoteDetail
import logging.config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)

api = Api(app)

api.add_resource(Signup,       '/signup')
api.add_resource(Login,        '/login')
api.add_resource(Logout,       '/logout')
api.add_resource(CheckSession, '/check_session')
api.add_resource(NoteList,     '/notes')
api.add_resource(NoteDetail,   '/notes/<int:id>')

if __name__ == '__main__':
    app.run(port=5555, debug=True)