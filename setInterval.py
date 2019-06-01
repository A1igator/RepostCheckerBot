from multiprocessing import Process, Event

def setInterval(interval):
    def decorator(function):
        def wrapper(*args, **kwargs):
            stopped = Event()

            def loop(): # executed in another thread
                while not stopped.wait(interval): # until stopped
                    function(*args, **kwargs)

            t = Process(target=loop)
            t.daemon = True # stop if the program exits
            t.start()
            return stopped
        return wrapper
    return decorator