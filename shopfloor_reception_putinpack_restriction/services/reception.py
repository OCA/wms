# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)


from datetime import timezone

from odoo.addons.component.core import Component

UTC = timezone.utc


class Reception(Component):
    _inherit = "shopfloor.reception"

    def _check_picking_putinpack_restriction(self, picking, with_pack: bool):
        if picking.put_in_pack_restriction == "no_package" and with_pack:
            return self.msg_store.package_not_allowed_for_operation(picking)
        if picking.put_in_pack_restriction == "with_package" and not with_pack:
            return self.msg_store.package_required_for_operation(picking)

    def process_with_existing_pack(self, picking_id, selected_line_id, quantity):
        picking = self.env["stock.picking"].browse(picking_id)
        selected_line = self.env["stock.move.line"].browse(selected_line_id)

        if message := self._check_picking_putinpack_restriction(
            picking, with_pack=True
        ):
            return self._response_for_set_quantity(
                picking, selected_line, message=message
            )
        res = super().process_with_existing_pack(picking_id, selected_line_id, quantity)

        return res

    def process_with_new_pack(self, picking_id, selected_line_id, quantity):
        picking = self.env["stock.picking"].browse(picking_id)
        selected_line = self.env["stock.move.line"].browse(selected_line_id)

        if message := self._check_picking_putinpack_restriction(
            picking, with_pack=True
        ):
            return self._response_for_set_quantity(
                picking, selected_line, message=message
            )
        res = super().process_with_new_pack(picking_id, selected_line_id, quantity)

        return res

    def process_without_pack(self, picking_id, selected_line_id, quantity):
        picking = self.env["stock.picking"].browse(picking_id)
        selected_line = self.env["stock.move.line"].browse(selected_line_id)

        if message := self._check_picking_putinpack_restriction(
            picking, with_pack=False
        ):
            return self._response_for_set_quantity(
                picking, selected_line, message=message
            )
        res = super().process_without_pack(picking_id, selected_line_id, quantity)

        return res

    def _set_quantity__by_package(self, picking, selected_line, package):
        if message := self._check_picking_putinpack_restriction(
            picking, with_pack=True
        ):
            return self._response_for_set_quantity(
                picking, selected_line, message=message
            )
        return super()._set_quantity__by_package(picking, selected_line, package)

    def _set_quantity__by_new_package(
        self, picking, selected_line, barcode: str, confirmation: str
    ):
        if message := self._check_picking_putinpack_restriction(
            picking, with_pack=True
        ):
            return self._response_for_set_quantity(
                picking, selected_line, message=message
            )
        return super()._set_quantity__by_new_package(
            picking, selected_line, barcode, confirmation
        )

    def _response_for_set_quantity(
        self, picking, line, message=None, asking_confirmation=None
    ):
        pip_restriction = picking.put_in_pack_restriction

        if pip_restriction == "no_package" and asking_confirmation:
            return self._response_for_set_quantity(
                picking,
                line,
                message=self.msg_store.package_not_allowed_for_operation(picking),
            )

        res = super()._response_for_set_quantity(
            picking, line, message, asking_confirmation
        )
        if pip_restriction:
            res["data"]["set_quantity"]["put_in_pack_restriction"] = pip_restriction
        return res


class ShopfloorReceptionValidatorResponse(Component):
    _inherit = "shopfloor.reception.validator.response"

    @property
    def _schema_set_quantity(self):
        res = super()._schema_set_quantity
        picking_type_model = self.env["stock.picking.type"]
        selection_put_in_pack_restriction_values = [
            x[0] for x in picking_type_model._selection_put_in_pack_restriction()
        ]
        res.update(
            {
                "put_in_pack_restriction": {
                    "type": "string",
                    "nullable": True,
                    "required": False,
                    "allowed": selection_put_in_pack_restriction_values,
                },
            }
        )
        return res
