# This file implements the Event + Observer pattern for notifications and logging hooks.

class Event:
    def __init__(self):
        self._observers = []

    def subscribe(self, observer):
        if observer not in self._observers:
            self._observers.append(observer)

    def unsubscribe(self, observer):
        self._observers.remove(observer)

    def notify(self, *args, **kwargs):
        for observer in self._observers:
            observer.update(*args, **kwargs)


class Observer:
    def update(self, *args, **kwargs):
        raise NotImplementedError("Observer must implement the update method.")