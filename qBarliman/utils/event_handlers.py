import copy
import functools


def clone(model):
    """Creates a deep copy of the model to preserve immutability."""
    return copy.deepcopy(model)


def event_handler(expected_event_name):
    """
    A decorator for event handlers.

    This decorator checks if the incoming event message's name matches the expected name.
    If it does, it clones the model and passes the clone into the wrapped handler.
    The handler is then responsible for returning an updated model.
    If the event name doesn't match, the original model is returned unmodified.

    Example usage:

        @event_handler("update_username")
        def update_username_handler(event_message, model):
            model['username'] = event_message.payload
            return model
    """

    def decorator(handler_func):
        @functools.wraps(handler_func)
        def wrapper(event_message, model):
            if event_message.name == expected_event_name:
                return handler_func(event_message, clone(model))
            return model

        return wrapper

    return decorator
