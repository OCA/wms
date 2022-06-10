# Copyright 2022 Akretion (https://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


class ShopfloorError(Exception):
    """Base Error for shopfloor apps"""

    def __init__(
        self, base_response=None, data=None, next_state=None, message=None, popup=None
    ):

        self.base_response = base_response
        self.data = data
        self.next_state = next_state
        self.message_data = message
        self.popup = popup
        super().__init__(
            base_response=base_response,
            data=data,
            next_state=next_state,
            message=message,
            popup=popup,
        )
