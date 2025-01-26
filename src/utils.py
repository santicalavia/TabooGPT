class CircularBuffer():
    """
    A circular buffer that cycles through a list of elements infinitely.

    Attributes:
        elements (list): The list of elements to cycle through.
        index (int): The current index in the buffer.
    """
    def __init__(self, elements : list):
        """
        Initializes the circular buffer with the given elements.

        Args:
            elements (list): The list of elements to be cycled through.
        """
        self.elements = elements
        self.index = 0

    def next(self) -> object:
        """
        Retrieves the next element in the buffer and updates the index.

        Returns:
            Any: The next element in the circular buffer.
        """
        elem = self.elements[self.index]
        self.index += 1
        if self.index == len(self.elements):
            self.index = 0
        return elem