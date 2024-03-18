import sys
from functools import wraps


class IndexableProperty:
    """
    An instance property which can be accessed and modified by pythons __getitem__ and
    __setitem__ functions. Meant to be used as decorator function.
    Implements similar interface as pythons property inbuilt function except that getter function is
    called itemgetter and setter function is called itemsetter.
    See pythons property inbuilt function for more information.
    """

    def __init__(
            self,
            fget: callable = None,
            fset: callable = None,
            fdel: callable = None,
            pdel: callable = None,
            doc: str = None
    ):
        """
        Returns an indexable property attribute.
        The advantage compared to property is, that an indexable property does not provide direct access
        to an underlying attribute and therefore favours the enclosure principle to produce cleaner code.
        E.g. if the underlying data structure is a list, you do not have access to the list object but
        instead access to the values of the list.

        :param fget: is a function for accessing attribute value(s). It's parameters have to be as __getitem__
        function.
        :param fset: is a function for setting attribute value(s). It's parameters have to be as __setitem__
        function.
        :param pdel: is a function for deleting attribute value(s). It's parameters have to be as __delitem__
        function.
        :param fdel: is a function for deleting the attribute.
        :param doc: creates a docstring for the attribute.
        """
        self.fget: callable = fget
        self.fset: callable = fset
        self.fdel: callable = fdel
        self.pdel: callable = pdel
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
                f'IndexableProperty {self.name!r} of {type(self.instance).__name__!r} object has no item getter'
            )
        return self.fget(self.instance, item)

    def __setitem__(self, key, value):
        if self.fset is None:
            raise AttributeError(
                f'IndexableProperty {self.name!r} of {type(self.instance).__name__!r} object has no item setter'
            )
        self.fset(self.instance, key, value)

    def __delitem__(self, key):
        if self.fdel is None:
            raise AttributeError(
                f'IndexableProperty {self.name!r} of {type(self.instance).__name__!r} object has no item deleter'
            )
        self.fdel(self.instance, key)

    def __delete__(self, obj):
        if self.pdel is None:
            raise AttributeError(
                f'IndexableProperty {self.name!r} of {type(obj).__name__!r} object has no deleter'
            )
        self.pdel(obj)

    def itemgetter(self, fget: callable):
        """
        Defines the __getitem__ function for this indexable property.
        :param fget: A function that corresponds with the __getitem__ parameter list.
        :return: The indexable property.
        """
        prop = type(self)(fget, self.fset, self.fdel, self.pdel, self.__doc__)

        return prop

    def itemsetter(self, fset: callable):
        """
        Defines the __setitem__ function for this indexable property.
        :param fset: A function that corresponds with the __setitem__ parameter list.
        :return: The indexable property.
        """
        prop = type(self)(self.fget, fset, self.fdel, self.pdel, self.__doc__)

        return prop

    def itemdeleter(self, fdel: callable):
        """
        Defines the __delitem__ function for this indexable property.
        :param fdel: A function that corresponds with the __delitem__ parameter list.
        :return: The indexable property.
        """
        prop = type(self)(self.fget, self.fset, fdel, self.pdel, self.__doc__)

        return prop

    def deleter(self, pdel: callable):
        """
        Defines the __del__ function for this indexable property.
        :param pdel: A function that corresponds with the __del__ parameter list.
        :return: The indexable property.
        """
        prop = type(self)(self.fget, self.fset, self.fdel, pdel, self.__doc__)
        prop.name = self.name
        return prop


class RequiresOptionalImport:
    """
    A decorator class that checks during runtime if an optional import has been imported before running
    the decorated code section.
    """

    def __init__(self, import_: str, from_: str = None, as_: str = None, msg: str = None, check_modules: bool = False):
        """
        Creates a new check for the required optional import during runtime.
        Raises an Error if the specified requirement is not imported when calling the decorated code.

        E.g. if you have an optional import in a try-catch block like:

        import A from b.c as D

        you can decorate a function, class or method as followed:

        @RequiresOptionalImport(import_='A', from_='b.c', as_='D')

        :param import_: The import part of the complete import statement within the document.
        :param from_: The from part of the complete import statement within the document.
        :param as_: The as part of the complete import statement within the document.
        :param msg: The error message to raise.
        :param check_modules: If true also checks if the modules are imported.
        """
        self._check_modules = check_modules

        if self._check_modules:
            module_name = import_ if from_ is None else from_
            all_modules = module_name.split('.')
            self._module_names_to_check = ['.'.join(all_modules[:i + 1]) for i in range(0, len(all_modules))]

        self._reference_name_to_check = import_.split('.')[0] if from_ is None else import_
        self._reference_name_to_check = as_ if as_ is not None else self._reference_name_to_check
        self._msg = f"Unresolved reference '{self._reference_name_to_check}'" if msg is None else msg

    def __call__(self, func):
        """
        :return: Returns a wrapper for a given function.
        """
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
    """
    Replaces None values in a slice object with default values.
    The default start value is 0, the default stop value is sys.maxsize and the default step value is 1.
    :param item: A slice object.
    :return: A new slice object where None values are replaced by the default values described above.
    """
    new_start = 0 if item.start is None else item.start
    new_stop = sys.maxsize if item.stop is None else item.stop
    new_step = 1 if item.step is None else item.step

    return slice(new_start, new_stop, new_step)


def subtract_offset_from_slice(item: slice, offset: int) -> slice:
    """
    Correctly subtracts an offset from a slice object.
    Note that subtracting a negative offset to a negative start or stop value where the difference exceeds the
    negative number space results in sys.maxsize (start: -1 - offset: -5 => new_start: sys.maxsize).

    E.g. if you have a slice(2, 10, 1) object, and you want to subtract the offset value 5 you get
    a slice(0, 5, 1) object.

    :param item: A slice object.
    :param offset: The offset to subtract.
    :return: A new slice object where the start and stop have been subtracted by offset.
    """
    if offset == 0:
        return item

    if item.start > 0:
        new_start = max(0, item.start - offset)
    else:
        new_start = item.start - offset if item.start - offset < 0 else sys.maxsize
    if item.stop > 0:
        new_stop = max(0, item.stop - offset)
    else:
        new_stop = item.stop - offset if item.stop - offset < 0 else sys.maxsize

    return slice(new_start, new_stop, item.step)


def add_offset_to_slice(item: slice, offset: int) -> slice:
    """
    Correctly adds an offset to a slice object.
    Note that adding a positive offset to a negative start or stop value where the difference exceeds the
    negative number space results in sys.maxsize (start: -1 + offset: 5 => new_start: sys.maxsize).

    E.g. if you have a slice(2, 10, 1) object, and you want to add the offset value 5 you get
    a slice(7, 15, 1) object.

    :param item: A slice object.
    :param offset: The offset to add.
    :return: A new slice object where offset has been added to start and stop.
    """
    return subtract_offset_from_slice(item=item, offset=-offset)
