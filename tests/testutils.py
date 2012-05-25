from multiprocessing import Event
from functional import curry


@curry
def debug_print(prefix, data, callback=None):
    print(str(prefix) + str(data))
    if callback: callback(data)

@curry
def x_eq_y(x, y):
    """function for callback to test assertion.
    If following expression call function f asynchronously
    and when f is finished, call callback with argument f returns, then
    it is useful to use functions which takes more arguments with
    @curry decorator

        do_async(f, callback=x_eq_y(10))

    equals to synchronized expression:

        x_eq_y(10)( f() )

    which is the same as

        x_eq_y(10, f())

    """
    assert x == y

@curry
def x_is_y(x, y):
    """analogously to x_eq_y
    read help from function x_eq_y for more information
    """
    assert x is y



class NumDict(dict):
    def __getitem__(self, key):
        return self.get(key, 0)


def fake_function(*args, **kwargs):
    pass


class FakeCls(object):
    """Fake class  which accepts every field, and returns <ret_val>, which
    is `fake function` as default"""
    def __init__(self, ret_val=fake_function):
        self.ret_val = ret_val

    def __getattr__(self, name):
        """this is runned if self.name fails"""
        return self.ret_val


class SpyCls(object):
    """type for test which trace object usage:
      it allows to access any field / method
      it counts number of getting / calling   fields / methods
      """
    def __new__(cls, *args):
        obj = super(SpyCls, cls).__new__(cls, *args)
        obj.num_method_calls = NumDict()
        return obj

    def __getattr__(self, name):
        """this is runned if self.name fails"""
        self.num_method_calls[name] += 1
        return fake_function

class SpyMethod(SpyCls):
    def __init__(self):
        self.num_calls = 0
    def __call__(self, *args, **kwargs):
        self.num_calls += 1

class SpyCallbackMethod(SpyMethod):
    def __call__(self, f, *args, **kwargs):
        super(SpyCallbackMethod, self).__call__(f, *args, **kwargs)
        return f(*args, **kwargs)


def wrap_with_event_beginning(obj, fun_name):
    """wrap obj.fun_name function with event set at the beginning of the
    function"""
    e = Event()
    orig = obj.__getattribute__(fun_name)
    def wrapper():
        e.set()
        orig()
    obj.__setattr__(fun_name, wrapper)
    return e

def wrap_with_event_ending(obj, fun_name):
    """wrap obj.fun_name function with event set at the ending of the
    function"""
    e = Event()
    orig = obj.__getattribute__(fun_name)
    def wrapper():
        orig()
        e.set()
    obj.__setattr__(fun_name, wrapper)
    return e
