# -*- coding: utf-8 -*-

from flask import current_app, Markup
from werkzeug import url_encode
from flask import json
from flask.ext.wtf._compat import text_type
JSONEncoder = json.JSONEncoder

try:
    from speaklater import _LazyString

    class _JSONEncoder(JSONEncoder):
        def default(self, o):
            if isinstance(o, _LazyString):
                return str(o)
            return JSONEncoder.default(self, o)
except:
    _JSONEncoder = JSONEncoder

RECAPTCHA_HTML = u'''
<script src="https://www.google.com/recaptcha/api.js?onload=recaptchaOnloadCallback&render=explicit" async defer></script>
<script type="text/javascript">
  var recaptchaOnloadCallback= function() {
    grecaptcha.render('recaptchaField', %(options)s);
  };
</script>
<div id="recaptchaField"></div>
'''

__all__ = ["RecaptchaWidget"]


class RecaptchaWidget(object):

    def recaptcha_html(self, query, options):
        html = current_app.config.get('RECAPTCHA_HTML', RECAPTCHA_HTML)
        return Markup(html % dict(
            options=json.dumps(options, cls=_JSONEncoder)
        ))

    def __call__(self, field, error=None, **kwargs):
        """Returns the recaptcha input HTML."""

        try:
            public_key = current_app.config['RECAPTCHA_PUBLIC_KEY']
        except KeyError:
            raise RuntimeError("RECAPTCHA_PUBLIC_KEY config not set")
        query_options = dict()

        if field.recaptcha_error is not None:
            query_options['error'] = text_type(field.recaptcha_error)

        query = url_encode(query_options)

        _ = field.gettext

        options = {
            'sitekey': public_key
        }

        options.update(current_app.config.get('RECAPTCHA_OPTIONS', {}))

        return self.recaptcha_html(query, options)
