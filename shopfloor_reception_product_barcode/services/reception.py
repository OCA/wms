# Copyright 2023 Camptocamp SA
# Copyright 2025 ACSONE SA/NV (https://acsone.eu)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo.osv import expression

from odoo.addons.base_rest.components.service import to_int
from odoo.addons.component.core import Component
from odoo.addons.product.models.product_product import ProductProduct


class Reception(Component):
    _inherit = "shopfloor.reception"

    product_barcode_update_done = False

    def _before_state__set_quantity(self, picking, line, message=None):
        """
        Check if product needs its barcode before
        """
        if self.work.menu.set_product_barcode and not self.product_barcode_update_done:
            product = self._get_product_to_set_barcode(line.product_id)
            if product:
                return self._response_for_set_product_barcode(
                    picking, line, message=message
                )
        return super()._before_state__set_quantity(picking, line, message=message)

    def _get_domain_product_needs_barcode(self):
        """
        Returns the domain to filter product that should be
        selected for barcode assignation.
        """
        return expression.OR(
            [
                [("barcode", "=", "")],
                [("barcode", "=", False)],
            ]
        )

    def _get_product_to_set_barcode(self, product) -> ProductProduct:
        """
        Filter the selected product to check if barcode
        should be set.
        """
        domain_dimension = self._get_domain_product_needs_barcode()
        return product.filtered_domain(domain_dimension)

    def _response_for_set_product_barcode(self, picking, line, message=None) -> dict:
        return self._response(
            next_state="set_product_barcode",
            data={
                "picking": self.data.picking(picking),
                "selected_move_line": self.data.move_line(line),
                "product": self.data_detail.product_detail(line.product_id),
                "product_barcode": line.product_id.barcode or "",
            },
            message=message,
        )

    def set_product_barcode_scan(self, picking_id, selected_line_id, barcode) -> dict:
        """
        This will parse the scanned barcode and return the result
        """
        search = self._actions_for("search")
        result = search.parser.parse(barcode, ["product"])
        result_value = result[0].value if result else ""
        picking = self.env["stock.picking"].browse(picking_id)
        selected_line = self.env["stock.move.line"].browse(selected_line_id)
        return self._response(
            next_state="set_product_barcode",
            data={
                "picking": self.data.picking(picking),
                "selected_move_line": self.data.move_line(selected_line),
                "product": self.data_detail.product_detail(selected_line.product_id),
                "product_barcode": result_value,
            },
        )

    def set_product_barcode(
        self,
        picking_id,
        selected_line_id,
        barcode,
        cancel=False,
    ) -> dict:
        """
        Set the barcode on a product if not already set.
        """
        picking = self.env["stock.picking"].browse(picking_id)
        selected_line = self.env["stock.move.line"].browse(selected_line_id)
        product = self._get_product_to_set_barcode(selected_line.product_id)
        message = None
        if product and not cancel:
            self._update_product_barcode(product, barcode)
            message = self.msg_store.product_barcode_updated(product)
        self.product_barcode_update_done = True
        return super()._before_state__set_quantity(
            picking, selected_line, message=message
        )

    def _update_product_barcode(self, product, barcode) -> None:
        """Update barcode on the product."""
        product_sudo = product.sudo()
        product_sudo.barcode = barcode


class ShopfloorReceptionValidator(Component):
    _inherit = "shopfloor.reception.validator"

    def set_product_barcode(self) -> dict:
        return {
            "picking_id": {"coerce": to_int, "required": True, "type": "integer"},
            "selected_line_id": {
                "coerce": to_int,
                "required": True,
                "type": "integer",
            },
            "barcode": {
                "required": True,
                "type": "string",
                "nullable": True,
            },
            "cancel": {"type": "boolean"},
        }

    def set_product_barcode_scan(self) -> dict:
        return {
            "picking_id": {"coerce": to_int, "required": True, "type": "integer"},
            "selected_line_id": {
                "coerce": to_int,
                "required": True,
                "type": "integer",
            },
            "barcode": {
                "required": True,
                "type": "string",
                "nullable": True,
            },
        }


class ShopfloorReceptionValidatorResponse(Component):
    _inherit = "shopfloor.reception.validator.response"

    def _states(self) -> dict:
        res = super()._states()
        res.update(
            {
                "set_product_barcode": self._schema_set_product_barcode,
                "set_product_barcode_scan": self._schema_set_product_barcode_scan,
            }
        )
        return res

    def _scan_line_next_states(self) -> dict:
        res = super()._scan_line_next_states()
        res.update({"set_product_barcode"})
        return res

    def _set_lot_confirm_action_next_states(self) -> dict:
        res = super()._set_lot_confirm_action_next_states()
        res.update({"set_product_barcode"})
        return res

    @property
    def _schema_set_product_barcode(self) -> dict:
        return {
            "picking": {"type": "dict", "schema": self.schemas.picking()},
            "selected_move_line": {"type": "dict", "schema": self.schemas.move_line()},
            "product": {"type": "dict", "schema": self.schemas_detail.product_detail()},
            "product_barcode": {"type": "string", "required": False, "nullable": True},
        }

    @property
    def _schema_set_product_barcode_scan(self) -> dict:
        return self._schema_set_product_barcode
