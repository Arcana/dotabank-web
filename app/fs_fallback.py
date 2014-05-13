__author__ = 'rjackson'
from functools import wraps
from flask import current_app
import os
import json
# For temporary schema object store
import cPickle as pickle
from time import time


def fs_fallback(func):
    """ File-system fallback for external data dependencies.  Will read from filesystem if the external data provided is
    trash.  Will write to filesystem if the external data differs from what we already have stored (archiving the
    previous data) """

    @wraps(func)
    def inner(*args, **kwargs):

        # Get data
        data = func(*args, **kwargs)

        # Generate path for where this data's filesystem fallback should be stored.
        fallback_filepath = os.path.join(
            current_app.config['APP_DIR'],
            'fallback_data',
            func.__name__ + '.json'
        )

        # If data is shit, try get from FS
        if data == {}:
            # If we have a file, return the data stored in the file.
            if os.path.exists(fallback_filepath):
                with open(fallback_filepath, 'r') as f:
                    return json.loads(f.read())
            # Otherwise return the (trash) data from the function
            else:
                return data

        # If we have good data, evaluate if we need to write it to file.
        else:
            save_to_file = True

            # If we have a previous file, compare the data stored to the live data we have.
            if os.path.exists(fallback_filepath):
                with open(fallback_filepath, 'r') as f:
                    # The data on file is the same as the new data, we don't need to write to FS.
                    if f.read() == json.dumps(data):
                        save_to_file = False
                    # The data difers, we need to archive the old data. New data will be written because `save_to_file`
                    # will be True already.
                    else:
                        os.rename(fallback_filepath, fallback_filepath + '_' + repr(time()))

            # Writing to file if we have new data.
            if save_to_file:
                with open(fallback_filepath, 'w') as f:
                        f.write(json.dumps(data))

            # Give data back to caller.
            return data

    return inner
