# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo import _, fields, models
from odoo.exceptions import UserError


class DeliveryCarrier(models.Model):

    _inherit = "delivery.carrier"

    adr_limited_amount_ids = fields.Many2many(
        "limited.amount",
        string="Warns according to ADR limited amount",
        help="Raise warning when following limited amount are defined on "
        "any product in the document.",
    )

    def _prepare_adr_warning(self, warnings, checked_object):
        """Prepare warning dictionnary to be displayed according to warnings

        :param warnings: Dict of {item: warning_record} where:
          - item is either a sale.order.line or stock.move object
          - warning_record is an object that defines field name
        :param checked_object: String being either "order_line" or "move" that
          must match items in warnings parameter
        :return: Warning dictionnary
        """
        self.ensure_one()
        single_object_str = ""
        checked_object_str = ""
        if checked_object not in ("move", "order_line"):
            raise UserError(
                _(
                    "checked_object parameter %s used to call "
                    "_prepare_dangerous_goods_warning is invalid."
                )
                % checked_object
            )
        elif checked_object == "move":
            single_object_str = _("Move")
            checked_object_str = _("moves")
        elif checked_object == "order lines":
            single_object_str = _("Order line")
            checked_object_str = _("order lines")
        base_warning_msg = _(
            "Following %s contain products having ADR settings that might not "
            "be accepted according to carrier %s ADR configuration:\n"
        ) % (checked_object_str, self.name)
        moves_warning_messages = [base_warning_msg]
        for item, warning_record in warnings.items():
            moves_warning_messages.append(
                _(" * %s %s has product %s that defined %s.")
                % (
                    single_object_str,
                    item.name,
                    item.product_id.name,
                    warning_record.name,
                )
            )
        return {
            "warning": {
                "title": _("ADR warning"),
                "message": "\n".join(moves_warning_messages),
            }
        }
