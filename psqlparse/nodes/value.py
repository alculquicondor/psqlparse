import abc


class Value(object):
    __metaclass__ = abc.ABCMeta

    def __str__(self):
        return str(self.val)

    @abc.abstractproperty
    def val(self):
        pass


class Integer(Value):

    def __init__(self, obj):
        self.ival = obj.get('ival')

    def __int__(self):
        return self.ival

    @property
    def val(self):
        return self.ival


class String(Value):

    def __init__(self, obj):
        self.str = obj.get('str')

    @property
    def val(self):
        return self.str


class Literal(String):
    "A literal symbol, used for example for expression's operators."


class Name(String):
    "A column name, that could need to be double quoted in its textual representation."

    @classmethod
    def from_string(cls, str):
        if str is None:
            return None
        return cls(dict(str=str))

    def __str__(self):
        v = self.str
        if not v.islower():
            v = '"%s"' % v
        return v


class Float(Value):

    def __init__(self, obj):
        self.str = obj.get('str')
        self.fval = float(self.str)

    def __float__(self):
        return self.fval

    @property
    def val(self):
        return self.fval
