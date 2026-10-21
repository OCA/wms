# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# Copyright 2023 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import logging

from odoo import _

from odoo.addons.component.core import Component

_logger = logging.getLogger(__name__)


class MessageAction(Component):
    _inherit = "shopfloor.message.action"

    def product_dimension_updated(self, product):
        return {
            "message_type": "success",
            "body": _(
                "Product '%(product_name)s' dimension updated.",
                product_name=product.name,
            ),
        }
