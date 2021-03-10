# Copyright 2021 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo_test_helper import FakeModelLoader

from .test_checkout_base import CheckoutCommonCase
from .test_checkout_select_package_base import CheckoutSelectPackageMixin


class CheckoutListDeliveryPackagingCase(CheckoutCommonCase, CheckoutSelectPackageMixin):
    @classmethod
    def _load_test_models(cls):
        cls.loader = FakeModelLoader(cls.env, cls.__module__)
        cls.loader.backup_registry()
        from .models import DeliveryCarrierTest, ProductPackagingTest

        cls.loader.update_registry((DeliveryCarrierTest, ProductPackagingTest))

    @classmethod
    def tearDownClass(cls):
        cls.loader.restore_registry()
        super(CheckoutListDeliveryPackagingCase, cls).tearDownClass()

    @classmethod
    def setUpClassBaseData(cls, *args, **kwargs):
        super().setUpClassBaseData(*args, **kwargs)
        cls._load_test_models()
        cls.carrier = cls.env["delivery.carrier"].search([], limit=1)
        cls.carrier.sudo().delivery_type = "test"
        cls.picking = cls._create_picking(
            lines=[
                (cls.product_a, 10),
                (cls.product_b, 10),
                (cls.product_c, 10),
                (cls.product_d, 10),
            ]
        )
        cls.picking.carrier_id = cls.carrier
        cls.packaging_type = (
            cls.env["product.packaging.type"]
            .sudo()
            .create({"name": "Transport Box", "code": "TB", "sequence": 0})
        )
        cls.delivery_packaging1 = (
            cls.env["product.packaging"]
            .sudo()
            .create(
                {
                    "name": "Box 1",
                    "package_carrier_type": "test",
                    "packaging_type_id": cls.packaging_type.id,
                    "barcode": "BOX1",
                }
            )
        )
        cls.delivery_packaging2 = (
            cls.env["product.packaging"]
            .sudo()
            .create(
                {
                    "name": "Box 2",
                    "package_carrier_type": "test",
                    "packaging_type_id": cls.packaging_type.id,
                    "barcode": "BOX2",
                }
            )
        )
        cls.delivery_packaging = (
            cls.delivery_packaging1 | cls.delivery_packaging2
        ).sorted("name")

    def test_list_delivery_packaging_available(self):
        self._fill_stock_for_moves(self.picking.move_lines, in_package=True)
        self.picking.action_assign()
        selected_lines = self.picking.move_line_ids
        response = self.service.dispatch(
            "list_delivery_packaging",
            params={
                "picking_id": self.picking.id,
                "selected_line_ids": selected_lines.ids,
            },
        )
        self.assert_response(
            response,
            next_state="select_delivery_packaging",
            data={
                "packaging": self.service.data.delivery_packaging_list(
                    self.delivery_packaging
                ),
            },
        )

    def test_list_delivery_packaging_not_available(self):
        self.delivery_packaging.package_carrier_type = False
        self._fill_stock_for_moves(self.picking.move_lines, in_package=True)
        self.picking.action_assign()
        selected_lines = self.picking.move_line_ids
        # for line in selected_lines:
        #     line.qty_done = line.product_uom_qty
        response = self.service.dispatch(
            "list_delivery_packaging",
            params={
                "picking_id": self.picking.id,
                "selected_line_ids": selected_lines.ids,
            },
        )
        self.assert_response(
            response,
            next_state="select_package",
            data={
                "picking": self._picking_summary_data(self.picking),
                "selected_move_lines": [
                    self._move_line_data(ml) for ml in selected_lines.sorted()
                ],
                "packing_info": self.service._data_for_packing_info(self.picking),
                "no_package_enabled": not self.service.options.get(
                    "checkout__disable_no_package"
                ),
            },
            message=self.service.msg_store.no_delivery_packaging_available(),
        )
