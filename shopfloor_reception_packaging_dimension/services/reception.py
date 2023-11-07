# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo.osv import expression

from odoo.addons.base_rest.components.service import to_int
from odoo.addons.component.core import Component
from odoo.addons.shopfloor.utils import to_float


class Reception(Component):
    _inherit = "shopfloor.reception"

    packaging_update_done = False

    def _before_state__set_quantity(self, picking, line, message=None):
        """Show the packaging dimension screen before the set quantity screen."""
        if self.work.menu.set_packaging_dimension and not self.packaging_update_done:
            packaging = self._get_next_packaging_to_set_dimension(line.product_id)
            if packaging:
                return self._response_for_set_packaging_dimension(
                    picking, line, packaging, message=message
                )
        return super()._before_state__set_quantity(picking, line, message=message)

    def _get_domain_packaging_needs_dimension(self):
        return expression.OR(
            [
                [("packaging_length", "=", 0)],
                [("packaging_length", "=", False)],
                [("width", "=", 0)],
                [("width", "=", False)],
                [("height", "=", 0)],
                [("height", "=", False)],
                [("max_weight", "=", 0)],
                [("max_weight", "=", False)],
                [("qty", "=", 0)],
                [("qty", "=", False)],
                [("barcode", "=", False)],
            ]
        )

    def _get_next_packaging_to_set_dimension(self, product, previous_packaging=None):
        """Return for a product the next packaging needing dimension to be set."""
        next_packaging_id = previous_packaging.id + 1 if previous_packaging else 0
        domain_dimension = self._get_domain_packaging_needs_dimension()
        domain_packaging_id = [
            ("product_id", "=", product.id),
            ("id", ">=", next_packaging_id),
        ]
        domain = expression.AND([domain_packaging_id, domain_dimension])
        return self.env["product.packaging"].search(domain, order="id", limit=1)

    def _response_for_set_packaging_dimension(
        self, picking, line, packaging, message=None
    ):
        return self._response(
            next_state="set_packaging_dimension",
            data={
                "picking": self.data.picking(picking),
                "selected_move_line": self.data.move_line(line),
                "packaging": self.data_detail.packaging_detail(packaging),
            },
            message=message,
        )

    def set_packaging_dimension(
        self, picking_id, selected_line_id, packaging_id, cancel=False, **kwargs
    ):
        """Set the dimension on a product packaging.

        If the user cancel the dimension update we still propose the next
        possible packgaging.

        Transitions:
            - set_packaging_dimension: if more packaging needs dimension
            - set_quantity: otherwise
        """
        picking = self.env["stock.picking"].browse(picking_id)
        selected_line = self.env["stock.move.line"].browse(selected_line_id)
        packaging = self.env["product.packaging"].sudo().browse(packaging_id)
        message = None
        next_packaging = None
        if not packaging:
            message = self.msg_store.record_not_found()
        elif not cancel and self._check_dimension_to_update(kwargs):
            self._update_packaging_dimension(packaging, kwargs)
            message = self.msg_store.packaging_dimension_updated(packaging)

        if packaging:
            next_packaging = self._get_next_packaging_to_set_dimension(
                selected_line.product_id, packaging
            )
        if next_packaging:
            return self._response_for_set_packaging_dimension(
                picking, selected_line, next_packaging, message=message
            )
        self.packaging_update_done = True
        return self._before_state__set_quantity(picking, selected_line, message=message)

    def _check_dimension_to_update(self, dimensions):
        """Return True if there is any dimension that needs to be updated on the packaging."""
        return any([value is not None for key, value in dimensions.items()])

    def _get_dimension_fields_conversion_map(self):
        return {"length": "packaging_length"}

    def _update_packaging_dimension(self, packaging, dimensions_to_update):
        """Update dimension on the packaging."""
        fields_conv_map = self._get_dimension_fields_conversion_map()
        for dimension, value in dimensions_to_update.items():
            if value is not None:
                dimension = fields_conv_map.get(dimension, dimension)
                packaging[dimension] = value


class ShopfloorReceptionValidator(Component):
    _inherit = "shopfloor.reception.validator"

    def set_packaging_dimension(self):
        return {
            "picking_id": {"coerce": to_int, "required": True, "type": "integer"},
            "selected_line_id": {
                "coerce": to_int,
                "required": True,
                "type": "integer",
            },
            "packaging_id": {"coerce": to_int, "required": True, "type": "integer"},
            "height": {
                "coerce": to_float,
                "required": False,
                "type": "float",
                "nullable": True,
            },
            "length": {
                "coerce": to_float,
                "required": False,
                "type": "float",
                "nullable": True,
            },
            "width": {
                "coerce": to_float,
                "required": False,
                "type": "float",
                "nullable": True,
            },
            "max_weight": {
                "coerce": to_float,
                "required": False,
                "type": "float",
                "nullable": True,
            },
            "shipping_weight": {
                "coerce": to_float,
                "required": False,
                "type": "float",
                "nullable": True,
            },
            "qty": {
                "coerce": to_float,
                "required": False,
                "type": "float",
                "nullable": True,
            },
            "barcode": {"type": "string", "required": False, "nullable": True},
            "cancel": {"type": "boolean"},
        }


class ShopfloorReceptionValidatorResponse(Component):
    _inherit = "shopfloor.reception.validator.response"

    def _states(self):
        res = super()._states()
        res.update({"set_packaging_dimension": self._schema_set_packaging_dimension})
        return res

    def _scan_line_next_states(self):
        res = super()._scan_line_next_states()
        res.update({"set_packaging_dimension"})
        return res

    def _set_lot_confirm_action_next_states(self):
        res = super()._set_lot_confirm_action_next_states()
        res.update({"set_packaging_dimension"})
        return res

    @property
    def _schema_set_packaging_dimension(self):
        return {
            "picking": {"type": "dict", "schema": self.schemas.picking()},
            "selected_move_line": {"type": "dict", "schema": self.schemas.move_line()},
            "packaging": {
                "type": "dict",
                "schema": self.schemas_detail.packaging_detail(),
            },
        }
