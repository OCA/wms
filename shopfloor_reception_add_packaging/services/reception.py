# Copyright 2026 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)


from odoo.addons.base_rest.components.service import to_int
from odoo.addons.component.core import Component


class Reception(Component):
    _inherit = "shopfloor.reception"

    def _response_for_set_quantity(
        self, picking, line, message=None, asking_confirmation=None
    ):
        res = super()._response_for_set_quantity(
            picking, line, message, asking_confirmation
        )
        if self.work.menu.create_new_packaging:
            res["data"]["set_quantity"]["create_new_packaging"] = True
        return res

    def _response_for_create_new_packaging(self, picking, line, message=None):
        packaging_levels = self.env["product.packaging.level"].search([])
        response = self._response(
            next_state="create_new_packaging",
            data={
                "selected_move_line": self.data.move_line(line),
                "picking": self.data.picking(picking),
                "packaging_levels": self.data.packaging_levels(packaging_levels),
            },
            message=message,
        )
        return response

    def start_new_packaging(self, picking_id, selected_line_id):
        picking = self.env["stock.picking"].browse(picking_id)
        line = self.env["stock.move.line"].browse(selected_line_id)

        return self._response_for_create_new_packaging(picking, line)

    def create_new_packaging(
        self,
        picking_id,
        selected_line_id,
        name,
        quantity,
        packaging_level_id,
    ):
        picking = self.env["stock.picking"].browse(picking_id)
        line = self.env["stock.move.line"].browse(selected_line_id)
        packaging = (
            self.env["product.packaging"]
            .sudo()
            .create(
                {
                    "name": name,
                    "qty": quantity,
                    "product_id": line.product_id.id,
                    "packaging_level_id": packaging_level_id,
                }
            )
        )

        return self._response_for_set_quantity(
            picking,
            line,
            message=self.msg_store.new_packaging_created(packaging),
        )


class ShopfloorReceptionValidator(Component):
    _inherit = "shopfloor.reception.validator"

    def create_new_packaging(self):
        return {
            "picking_id": {"coerce": to_int, "required": True, "type": "integer"},
            "selected_line_id": {
                "coerce": to_int,
                "required": True,
                "type": "integer",
            },
            "name": {"type": "string", "required": True},
            "quantity": {
                "coerce": to_int,
                "required": True,
                "type": "integer",
            },
            "packaging_level_id": {
                "coerce": to_int,
                "required": True,
                "type": "integer",
            },
        }

    def start_new_packaging(self):
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
        res.update({"create_new_packaging": self._schema_create_new_packaging})
        return res

    @property
    def _schema_create_new_packaging(self):
        return {
            "picking": {"type": "dict", "schema": self.schemas.picking()},
            "selected_move_line": {"type": "dict", "schema": self.schemas.move_line()},
            "packaging_levels": {
                "type": "dict",
                "schema": self.schemas._schema_list_of(self.schemas._simple_record()),
            },
        }

    def _create_new_packaging_next_state(self):
        return {"create_new_packaging", "set_quantity"}

    def create_new_packaging(self):
        return self._response_schema(
            next_states=self._create_new_packaging_next_state()
        )

    @property
    def _schema_set_quantity(self):
        res = super()._schema_set_quantity

        res.update(
            {
                "create_new_packaging": {
                    "type": "boolean",
                    "nullable": True,
                    "required": False,
                },
            }
        )
        return res
