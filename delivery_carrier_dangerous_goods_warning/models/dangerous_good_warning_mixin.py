# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class DangerousGoodCarrierWarningMixin(models.AbstractModel):

    _name = "dangerous.good.warning.mixin"
    _description = "Display warning according to carrier and dangerous goods"

    _line_field_name = None
    _line_doc_m2o_field_name = None

    contains_dangerous_goods = fields.Boolean(
        compute="_compute_contains_dangerous_goods",
        search="_search_contains_dangerous_goods",
    )
    display_dangerous_goods_carrier_warning = fields.Boolean(
        compute="_compute_dangerous_goods_carrier_warning"
    )
    dangerous_goods_carrier_warning = fields.Text(
        compute="_compute_dangerous_goods_carrier_warning"
    )

    def _compute_contains_dangerous_goods(self):
        for doc in self:
            doc.contains_dangerous_goods = any(
                [l.product_id.is_dangerous_good for l in doc[self._line_field_name]]
            )

    def _search_contains_dangerous_goods(self, operator, value):
        if operator not in ["=", "!="] or not isinstance(value, bool):
            raise UserError(_("Operation not supported"))
        line_model = self[self._line_field_name]._name
        dangerous_goods_lines = self.env[line_model].search(
            [("product_id.is_dangerous_good", "=", True)]
        )
        return [
            (
                "id",
                "in" if value else "not in",
                dangerous_goods_lines.mapped(self._line_doc_m2o_field_name).ids,
            )
        ]

    @api.depends("contains_dangerous_goods", "carrier_id")
    def _compute_dangerous_goods_carrier_warning(self):
        for doc in self:
            if doc.contains_dangerous_goods and doc.carrier_id.dangerous_goods_warning:
                warning = doc._check_dangerous_goods()
                vals = {
                    "display_dangerous_goods_carrier_warning": True,
                    "dangerous_goods_carrier_warning": warning,
                }
            else:
                vals = {
                    "display_dangerous_goods_carrier_warning": False,
                    "dangerous_goods_carrier_warning": "",
                }
            doc.update(vals)

    def _check_dangerous_goods(self, carrier=None):
        """Display a warning if any line has a dangerous good"""
        self.ensure_one()
        if carrier is None:
            carrier = self.carrier_id
        if (
            carrier
            and carrier.dangerous_goods_warning
            and self.contains_dangerous_goods
        ):
            warnings = [
                line
                for line in self[self._line_field_name]
                if line.product_id.is_dangerous_good
            ]
            return carrier._prepare_dangerous_goods_warning(
                warnings, self._line_field_name
            )
        return ""
