import six


@six.python_2_unicode_compatible
class PSqlParseError(Exception):

    def __init__(self, message, lineno, cursorpos):
        self.message = message
        self.lineno = lineno
        self.cursorpos = cursorpos

    def __str__(self):
        return self.message
