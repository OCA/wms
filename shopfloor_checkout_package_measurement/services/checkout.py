# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)


from odoo.addons.base_rest.components.service import to_int
from odoo.addons.component.core import Component
from odoo.addons.shopfloor.utils import to_float


class Checkout(Component):
    _inherit = "shopfloor.checkout"

    def _response_for_package_measurement(self, picking, selected_lines, package):
        packages_data = self.data.package(
            package,
            with_packaging=True,
        )
        res = self._response(
            next_state="package_measurement",
            data={
                "picking": self.data.picking(picking),
                "package": packages_data,
                "package_requirement": self.data.package_requirement(
                    package.packaging_id
                ),
            },
        )
        return res

    def set_package_measurement(
        self,
        picking_id,
        package_id,
        height=None,
        length=None,
        width=None,
        shipping_weight=None,
    ):
        """Set measurements on a package."""
        picking = self.env["stock.picking"].browse(picking_id)
        message = self._check_picking_status(picking)
        if message:
            return self._response_for_select_document(message=message)
        package = self.env["stock.quant.package"].browse(package_id).exists()
        if not package:
            return self._response_for_summary(
                picking, message=self.msg_store.record_not_found()
            )
        if height:
            package.height = height
        if length:
            package.pack_length = length
        if width:
            package.width = width
        if shipping_weight:
            package.shipping_weight = shipping_weight
        if self.work.menu.auto_post_line:
            # If option auto_post_line is active in the shopfloor menu,
            # create a split order with these packed lines.
            self._auto_post_lines(package.move_line_ids)
        return self._response_for_summary(
            picking,
            message=self.msg_store.package_measurement_changed(),
        )

    def _put_lines_in_allowed_package(self, picking, lines_to_pack, package):
        res = super()._put_lines_in_allowed_package(picking, lines_to_pack, package)
        # Only check if the packaging used requires measurements
        # Because even if the measurements are set on the package, when changing
        # its content, the measurements need to be updated.
        package_measurement_required = (
            package.length_required
            or package.width_required
            or package.height_required
            or package.weight_required
        )
        if package_measurement_required:
            return self._response_for_package_measurement(
                picking, lines_to_pack, package
            )
        return res


class ShopfloorCheckoutValidator(Component):
    _inherit = "shopfloor.checkout.validator"

    def set_package_measurement(self):
        return {
            "picking_id": {"coerce": to_int, "required": True, "type": "integer"},
            "package_id": {"coerce": to_int, "required": False, "type": "integer"},
            "height": {"coerce": to_float, "required": False, "type": "float"},
            "length": {"coerce": to_float, "required": False, "type": "float"},
            "width": {"coerce": to_float, "required": False, "type": "float"},
            "shipping_weight": {"coerce": to_float, "required": False, "type": "float"},
        }


class ShopfloorCheckoutValidatorResponse(Component):
    _inherit = "shopfloor.checkout.validator.response"

    def _states(self):
        res = super()._states()
        res["package_measurement"] = self._schema_package_measurement
        return res

    @property
    def _schema_package_measurement(self):
        return {
            "selected_move_lines": {
                "type": "list",
                "schema": {"type": "dict", "schema": self.schemas.move_line()},
            },
            "package": {
                "type": "dict",
                "schema": self.schemas.package(with_packaging=True),
            },
            "package_requirement": {
                "type": "dict",
                "schema": self.schemas.package_requirement(),
            },
            "picking": {"type": "dict", "schema": self.schemas.picking()},
        }

    def scan_package_action(self):
        res = super().scan_package_action()
        other_schema = self._response_schema(next_states={"package_measurement"})
        res["data"]["schema"].update(other_schema["data"]["schema"])
        return res

    def set_dest_package(self):
        res = super().set_dest_package()
        other_schema = self._response_schema(next_states={"package_measurement"})
        res["data"]["schema"].update(other_schema["data"]["schema"])
        return res

    def set_package_measurement(self):
        return self._response_schema(next_states={"summary"})
