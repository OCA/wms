# Copyright 2020 Camptocamp (https://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import logging

from odoo import _, fields
from odoo.tests import common

from odoo.addons.stock_available_to_promise_release.tests.common import (
    PromiseReleaseCommonCase,
)


class ReleaseChannelCase(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.customer_location = cls.env.ref("stock.stock_location_customers")
        cls.default_channel = cls.env.ref(
            "stock_release_channel.stock_release_channel_default"
        )
        cls._create_base_data()

    def setUp(self):
        super(ReleaseChannelCase, self).setUp()
        loggers = ["odoo.addons.stock_release_channel.models.stock_release_channel"]
        for logger in loggers:
            logging.getLogger(logger).addFilter(self)

        # pylint: disable=unused-variable
        @self.addCleanup
        def un_mute_logger():
            for logger_ in loggers:
                logging.getLogger(logger_).removeFilter(self)

    def filter(self, record):
        return 0

    @classmethod
    def _create_base_data(cls):
        cls.wh = cls.env["stock.warehouse"].create(
            {
                "name": "Test Warehouse",
                "reception_steps": "one_step",
                "delivery_steps": "pick_ship",
                "code": "WHTEST",
            }
        )
        cls.wh.delivery_route_id.write({"available_to_promise_defer_pull": True})
        cls.product1 = cls.env["product.product"].create(
            {"name": "Test Product 1", "barcode": "test", "type": "product"}
        )
        cls.product2 = cls.env["product.product"].create(
            {"name": "Test Product 2", "barcode": "test2", "type": "product"}
        )
        # Set product1 as default product
        cls.product = cls.product1

    @classmethod
    def _update_qty_in_location(
        cls, location, product, quantity, package=None, lot=None, in_date=None
    ):
        quants = cls.env["stock.quant"]._gather(
            product, location, lot_id=lot, package_id=package, strict=True
        )
        # this method adds the quantity to the current quantity, so remove it
        quantity -= sum(quants.mapped("quantity"))
        cls.env["stock.quant"]._update_available_quantity(
            product,
            location,
            quantity,
            package_id=package,
            lot_id=lot,
            in_date=in_date,
        )

    @classmethod
    def _create_single_move(cls, product, qty, group=None):
        # create a group so different moves are not merged in
        # the same picking
        if not group:
            group = cls.env["procurement.group"].create({})
        picking_type = cls.wh.out_type_id
        move_vals = {
            "name": product.name,
            "picking_type_id": picking_type.id,
            "product_id": product.id,
            "product_uom_qty": qty,
            "product_uom": product.uom_id.id,
            "location_id": picking_type.default_location_src_id.id,
            "location_dest_id": cls.customer_location.id,
            "state": "confirmed",
            "procure_method": "make_to_stock",
            "group_id": group.id,
        }
        move = cls.env["stock.move"].create(move_vals)
        move._assign_picking()
        return move

    @classmethod
    def _create_channel(cls, **vals):
        # Forced update state of channel to "open"
        vals.update({"state": "open"})
        return cls.env["stock.release.channel"].create(vals)

    def _run_customer_procurement(self, date=None):
        """
        Call this in order to create a procurement on customer
        location.

        Before, set self.product as the product to be used
        """
        self.customer_procurement = self.env["procurement.group"].create(
            {
                "name": "Customer procurement",
            }
        )
        values = {
            "company_id": self.wh.company_id,
            "group_id": self.customer_procurement,
            "date_planned": date or fields.Datetime.now(),
            "warehouse_id": self.wh,
        }
        self.env["procurement.group"].run(
            [
                self.env["procurement.group"].Procurement(
                    self.product,
                    10.0,
                    self.product.uom_id,
                    self.customer_location,
                    "TEST",
                    "TEST",
                    self.wh.company_id,
                    values,
                )
            ]
        )

    @classmethod
    def _run_procurement(cls, move, date=None):
        values = {
            "company_id": cls.wh.company_id,
            "group_id": move.picking_id.group_id,
            "date_planned": date or fields.Datetime.now(),
            "warehouse_id": cls.wh,
        }
        cls.env["procurement.group"].run(
            [
                cls.env["procurement.group"].Procurement(
                    move.product_id,
                    move.product_uom_qty,
                    move.product_uom,
                    cls.customer_location,
                    "TEST",
                    "TEST",
                    cls.wh.company_id,
                    values,
                )
            ]
        )


class ChannelReleaseCase(PromiseReleaseCommonCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.commercial_partner = cls.env["res.partner"].create({"name": "Main Company"})
        cls.delivery_address_1 = cls.env["res.partner"].create(
            {"name": "Delivery 1", "parent_id": cls.commercial_partner.id}
        )
        cls.delivery_address_2 = cls.env["res.partner"].create(
            {"name": "Delivery 2", "parent_id": cls.commercial_partner.id}
        )
        cls.other_partner = cls.env["res.partner"].create({"name": "Partner 2"})

        cls.wh.delivery_route_id.write({"available_to_promise_defer_pull": True})
        cls.picking = cls._out_picking(
            cls._create_picking_chain(
                cls.wh,
                [(cls.product1, 5), (cls.product2, 5)],
                move_type="direct",
            )
        )
        cls.picking.partner_id = cls.delivery_address_1
        cls.picking2 = cls._out_picking(
            cls._create_picking_chain(
                cls.wh,
                [(cls.product1, 5), (cls.product2, 5)],
                move_type="direct",
            )
        )
        cls.picking2.partner_id = cls.delivery_address_2
        cls.picking3 = cls._out_picking(
            cls._create_picking_chain(
                cls.wh,
                [(cls.product1, 5), (cls.product2, 5)],
                move_type="direct",
            )
        )
        cls.picking3.partner_id = cls.other_partner
        (cls.picking + cls.picking2 + cls.picking3).assign_release_channel()

        cls.channel = cls.picking.release_channel_id

    @classmethod
    def _out_picking(cls, pickings):
        return pickings.filtered(lambda r: r.picking_type_code == "outgoing")

    def _action_done_picking(self, picking):
        for line in picking.move_line_ids:
            line.qty_done = line.reserved_qty
        picking._action_done()

    def _assert_action_nothing_in_the_queue(self, action):
        self.assertEqual(
            action,
            {
                "effect": {
                    "fadeout": "fast",
                    "message": _("Nothing in the queue!"),
                    "img_url": "/web/static/src/img/smile.svg",
                    "type": "rainbow_man",
                }
            },
        )
