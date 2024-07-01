# Copyright 2021 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.safe_eval import test_python_expr


class StockDeviceType(models.Model):

    _inherit = "stock.device.type"

    line_sort_key_code = fields.Text(
        groups="base.group_system",
        string="Line sort key method",
        help="""Python code to sort the lines in the batch.

        The 'line' will be a recordset of stock.move.line.
        and the method must assign a value to the variable 'key'
        that will be used to sort the lines. You can also call
        the super method to get the default behavior.
        """,
    )

    @api.constrains("line_sort_key_code")
    def _check_line_sort_key_code(self):
        for record in self:
            code = record.line_sort_key_code and record.line_sort_key_code.strip()
            if not code:
                continue
            msg = test_python_expr(expr=code, mode="exec")
            if msg:
                raise ValidationError(msg)
