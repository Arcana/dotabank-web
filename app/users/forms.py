from flask.ext.wtf import Form
from flask.ext.login import current_user

from wtforms import TextField, BooleanField
from wtforms.validators import Required, Email, Optional, ValidationError

from app.users.models import User


class SettingsForm(Form):
    name = TextField("Display name", validators=[Required("You must provide a display name.")])
    email = TextField("E-mail address",
                      validators=[Optional(), Email()],
                      description="Used to notify you when your matches have been parsed.")
    show_ads = BooleanField("Show ads", description="Uncheck to hide advertisements on Dotabank.")

    def validate_name(self, field):
        user = User.query.filter_by(name=field.data).first()
        if user and user.id != current_user.id:
            raise ValidationError("This username is taken")

    def __init__(self, user, *args, **kwargs):
        self.user = user
        kwargs['obj'] = self.user
        super(SettingsForm, self).__init__(*args, **kwargs)
