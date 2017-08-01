import importlib

from six import next, iteritems


module = importlib.import_module('psqlparse.nodes')


def get_node_class(class_name):
    class_name = class_name.replace('_', '')
    return getattr(module, class_name, None)


def build_from_obj(obj, override_class_name=None):
    if isinstance(obj, list):
        return [build_from_obj(item, override_class_name) for item in obj]
    if not isinstance(obj, dict):
        return obj
    class_name, value = next(iteritems(obj))
    _class = get_node_class(override_class_name or class_name)
    return _class(value) if _class else obj


def build_from_item(obj, key, override_class_name=None):
    return build_from_obj(obj[key], override_class_name) if key in obj else None
