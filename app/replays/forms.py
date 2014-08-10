from flask.ext.wtf import Form
from flask.ext.wtf.recaptcha import RecaptchaField
from wtforms.validators import Length

from wtforms import StringField
from wtforms.widgets import Input


class SearchInput(Input):
    """
    Render a single-line search input.
    """
    input_type = 'search'


class DownloadForm(Form):
    recaptcha = RecaptchaField()


class SearchForm(Form):
    query = StringField("Query", widget=SearchInput())


class AliasForm(Form):
    alias = StringField("Alias",
                        validators=[Length(max=96)],
                        description="Set a custom alias for this replay.")

    def __init__(self, replay_alias, *args, **kwargs):
        self.replay_alias = replay_alias
        kwargs['obj'] = self.replay_alias
        super(AliasForm, self).__init__(*args, **kwargs)
