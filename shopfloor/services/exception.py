from functools import wraps

from odoo import _

class ScenarioError(Exception):
    def __init__(self, response):
        super().__init__("")
        self.response = response


class StateBasedError(Exception):
    def __init__(self, state, data):
        super().__init__("")
        self.state = state
        self.data = data


class MessageNameBasedError(StateBasedError):
    def __init__(self, state, data, message_name, **kw):
        super().__init__(state, data)
        self.message_name = message_name
        self.kw = kw


class MessageBasedError(StateBasedError):
    def __init__(self, state, data, message):
        super().__init__(state, data)
        self.message_dict = message


class BatchDoesNotExistError(Exception):
    pass


class OperationNotFoundError(MessageNameBasedError):
    def __init__(self, state, data):
        super().__init__(state, data, message_name="operation_not_found")


class StockPickingNotFound(MessageNameBasedError):
    def __init__(self, state, data):
        super().__init__(state, data, message_name="stock_picking_not_found")


class CannotMovePickingType(MessageNameBasedError):
    def __init__(self, state, data):
        super().__init__(
            state, data, message_name="cannot_move_something_in_picking_type"
        )


class StockPickingNotAvailable(MessageNameBasedError):
    def __init__(self, state, data):
        super().__init__(state, data, message_name="stock_picking_not_available")


class BarcodeNotFoundError(MessageNameBasedError):
    def __init__(self, state, data):
        super().__init__(state, data, message_name="barcode_not_found")


class UnableToPickMoreError(MessageNameBasedError):
    def __init__(self, state, data, **kw):
        super().__init__(state, data, message_name="unable_to_pick_more", **kw)


class DestLocationNotAllowed(MessageNameBasedError):
    def __init__(self, state, data):
        super().__init__(state, data, message_name="dest_location_not_allowed")


class LocationNotFound(MessageNameBasedError):
    def __init__(self, state, data):
        super().__init__(state, data, message_name="no_location_found")


class TooMuchProductInCommandError(MessageBasedError):
    def __init__(self, state, data):
        message = {
            "message_type": "error",
            "body": _("Too much product in command"),
        }
        super().__init__(state, data, message)


class NoMoreOrderToSkip(MessageBasedError):
    def __init__(self, state, data):
        message = {
            "message_type": "error",
            "body": _("There's no more order to skip"),
        }
        super().__init__(state, data, message)


class ProductNotInSource(MessageBasedError):
    def __init__(self, state, data):
        message = {
            "message_type": "error",
            "body": _("Product is not in source location"),
        }
        super().__init__(state, data, message)


class ProductNotInOrder(MessageBasedError):
    def __init__(self, state, data):
        message = {
            "message_type": "error",
            "body": _("Product is not present in the receipt"),
        }
        super().__init__(state, data, message)


def response_decorator(called_func):
    @wraps(called_func)
    def decorated_response(*args, **kwargs):
        instance = args[0]
        try:
            return called_func(*args, **kwargs)
        except BatchDoesNotExistError:
            return instance._response_batch_does_not_exist()
        except MessageNameBasedError as e:
            message = getattr(instance.msg_store, e.message_name)(**(e.kw))
            return instance._response(next_state=e.state, data=e.data, message=message)
        except MessageBasedError as e:
            return instance._response(
                next_state=e.state, data=e.data, message=e.message_dict
            )
        except ScenarioError as e:
            return e.response

    return decorated_response
