# Copyright 2022 ACSONE SA/NV (http://www.acsone.eu)
# Copyright 2024 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)
from odoo.addons.stock_release_channel.tests.common import ReleaseChannelCase


class TestReleaseChannelProcurement(ReleaseChannelCase):

    """
    Test class for (at least) two steps delivery flows
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._update_qty_in_location(cls.wh.lot_stock_id, cls.product1, 20.0)
        cls._update_qty_in_location(cls.wh.lot_stock_id, cls.product2, 20.0)
        cls.wh.out_type_id.propagate_to_pickings_chain = True
        cls.env["stock.release.channel"].search(
            [("id", "!=", cls.default_channel.id)]
        ).active = False

    @classmethod
    def _create_propagate_channel(cls):
        cls.channel = cls.env["stock.release.channel"].create(
            {
                "name": "Propagate Channel",
                "sequence": 200,
                "rule_domain": [],
            }
        )

    def test_channel_internal_propagation(self):
        """
        Create a procurement on customer location
        Release the channel
        Check the picking is well created and channel is well set
        """
        self.product = self.product1
        pickings_before = self.env["stock.picking"].search(
            [("product_id", "=", self.product.id)]
        )
        self._run_customer_procurement()
        pickings_after = (
            self.env["stock.picking"].search([("product_id", "=", self.product.id)])
            - pickings_before
        )
        pickings_after.assign_release_channel()
        self.assertEqual(pickings_after.release_channel_id, self.default_channel)

        pickings_after.release_available_to_promise()

        pickings_internal = (
            self.env["stock.picking"].search([("product_id", "=", self.product.id)])
            - pickings_after
            - pickings_before
        )

        self.assertEqual(pickings_internal.release_channel_id, self.default_channel)

    def test_channel_internal_no_propagation(self):
        """
        Disable the channel propagation on the pickings
        Create a procurement on customer location
        Release the channel
        Check the picking is well created and channel is not set
        """
        self.wh.out_type_id.propagate_to_pickings_chain = False
        self.product = self.product1
        pickings_before = self.env["stock.picking"].search(
            [("product_id", "=", self.product.id)]
        )
        self._run_customer_procurement()
        pickings_after = (
            self.env["stock.picking"].search([("product_id", "=", self.product.id)])
            - pickings_before
        )
        pickings_after.assign_release_channel()
        self.assertEqual(pickings_after.release_channel_id, self.default_channel)

        pickings_after.release_available_to_promise()

        pickings_internal = (
            self.env["stock.picking"].search([("product_id", "=", self.product.id)])
            - pickings_after
            - pickings_before
        )
        self.assertEqual(1, len(pickings_internal))
        self.assertFalse(pickings_internal.release_channel_id)

    def test_channel_internal_propagation_multi(self):
        """
        This will test a release process to check the multi recordset call

        Create two procurements on customer location for product 1
        Assign the release channel on OUT pickings

        Change the assignation rule on default channel to avoid new pickings
        to be assigned in it.

        Create a procurement on customer location for product 2
        Assign the release channel on OUT picking

        On all OUT pickings, release the channels
        Check the pickings is well created and channels is well set:
            - Default Channel on first two pickings (product 1)
            - New channel on third one (product 2)
        """
        self.product = self.product1
        pickings_before = self.env["stock.picking"].search(
            [("product_id", "=", self.product.id)]
        )
        # Create two procurement on customer location
        self._run_customer_procurement()
        self._run_customer_procurement()
        pickings_after = (
            self.env["stock.picking"].search([("product_id", "=", self.product.id)])
            - pickings_before
        )
        self.assertEqual(2, len(pickings_after))
        pickings_after.assign_release_channel()
        self.assertEqual(pickings_after.release_channel_id, self.default_channel)

        # Add a False domain selection criteria on default channel to assign the other one
        self.default_channel.rule_domain = [(0, "=", 1)]
        self._create_propagate_channel()

        self.product = self.product2
        pickings_before = self.env["stock.picking"].search(
            [("product_id", "=", self.product.id)]
        )
        self._run_customer_procurement()

        picking_out_all = pickings_after

        pickings_after = self.env["stock.picking"].search(
            [("product_id", "=", self.product.id)]
        )
        picking_out_all += pickings_after

        pickings_after.assign_release_channel()
        self.assertEqual(pickings_after.release_channel_id, self.channel)

        # Release all pickings - in both channels
        picking_out_all.release_available_to_promise()

        internal_pickings_product_1 = self.env["stock.picking"].search(
            [
                ("product_id", "=", self.product1.id),
                ("picking_type_id.code", "=", "internal"),
            ]
        )
        self.assertEqual(2, len(internal_pickings_product_1))
        self.assertEqual(
            internal_pickings_product_1.release_channel_id, self.default_channel
        )

        internal_pickings_product_2 = self.env["stock.picking"].search(
            [
                ("product_id", "=", self.product2.id),
                ("picking_type_id.code", "=", "internal"),
            ]
        )

        self.assertEqual(1, len(internal_pickings_product_2))
        self.assertEqual(internal_pickings_product_2.release_channel_id, self.channel)
