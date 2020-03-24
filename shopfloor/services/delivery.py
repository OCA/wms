from odoo.addons.component.core import Component


class Delivery(Component):
    """
    Methods for the Delivery Process

    TODO

    Flow Diagram: https://www.draw.io/#G1qRenBcezk50ggIazDuu2qOfkTsoIAxXP
    """

    _inherit = "base.shopfloor.service"
    _name = "shopfloor.delivery"
    _usage = "delivery"
    _description = __doc__


class ShopfloorDeliveryValidator(Component):
    """Validators for the Delivery endpoints"""

    _inherit = "base.shopfloor.validator"
    _name = "shopfloor.delivery.validator"
    _usage = "delivery.validator"


class ShopfloorDeliveryValidatorResponse(Component):
    """Validators for the Delivery endpoints responses"""

    _inherit = "base.shopfloor.validator.response"
    _name = "shopfloor.delivery.validator.response"
    _usage = "delivery.validator.response"

    _start_state = "start"

    def _states(self):
        """List of possible next states

        With the schema of the data send to the client to transition
        to the next state.
        """
        return {
            "start": {},
        }
