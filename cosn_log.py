#!/usr/bin/env python

#
# Singleton Code From [Python and the Singleton Pattern - Stack Overflow](http://stackoverflow.com/questions/42558/python-and-the-singleton-pattern)
#
class Singleton:
    """
    A non-thread-safe helper class to ease implementing singletons.
    This should be used as a decorator -- not a metaclass -- to the
    class that should be a singleton.

    The decorated class can define one `__init__` function that
    takes only the `self` argument. Other than that, there are
    no restrictions that apply to the decorated class.

    To get the singleton instance, use the `Instance` method. Trying
    to use `__call__` will result in a `TypeError` being raised.

    Limitations: The decorated class cannot be inherited from.

    """

    def __init__(self, decorated):
        self._decorated = decorated

    def Instance(self):
        """
        Returns the singleton instance. Upon its first call, it creates a
        new instance of the decorated class and calls its `__init__` method.
        On all subsequent calls, the already created instance is returned.

        """
        try:
            return self._instance
        except AttributeError:
            self._instance = self._decorated()
            return self._instance

    def __call__(self):
        raise TypeError('Singletons must be accessed through `Instance()`.')

    def __instancecheck__(self, inst):
        return isinstance(inst, self._decorated)

@Singleton
class ActivityLog:

	def __init__(self):
		1
	
	def __del__(self):
		1

	def log(self, log):
		self.file = open("activity.log", "a")
		if log[len(log)-1] != "\n":
			log += "\n"
		self.file.write(log)
		self.file.close()
		

@Singleton
class ErrorLog:

	def __init__(self):
		self.file = open("error.log", "a")
	
	def __del__(self):
		self.file.close()

	def log(self, log):
		self.file.write(log)
