from flask.ext.wtf import Form
from flask.ext.wtf.recaptcha import RecaptchaField


class DownloadForm(Form):
    recaptcha = RecaptchaField()
