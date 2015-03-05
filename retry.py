# so damn useful it deserved its own file

import time

def retry(Exceptions, tries=10, wait=1):
    if type(Exceptions) == Exception:
        Exceptions = (Exceptions,)
    def retryer(f):
        def deco(*args, **kwargs):
            for i in range(tries - 1):
                try:
                    return f(*args, **kwargs)
                except Exceptions:
                    time.sleep(wait)
            return f(*args, **kwargs)
        return deco
    return retryer
