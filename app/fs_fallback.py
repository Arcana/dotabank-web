__author__ = 'rjackson'
from functools import wraps
from flask import current_app
import os
import json
from time import time


def fs_fallback(func):
    @wraps(func)
    def inner(*args, **kwargs):
        # Get dater
        data = func(*args, **kwargs)
        fallback_filepath = os.path.join(
            current_app.config['APP_DIR'],
            'fallback_data',
            func.__name__ + '.json'
        )

        # If data is shit, try get from FS
        if data == {}:
            if os.path.exists(fallback_filepath):
                # Get from fallback file
                with open(fallback_filepath, 'r') as f:
                    return json.loads(f.read())
            else:
                # Return original data
                return data
        # Save good data back to filesytem
        else:
            save_to_file = True

            # If previous file exists
            if os.path.exists(fallback_filepath):

                # Overwrite with new data if file contents differ
                with open(fallback_filepath, 'r') as f:
                    if f.read() == json.dumps(data):
                        # Data on file is same as data we have stored.
                        save_to_file = False
                    else:
                        # Backup old data
                        os.rename(fallback_filepath, fallback_filepath + '_' + repr(time()))

            # This will be true unless the file already exists with the same data stored
            if save_to_file:
                with open(fallback_filepath, 'w') as f:
                        f.write(json.dumps(data))

            # Give data back to caller.
            return data

    return inner
