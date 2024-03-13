import sys
from functools import wraps


class IndexableProperty:
    def __init__(self, fget=None, fset=None, fdel=None, doc=None):
        self.fget = fget
        self.fset = fset
        self.fdel = fdel
        if doc is None and fget is not None:
            doc = fget.__doc__
        self.__doc__ = doc
        self.owner = None
        self.name = ''

        self.instance = None

    def __set_name__(self, owner, name):
        self.owner = owner
        self.name = name

    def __get__(self, instance, owner):
        if instance is None:
            return self
        else:
            self.instance = instance

        if self.fget is None:
            raise AttributeError(
                f'IndexableProperty {self.name!r} of {type(instance).__name__!r} object has no getter'
            )
        return self

    def __getitem__(self, item):
        if self.fget is None:
            raise AttributeError(
                f'IndexableProperty {self.name!r} of {type(self.instance).__name__!r} object has no getter'
            )
        return self.fget(self.instance, item)

    def __setitem__(self, key, value):
        if self.fset is None:
            raise AttributeError(
                f'IndexableProperty {self.name!r} of {type(self.instance).__name__!r} object has no setter'
            )
        self.fset(self.instance, key, value)

    def __delete__(self, obj):
        if self.fdel is None:
            raise AttributeError(
                f'IndexableProperty {self.name!r} of {type(obj).__name__!r} object has no deleter'
            )
        self.fdel(obj)

    def itemgetter(self, fget):
        prop = type(self)(fget, self.fset, self.fdel, self.__doc__)

        return prop

    def itemsetter(self, fset):
        prop = type(self)(self.fget, fset, self.fdel, self.__doc__)

        return prop

    def deleter(self, fdel):
        prop = type(self)(self.fget, self.fset, fdel, self.__doc__)
        prop.name = self.name
        return prop


class RequiresOptionalImport:
    def __init__(self, import_: str, from_: str = None, as_: str = None, msg: str = None, check_modules: bool = False):
        self._check_modules = check_modules

        if self._check_modules:
            module_name = import_ if from_ is None else from_
            all_modules = module_name.split('.')
            self._module_names_to_check = ['.'.join(all_modules[:i + 1]) for i in range(0, len(all_modules))]

        self._reference_name_to_check = import_.split('.')[0] if from_ is None else import_
        self._reference_name_to_check = as_ if as_ is not None else self._reference_name_to_check
        self._msg = f"Unresolved reference '{self._reference_name_to_check}'" if msg is None else msg

    def __call__(self, func):
        return self._func_wrapper(func)

    def _func_wrapper(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if self._check_modules:
                for module_name in self._module_names_to_check:
                    if module_name not in sys.modules:
                        raise ModuleNotFoundError(f"No module named '{module_name}'")

            if (self._reference_name_to_check is not None and
                    self._reference_name_to_check not in sys.modules[func.__module__].__dict__):
                raise RuntimeError(self._msg)

            return func(*args, **kwargs)

        return wrapper


def replace_none_in_slice(item: slice) -> slice:
    new_start = 0 if item.start is None else item.start
    new_stop = sys.maxsize if item.stop is None else item.stop
    new_step = 1 if item.step is None else item.step

    return slice(new_start, new_stop, new_step)


def subtract_offset_from_slice(item: slice, offset: int) -> slice:
    if offset == 0:
        return item

    if item.start > 0:
        new_start = item.start - offset if item.start - offset >= 0 else 0
    else:
        new_start = item.start
    if item.stop > 0:
        new_stop = item.stop - offset if item.stop - offset >= 0 else 0
    else:
        new_stop = item.stop

    return slice(new_start, new_stop, item.step)
