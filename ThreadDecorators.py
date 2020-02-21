import wx
from functools import wraps
from threading import Thread


def in_main_thread(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        wx.CallAfter(func, *args, **kwargs)

    return wrapper


def in_new_thread(target_func):
    @wraps(target_func)
    def wrapper(*args, **kwargs):
        com_thread = Thread(target=target_func, args=args, kwargs=kwargs)
        com_thread.start()
    return wrapper
