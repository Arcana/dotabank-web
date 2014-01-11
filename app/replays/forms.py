from flask.ext.wtf import Form
from flask.ext.wtf.recaptcha import RecaptchaField

from wtforms import TextField


class DownloadForm(Form):
    recaptcha = RecaptchaField()


class SearchForm(Form):
    query = TextField("Query")
