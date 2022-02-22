class DynamicSubclasser(type):
    """Return an instance of the class that uses this as its metaclass.
    This metaclass allows for a class to be instantiated with an argument,
    and assume that argument's class as its parent class.

    >>> class Foo(metaclass=DynamicSubclasser): pass
    >>> foo = Foo(5)
    >>> isinstance(foo, int)
    True
    """
    def __call__(cls, obj, *args, **kwargs):
        dynamic_parent_cls = type(obj)

        # Make this metaclass inherit from the dynamic_parent's metaclass.
        # This avoids metaclass conflicts.
        mcls = type(cls)
        cls.__class__ = type(mcls.__name__, (mcls, type(dynamic_parent_cls)), {})

        # Make a new class that inherits from the old and the object type.
        new_cls = type(cls.__name__, (cls, dynamic_parent_cls), {})

        # Create the instance and initialize it with the given object.
        # Sets obj in instance for immutables like `tuple`
        instance = new_cls.__new__(new_cls, obj, *args, **kwargs)
        # Sets obj in instance for mutables like `list`
        instance.__init__(obj, *args, **kwargs)

        return instance

class DeepCollection(metaclass=DynamicSubclasser):
    """A class intended to allow easy access to items of deep collections.

    >>> dc = DeepCollection({"a": ["i", "j", "k"]})
    >>> dc["a", 1]
    'j'
    """
    def __init__(self, obj, *args, original_path=None, **kwargs):
        # This often sets the original value for `self` for mutable types.
        # I.e. it gives a new list its content.
        # Immutables like tuples often already have the base class set via __new__.
        try:
            super().__init__(obj, *args, **kwargs)
        except TypeError:  # self is immutable - like a tuple
            pass

        self.original_path = original_path

    def __getitem__(self, key):
        try:
            iter(key)
        except TypeError:
            item = super().__getitem__(key)
            try:
                iter(item)
            except TypeError:
                return item
            return DeepCollection(item)

        current_step = key[0]
        next_key = key[1:]

        item = super().__getitem__(current_step)

        if next_key:
            return DeepCollection(item)[next_key]
        return item
