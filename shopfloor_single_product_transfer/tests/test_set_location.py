# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from .common import CommonCase


class TestSetLocation(CommonCase):
    # set_location shoulf behave the same way as _set_quantity__by_location,
    # which is tested in its own test file.
    # Here we're only verifying that the set_location endpoint works.

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.location = cls.location_src
        cls.product = cls.product_a

    @classmethod
    def _setup_picking(cls):
        cls._add_stock_to_product(cls.product, cls.location, 10)
        return cls._create_picking(lines=[(cls.product, 10)])

    def test_set_location_ok(self):
        package = (
            self.env["stock.quant.package"].sudo().create({"name": "test-package"})
        )
        picking = self._setup_picking()
        move_line = picking.move_line_ids
        location = self.dispatch_location
        response = self.service.dispatch(
            "set_location",
            params={
                "selected_line_id": move_line.id,
                "package_id": package.id,
                "barcode": location.name,
            },
        )
        expected_message = self.msg_store.transfer_done_success(move_line.picking_id)
        completion_info = self.service._actions_for("completion.info")
        expected_popup = completion_info.popup(move_line)
        data = {"location": self._data_for_location(self.location)}
        self.assert_response(
            response,
            next_state="select_product",
            message=expected_message,
            data=data,
            popup=expected_popup,
        )

    def test_set_location_barcode_not_found(self):
        package = (
            self.env["stock.quant.package"].sudo().create({"name": "test-package"})
        )
        picking = self._setup_picking()
        move_line = picking.move_line_ids
        response = self.service.dispatch(
            "set_location",
            params={
                "selected_line_id": move_line.id,
                "package_id": package.id,
                "barcode": "wrong-barcode",
            },
        )
        expected_data = {
            "move_line": self._data_for_move_line(move_line),
            "package": self._data_for_package(package),
        }
        expected_message = self.msg_store.barcode_not_found()
        self.assert_response(
            response,
            next_state="set_location",
            data=expected_data,
            message=expected_message,
        )
