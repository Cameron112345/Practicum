from threading import Thread, Event

def init():
    global thread
    global thread_archive_id
    global event

    thread = Thread()
    thread_archive_id = -1
    event = Event()