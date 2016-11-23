import importlib

from six import next, iterkeys, itervalues


module = importlib.import_module('psqlparse.nodes')


def get_node_class(class_name):
    class_name = class_name.replace('_', '')
    return getattr(module, class_name, None)


def build_from_obj(obj):
    if isinstance(obj, list):
        return [build_from_obj(item) for item in obj]
    if not isinstance(obj, dict):
        return obj
    _class = get_node_class(next(iterkeys(obj)))
    return _class(next(itervalues(obj))) if _class else obj


def build_from_item(obj, key):
    return build_from_obj(obj[key]) if key in obj else None
