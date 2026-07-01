# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo.osv import expression

from odoo.addons.base_rest.components.service import to_int
from odoo.addons.component.core import Component
from odoo.addons.shopfloor.utils import to_float


class Reception(Component):
    _inherit = "shopfloor.reception"

    def __init__(self, work_context):
        super().__init__(work_context)
        self.packaging_update_done = False

    def _before_state__set_quantity(self, picking, line, message=None):
        """Show the packaging dimension screen before the set quantity screen."""
        if not self.work.menu.set_packaging_dimension or self.packaging_update_done:
            return super()._before_state__set_quantity(picking, line, message=message)

        packaging = self._get_next_packaging_to_set_dimension(line.product_id)
        if not packaging:
            return super()._before_state__set_quantity(picking, line, message=message)

        return self._response_for_set_packaging_dimension(
            picking, line, packaging, message=message
        )

    def _get_domain_packaging_needs_dimension(self):
        return expression.OR(
            [
                [
                    ("packaging_level_id.shopfloor_collect_length", "=", True),
                    "|",
                    ("packaging_length", "=", 0),
                    ("packaging_length", "=", False),
                ],
                [
                    ("packaging_level_id.shopfloor_collect_width", "=", True),
                    "|",
                    ("width", "=", 0),
                    ("width", "=", False),
                ],
                [
                    ("packaging_level_id.shopfloor_collect_height", "=", True),
                    "|",
                    ("height", "=", 0),
                    ("height", "=", False),
                ],
                [
                    ("packaging_level_id.shopfloor_collect_weight", "=", True),
                    "|",
                    ("weight", "=", 0),
                    ("weight", "=", False),
                ],
                [
                    ("packaging_level_id.shopfloor_collect_barcode", "=", True),
                    ("barcode", "=", False),
                ],
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
                "packaging": self._set_packaging_dimension_data_for_packaging(
                    packaging
                ),
            },
            message=message,
        )

    def _set_packaging_dimension_data_for_packaging(self, packaging):
        return self.data.packaging_dimensions(packaging)

    def set_packaging_dimension(
        self, picking_id, selected_line_id, packaging_id, skip=False, **kwargs
    ):
        """Set the dimension on a product packaging.

        If the user skip the dimension update we still propose the next
        possible packaging.

        Transitions:
            - set_packaging_dimension: if more packaging needs dimension
            - set_quantity: otherwise
        """
        picking = self.env["stock.picking"].browse(picking_id)
        selected_line = self.env["stock.move.line"].browse(selected_line_id)
        packaging = self.env["product.packaging"].sudo().browse(packaging_id)

        if not packaging:
            return self._before_state__set_quantity(
                picking, selected_line, message=self.msg_store.record_not_found()
            )

        message = None

        if not skip and self._check_dimension_to_update(kwargs):
            self._update_packaging_dimension(packaging, kwargs)
            message = self.msg_store.packaging_updated(packaging)

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
        """Check if the Shopfloor payload contains data for a packaging update."""
        return any(value is not None for value in dimensions.values())

    def _update_packaging_dimension(self, packaging, dimensions_to_update):
        """Update dimension on the packaging."""
        values_to_update = {}
        packaging_values = packaging.read(dimensions_to_update.keys())[0]

        for key, value in dimensions_to_update.items():
            if value is None:
                continue
            # Skip updating fields with unchanged values to prevent unnecessary
            # triggers of compute methods or other side effects
            if packaging_values[key] != value:
                values_to_update[key] = value

        if values_to_update:
            packaging.write(values_to_update)

    def _response_for_create_new_packaging(
        self, picking, line, packaging, message=None
    ):
        response = self._response(
            next_state="create_new_packaging",
            data={
                "selected_move_line": self.data.move_line(line),
                "picking": self.data.picking(picking),
                "packaging": self.data.packaging_dimensions(packaging),
            },
            message=message,
        )
        return response

    def create_new_packaging(self, picking_id, selected_line_id):
        picking = self.env["stock.picking"].browse(picking_id)
        line = self.env["stock.move.line"].browse(selected_line_id)
        packaging = (
            self.env["product.packaging"]
            .sudo()
            .create(
                {
                    "name": "New Packaging (from Shopfloor)",
                    "product_id": line.product_id.id,
                }
            )
        )

        return self._response_for_create_new_packaging(
            picking,
            line,
            packaging,
            message=self.msg_store.new_packaging_created(packaging),
        )


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
            "packaging_length": {
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
            "name": {"type": "string", "required": False, "nullable": True},
            "skip": {"type": "boolean"},
        }

    def create_new_packaging(self):
        return {
            "picking_id": {"coerce": to_int, "required": True, "type": "integer"},
            "selected_line_id": {
                "coerce": to_int,
                "required": True,
                "type": "integer",
            },
        }


class ShopfloorReceptionValidatorResponse(Component):
    _inherit = "shopfloor.reception.validator.response"

    def _states(self):
        res = super()._states()
        res.update({"set_packaging_dimension": self._schema_set_packaging_dimension})
        res.update({"create_new_packaging": self._schema_create_new_packaging})
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
            "packaging": self._schema_packaging_dimensions(),
        }

    @property
    def _schema_create_new_packaging(self):
        return {
            "picking": {"type": "dict", "schema": self.schemas.picking()},
            "selected_move_line": {"type": "dict", "schema": self.schemas.move_line()},
            "packaging": self._schema_packaging_dimensions(),
        }

    def _schema_packaging_dimensions(self):
        return {
            "type": "dict",
            "schema": self.schemas.packaging_dimensions(),
        }

    def _set_packaging_dimension_next_states(self):
        return {"set_packaging_dimension", "set_quantity"}

    def set_packaging_dimension(self):
        return self._response_schema(
            next_states=self._set_packaging_dimension_next_states()
        )

    def create_new_packaging(self):
        return self._response_schema(next_states={"create_new_packaging"})
