from flask.ext.wtf import Form
from app.wtf.fields import RecaptchaField
from wtforms.validators import Length

from wtforms import TextField


class DownloadForm(Form):
    recaptcha = RecaptchaField()


class SearchForm(Form):
    query = TextField("Query")


class AliasForm(Form):
    alias = TextField("Alias",
                      validators=[Length(max=96)],
                      description="Set a custom alias for this replay.")

    def __init__(self, replay_alias, *args, **kwargs):
        self.replay_alias = replay_alias
        kwargs['obj'] = self.replay_alias
        super(AliasForm, self).__init__(*args, **kwargs)
