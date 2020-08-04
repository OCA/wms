# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo import _, fields, models
from odoo.exceptions import UserError


class DeliveryCarrier(models.Model):

    _inherit = "delivery.carrier"

    dangerous_goods_warning = fields.Boolean(
        string="Dangerous goods warning",
        help="Display warning when products defined as dangerous goods are "
        "used with this carrier.",
    )

    def _prepare_dangerous_goods_warning(self, warnings, checked_object):
        """Prepare warning dictionary to be displayed according to warnings

        :param warnings: List of items with dangerous goods where item is
          either a sale.order.line or stock.move object
        :param checked_object: String being either "order_line" or "move" that
          must match items in warnings parameter
        :return: Warning dictionary
        """
        self.ensure_one()
        object_str = ""
        if checked_object not in ("move_lines", "order_line"):
            raise UserError(
                _(
                    "checked_object parameter %s used to call "
                    "_prepare_dangerous_goods_warning is invalid."
                )
                % checked_object
            )
        elif checked_object == "move_lines":
            object_str = _("move(s)")
        elif checked_object == "order_line":
            object_str = _("order line(s)")
        base_warning_msg = _(
            "Following %s contain dangerous goods that might not "
            "be accepted according to carrier '%s' configuration:\n"
        ) % (object_str, self.name)
        moves_warning_messages = [base_warning_msg]
        for item in warnings:
            moves_warning_messages.append(
                _(" * %s %s with product %s.")
                % (object_str, item.name, item.product_id.name,)
            )
        return "\n".join(moves_warning_messages)
