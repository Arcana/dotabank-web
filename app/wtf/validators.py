import requests

from flask import request, current_app
from wtforms import ValidationError

RECAPTCHA_VERIFY_SERVER = 'https://www.google.com/recaptcha/api/siteverify'

__all__ = ["Recaptcha"]


class Recaptcha(object):
    """Validates a ReCaptcha."""

    _error_codes = {
        'missing-input-secret': 'The private key for reCAPTCHA is missing',
        'invalid-input-secret': 'The private key for reCAPTCHA is invalid',
        'missing-input-response': 'The reCAPTCHA response is missing',
        'invalid-input-response': 'The reCAPTCHA response is invalid'
    }

    def __init__(self, message=u'Invalid word. Please try again.'):
        self.message = message

    def __call__(self, form, field):
        response = request.form.get('g-recaptcha-response', '')
        remote_ip = request.remote_addr

        if not response:
            raise ValidationError(field.gettext(self.message))

        if not self._validate_recaptcha(response, remote_ip):
            field.recaptcha_error = 'incorrect-captcha-sol'
            raise ValidationError(field.gettext(self.message))

    def _validate_recaptcha(self, response, remote_addr):
        """Performs the actual validation."""

        if current_app.testing:
            return True

        try:
            private_key = current_app.config['RECAPTCHA_PRIVATE_KEY']
        except KeyError:
            raise RuntimeError("No RECAPTCHA_PRIVATE_KEY config set")

        data = {
            'secret': private_key,
            'remoteip':   remote_addr,
            'response':   response
        }

        response = requests.get(RECAPTCHA_VERIFY_SERVER, params=data)

        if not response.ok:
            return False

        if response.json().get('success'):
            return True

        if response.json().get('error-codes'):
            for error in response.json().get('error-codes'):
                if error in self._error_codes:
                    raise RuntimeError(self._error_codes[error])

        return False
