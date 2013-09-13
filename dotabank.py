from app import app, login_manager
from models import AnonymousUser

# Have the views' code get a ran through - they register themselves, hence why no actual importing.
from admin import admin
admin.init_app(app)

import views

# Register our anonymous user object, for our custom methods that flask.ext.login.AnonymousUserMixin doesn't have.
login_manager.anonymous_user = AnonymousUser

# Debug environment
if app.debug:
    from flask.ext.debugtoolbar import DebugToolbarExtension
    toolbar = DebugToolbarExtension(app)

# Production environment code
else:
    import logging
    from logging.handlers import SMTPHandler
    credentials = None
    if app.config["MAIL_USERNAME"] or app.config["MAIL_PASSWORD"]:
        credentials = (app.config["MAIL_USERNAME"], app.config["MAIL_PASSWORD"])
    mail_handler = SMTPHandler((app.config["MAIL_SERVER"], app.config["MAIL_PORT"]), 'no-reply@' + app.config["MAIL_SERVER"], app.config["ADMINS"], 'dotabank failure', credentials)
    mail_handler.setLevel(logging.ERROR)
    app.logger.addHandler(mail_handler)


if __name__ == '__main__':
    app.run()
