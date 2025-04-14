from functools import wraps


def additional_info(arg):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            print(f'Additional info is {arg}')
            return f(*args, **kwargs)
        return wrapper
    return decorator


@additional_info('Some info')
def amazing_func(name, age=25, height=200):
    print(f'My name is {name}, age is {age}, height is {height}')


me = amazing_func('Andrey')
