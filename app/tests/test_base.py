import os
import sys
sys.path.append(os.path.join(os.getcwd(), '..'))

from app import app, db
import unittest
import tempfile


class DotabankTestCase(unittest.TestCase):

    ctx = None

    def setUp(self):
        self.db_fd, app.config['DATABASE'] = tempfile.mkstemp()

        # Turn on testing mode to surpress exception handling
        app.config['TESTING'] = True

        # Disable caches
        app.config['CACHE_MEMCACHED']['CACHE_TYPE'] = "null"
        app.config['CACHE_FS']['CACHE_TYPE'] = "null"

        # Use test request context
        self.ctx = app.test_request_context()
        self.ctx.push()

        self.app = app.test_client()
        db.create_all()

    def tearDown(self):
        self.ctx.pop()
        os.close(self.db_fd)
        os.unlink(app.config['DATABASE'])

if __name__ == '__main__':
    unittest.main()
