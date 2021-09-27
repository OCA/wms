# Copyright 2021 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo.tests.common import SavepointCase


class Common(SavepointCase):
    at_install = False
    post_install = True

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.storage_type_pallet = cls.env.ref(
            "stock_storage_type.package_storage_type_pallets"
        )
        cls.storage_type_pallet.barcode = "123"
        cls.product = cls.env.ref("product.product_delivery_01")
        cls.product.tracking = "lot"
        cls.product_packaging = cls._create_packaging("PKG TEST", cls.product, qty=4)

        cls.product_2 = cls.env.ref("product.product_delivery_02")
        cls.product_2.tracking = "none"
        cls.product_2_packaging = cls._create_packaging(
            "PKG TEST 2", cls.product_2, qty=2
        )

        cls.location_dest = cls.env.ref("stock.stock_location_stock")
        cls.location_src = cls.env.ref("stock.stock_location_suppliers")
        cls.picking = cls._create_picking_in(partner=cls.env.ref("base.res_partner_1"))
        cls._create_picking_line(cls.picking, cls.product, 10)
        cls._create_picking_line(cls.picking, cls.product_2, 10)
        cls.picking.action_confirm()
        cls.picking.action_reception_screen_open()
        cls.screen = cls.picking.reception_screen_id

    @classmethod
    def _create_picking_line(cls, picking, product, qty):
        return cls.env["stock.move"].create(
            {
                "picking_id": picking.id,
                "name": product.display_name,
                "product_id": product.id,
                "product_uom": product.uom_id.id,
                "product_uom_qty": qty,
                "location_id": cls.location_src.id,
                "location_dest_id": cls.location_dest.id,
            }
        )

    @classmethod
    def _create_picking_in(cls, partner):
        return cls.env["stock.picking"].create(
            {
                "partner_id": partner.id,
                "location_id": cls.location_src.id,
                "location_dest_id": cls.location_dest.id,
                "picking_type_id": cls.env.ref("stock.picking_type_in").id,
            }
        )

    @classmethod
    def _create_packaging(cls, name, product, qty):
        return cls.env["product.packaging"].create(
            {
                "name": name,
                "product_id": product.id,
                "qty": qty,
                "package_storage_type_id": cls.storage_type_pallet.id,
                "height": 200,
                "width": 500,
                "packaging_length": 500,
                "max_weight": 10,
            }
        )
