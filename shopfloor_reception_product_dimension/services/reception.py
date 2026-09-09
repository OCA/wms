# Copyright 2023 Camptocamp SA
# Copyright 2025 ACSONE SA/NV (https://acsone.eu)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)

from odoo.osv import expression

from odoo.addons.base_rest.components.service import to_int
from odoo.addons.component.core import Component
from odoo.addons.shopfloor.utils import to_float


class Reception(Component):
    _inherit = "shopfloor.reception"

    product_dimension_update_done = False

    def _before_state__set_quantity(self, picking, line, message=None):
        """Show the product dimension screen before the set quantity screen."""
        if (
            self.work.menu.set_product_dimension
            and not self.product_dimension_update_done
        ):
            product = self._get_product_to_set_dimension(line.product_id)
            if product:
                return self._response_for_set_product_dimension(
                    picking, line, message=message
                )
        return super()._before_state__set_quantity(picking, line, message=message)

    def _get_domain_product_needs_dimension(self):
        return expression.OR(
            [
                [("product_width", "=", 0)],
                [("product_width", "=", False)],
                [("product_height", "=", 0)],
                [("product_height", "=", False)],
                [("product_length", "=", 0)],
                [("product_length", "=", False)],
                [("product_length", "=", 0)],
                [("product_length", "=", False)],
                [("weight", "=", 0)],
                [("weight", "=", False)],
            ]
        )

    def _get_product_to_set_dimension(self, product):
        """
        Filter product if it misses one or several dimensions
        """
        domain_dimension = self._get_domain_product_needs_dimension()
        return product.filtered_domain(domain_dimension)

    def _response_for_set_product_dimension(self, picking, line, message=None):
        return self._response(
            next_state="set_product_dimension",
            data={
                "picking": self.data.picking(picking),
                "selected_move_line": self.data.move_line(line),
                "product": self.data_detail.product_detail(line.product_id),
            },
            message=message,
        )

    def set_product_dimension(
        self, picking_id, selected_line_id, cancel=False, **kwargs
    ):
        """Set the dimension on a product.

        If the user cancel the dimension update we still propose the next
        possible packgaging.

        Transitions:
            - set_product_dimension: if more packaging needs dimension
            - set_quantity: otherwise
        """
        picking = self.env["stock.picking"].browse(picking_id)
        selected_line = self.env["stock.move.line"].browse(selected_line_id)
        product = self._get_product_to_set_dimension(selected_line.product_id)
        message = None
        if product and (not cancel and self._check_product_dimension_to_update(kwargs)):
            self._update_product_dimension(product, kwargs)
            message = self.msg_store.product_dimension_updated(product)
        self.product_dimension_update_done = True
        return super()._before_state__set_quantity(
            picking, selected_line, message=message
        )

    def _check_product_dimension_to_update(self, dimensions):
        """Return True if there is any dimension that needs to be updated on the product."""
        return any([value is not None for key, value in dimensions.items()])

    def _get_product_dimension_fields_conversion_map(self):
        return {
            "height": "product_height",
            "length": "product_length",
            "width": "product_width",
            "weight": "weight",
        }

    def _update_product_dimension(self, product, dimensions_to_update):
        """Update dimension on the packaging."""
        product_sudo = product.sudo()
        fields_conv_map = self._get_product_dimension_fields_conversion_map()
        for dimension, value in dimensions_to_update.items():
            if value is not None:
                dimension = fields_conv_map.get(dimension, dimension)
                product_sudo[dimension] = value


class ShopfloorReceptionValidator(Component):
    _inherit = "shopfloor.reception.validator"

    def set_product_dimension(self):
        return {
            "picking_id": {"coerce": to_int, "required": True, "type": "integer"},
            "selected_line_id": {
                "coerce": to_int,
                "required": True,
                "type": "integer",
            },
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
            "weight": {
                "coerce": to_float,
                "required": False,
                "type": "float",
                "nullable": True,
            },
            "cancel": {"type": "boolean"},
        }


class ShopfloorReceptionValidatorResponse(Component):
    _inherit = "shopfloor.reception.validator.response"

    def _states(self):
        res = super()._states()
        res.update({"set_product_dimension": self._schema_set_product_dimension})
        return res

    def _scan_line_next_states(self):
        res = super()._scan_line_next_states()
        res.update({"set_product_dimension"})
        return res

    def _set_lot_confirm_action_next_states(self):
        res = super()._set_lot_confirm_action_next_states()
        res.update({"set_product_dimension"})
        return res

    @property
    def _schema_set_product_dimension(self):
        return {
            "picking": {"type": "dict", "schema": self.schemas.picking()},
            "selected_move_line": {"type": "dict", "schema": self.schemas.move_line()},
            "product": {"type": "dict", "schema": self.schemas_detail.product_detail()},
        }
