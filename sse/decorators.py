def sse_create(func):
    def wrapper(*args, **kwargs):
        path = args[1].path.split('/')
        obj = path[-2]
        parent_id = path[-3]

        res = func(*args, **kwargs)
        return res
    return wrapper
