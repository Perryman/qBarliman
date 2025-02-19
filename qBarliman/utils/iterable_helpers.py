def find(iterable, pred):
    """
    Returns the first element in 'iterable' for which 'pred' returns True.
    If no element is found, returns None.
    """
    return next((element for element in iterable if pred(element)), None)
