class Observer():
    """Observer class that functions as a dictionary of range(3):[list of functions]
                    it is to be used to control the execution of the various parts
                    of the GUI during experiment."""

    def __init__(self):
        self.dict = dict()
        for i in range(3): self.dict[i] = []  # initiating empty iterables as values for all keys of the dict.

    def subscribe(self, subscriber, row):
        self.dict[row].append(subscriber)

    def unsubscribe(self, subscriber):
        for i in range(3):
            self.dict[i] = [value for value in self.dict[i] if value != subscriber]

    def unsubscribe_row(self, subscriber, row):
        self.dict[row] = [value for value in self.dict[row] if value != subscriber]

    def call_subscribers(self, row):
        for function in self.dict[row]:
            function()
