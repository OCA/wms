# Copyright 2021 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
from .test_delivery_shipment_base import DeliveryShipmentCommonCase


class DeliveryShipmentLoadingListCase(DeliveryShipmentCommonCase):
    """Tests for '/loading_list' endpoint."""

    def test_loading_list_wrong_id(self):
        response = self.service.dispatch(
            "loading_list", params={"shipment_advice_id": -1}
        )
        self.assert_response_scan_dock(
            response, message=self.service.msg_store.record_not_found()
        )

    def test_loading_list_shipment_planned_partially_loaded(self):
        """Get the loading list of a planned shipment with part of it loaded."""
        # Plan some content in the shipment
        self._plan_records_in_shipment(self.shipment, self.pickings.move_lines)
        # Load a part of it
        #   - part of picking1
        move_line_d = self.picking1.move_line_ids.filtered(
            lambda ml: ml.product_id == self.product_d
        )
        move_line_d._load_in_shipment(self.shipment)
        #   - all content of picking2
        self.picking2._load_in_shipment(self.shipment)
        #   - nothing from picking3
        # Get the loading list
        response = self.service.dispatch(
            "loading_list", params={"shipment_advice_id": self.shipment.id}
        )
        self.assert_response_loading_list(response, self.shipment)
        # Check returned content
        lading = response["data"]["loading_list"]["lading"]
        on_dock = response["data"]["loading_list"]["on_dock"]
        #   'lading' key contains picking1 and picking2
        self.assertEqual(
            lading, self.service.data.pickings_loaded(self.picking1 | self.picking2)
        )
        #   'on_dock' key contains picking3
        self.assertEqual(on_dock, self.service.data.pickings(self.picking3))

    def test_loading_list_shipment_planned_fully_loaded(self):
        """Get the loading list of a planned shipment fully loaded."""
        # Plan some content in the shipment
        self._plan_records_in_shipment(self.shipment, self.pickings.move_lines)
        # Load everything
        self.pickings._load_in_shipment(self.shipment)
        # Get the loading list
        response = self.service.dispatch(
            "loading_list", params={"shipment_advice_id": self.shipment.id}
        )
        self.assert_response_loading_list(response, self.shipment)
        # Check returned content
        lading = response["data"]["loading_list"]["lading"]
        on_dock = response["data"]["loading_list"]["on_dock"]
        #   'lading' key contains picking1 and picking2
        self.assertEqual(lading, self.service.data.pickings_loaded(self.pickings))
        #   'on_dock' key is empty
        self.assertFalse(on_dock)

    def test_loading_list_shipment_not_planned_loaded_same_carrier_provider(self):
        """Get the loading list of an unplanned shipment with some content loaded.

        All deliveries are sharing the same carrier provider.
        """
        # Put the same carrier provider on all deliveries to get the unloaded
        # one in the returned result
        carrier1 = self.env.ref("delivery.delivery_carrier")
        carrier2 = self.env.ref("delivery.normal_delivery_carrier")
        (carrier1 | carrier2).sudo().delivery_type = "base_on_rule"
        self.picking1.carrier_id = carrier1
        self.picking2.carrier_id = self.picking3.carrier_id = carrier2
        # Load some content
        #   - part of picking1
        move_line_d = self.picking1.move_line_ids.filtered(
            lambda ml: ml.product_id == self.product_d
        )
        move_line_d._load_in_shipment(self.shipment)
        #   - all content of picking2
        self.picking2._load_in_shipment(self.shipment)
        #   - nothing from picking3
        # Get the loading list
        response = self.service.dispatch(
            "loading_list", params={"shipment_advice_id": self.shipment.id}
        )
        self.assert_response_loading_list(response, self.shipment)
        # Check returned content
        lading = response["data"]["loading_list"]["lading"]
        on_dock = response["data"]["loading_list"]["on_dock"]
        #   'lading' key contains picking1 and picking2
        self.assertEqual(
            lading, self.service.data.pickings_loaded(self.picking1 | self.picking2)
        )
        #   'on_dock' key contains at least picking3
        on_dock_picking_ids = [d["id"] for d in on_dock]
        self.assertIn(self.picking3.id, on_dock_picking_ids)
        self.assertNotIn(self.picking1.id, on_dock_picking_ids)
        self.assertNotIn(self.picking2.id, on_dock_picking_ids)

    def test_loading_list_shipment_not_planned_loaded_different_carrier_provider(self):
        """Get the loading list of an unplanned shipment with some content loaded.

        Deliveries loaded have the same carrier provider while the delivery still
        on dock have a different one, so it won't be listed as an available
        delivery to load in the current shipment.
        """
        # Put the same carrier provider on loaded deliveries
        carrier1 = self.env.ref("delivery.delivery_carrier")
        carrier1.sudo().delivery_type = "base_on_rule"
        self.picking1.carrier_id = self.picking2.carrier_id = carrier1
        # Put a different carrier provider on the unloaded one
        carrier2 = self.env.ref("delivery.normal_delivery_carrier")
        carrier2.sudo().delivery_type = "fixed"
        self.picking3.carrier_id = carrier2
        # Load some content
        #   - part of picking1
        move_line_d = self.picking1.move_line_ids.filtered(
            lambda ml: ml.product_id == self.product_d
        )
        move_line_d._load_in_shipment(self.shipment)
        #   - all content of picking2
        self.picking2._load_in_shipment(self.shipment)
        #   - nothing from picking3
        #     (in fact it's impossible to load it because the carrier provider
        #      is different)
        # Get the loading list
        response = self.service.dispatch(
            "loading_list", params={"shipment_advice_id": self.shipment.id}
        )
        self.assert_response_loading_list(response, self.shipment)
        # Check returned content
        lading = response["data"]["loading_list"]["lading"]
        on_dock = response["data"]["loading_list"]["on_dock"]
        #   'lading' key contains picking1 and picking2
        self.assertEqual(
            lading, self.service.data.pickings_loaded(self.picking1 | self.picking2)
        )
        #   'on_dock' key contains at least picking3
        on_dock_picking_ids = [d["id"] for d in on_dock]
        self.assertNotIn(self.picking3.id, on_dock_picking_ids)
        self.assertNotIn(self.picking1.id, on_dock_picking_ids)
        self.assertNotIn(self.picking2.id, on_dock_picking_ids)
