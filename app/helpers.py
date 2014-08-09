from subprocess import check_output, CalledProcessError
from . import sentry
from itertools import izip_longest


def current_version():
    """
    Queries the CWD git repository to get the latest tag if available, otherwise falling back to the latest commit hash.

    If an exception is thrown it is handled by Sentry, and this method will simply return an empty string.

    :return: str
    """
    try:
        return check_output(['git', 'describe', '--always'])
    except CalledProcessError:
        sentry.captureException()
        return ""


def grouper(iterable, n, fillvalue=None):
    args = [iter(iterable)] * n
    return izip_longest(*args, fillvalue=fillvalue)
