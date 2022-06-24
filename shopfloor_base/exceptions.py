# Copyright 2022 Akretion (https://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.exceptions import UserError


class ShopfloorDispatchError(UserError):
    def __init__(self, payload):
        payload["no_wrap"] = True
        self.rest_json_info = payload
        super().__init__(payload["message"]["body"])


class ShopfloorError(Exception):
    """Base Error for shopfloor apps"""

    def __init__(
        self, message_dict, base_response=None, data=None, next_state=None, popup=None
    ):
        self.base_response = base_response
        self.data = data
        self.next_state = next_state
        self.popup = popup
        self.message_type = message_dict["message_type"]
        super().__init__(message_dict["body"])
