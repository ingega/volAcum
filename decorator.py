import functools
import time

def add_log_in(msg):
    miarch=open("log.txt","a")
    msg += f' {time.asctime(time.gmtime())}\n'
    miarch.write(msg)
    miarch.close()
    print(msg)


def print_func_text(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        msg=f"this is the init of {func.__name__}"
        add_log_in(msg)
        result = func(*args, **kwargs)
        msg = f"this is the end of {func.__name__}"
        add_log_in(msg)
        return result
    return wrapper