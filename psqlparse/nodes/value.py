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


class Float(Value):

    def __init__(self, obj):
        self.str = obj.get('str')
        self.fval = float(self.str)

    def __float__(self):
        return self.fval

    @property
    def val(self):
        return self.fval
