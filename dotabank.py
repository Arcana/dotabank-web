from app import app, login_manager
from models import AnonymousUser
import views

login_manager.anonymous_user = AnonymousUser


if __name__ == '__main__':
    app.run()
