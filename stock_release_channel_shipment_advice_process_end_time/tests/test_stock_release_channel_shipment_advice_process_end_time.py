# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from datetime import datetime

from freezegun import freeze_time

from odoo.addons.stock_release_channel.tests.common import ChannelReleaseCase


class TestStockReleaseChannelShipmentAdviceProcessEndTime(ChannelReleaseCase):
    @classmethod
    @freeze_time("2023-02-15 10:30:00")
    def setUpClass(cls):
        super().setUpClass()
        output_loc = cls.channel.picking_ids.move_ids.location_id
        cls._update_qty_in_location(output_loc, cls.product1, 100)
        cls._update_qty_in_location(output_loc, cls.product2, 100)
        cls.channel.picking_ids.move_ids.write({"procure_method": "make_to_stock"})
        cls.channel.picking_ids.action_assign()
        cls.date_ref = datetime.now()
        cls.channel.process_end_date = cls.date_ref
        cls.channel.process_end_time = 10.5
        cls.channel.shipment_planning_method = "simple"

    def test_plan_shipment_simple_delay_on_warehouse_arrival_date(self):
        """
        delay:
        - warehouse: 20mn
        - channel: 0mn
        """
        self.wh.release_channel_shipment_advice_arrival_delay = 20
        self.channel.warehouse_id = self.wh
        self.channel.button_plan_shipments()
        shipment_advice = self.channel.shipment_advice_ids
        self.assertEqual(
            shipment_advice.arrival_date, self.date_ref.replace(hour=10, minute=50)
        )

    def test_plan_shipment_simple_delay_on_channel_arrival_date(self):
        """
        delay:
        - warehouse: 20mn
        - channel: 30mn
        """
        self.wh.release_channel_shipment_advice_arrival_delay = 20
        self.channel.warehouse_id = self.wh
        self.channel.shipment_advice_arrival_delay = 30

        self.channel.button_plan_shipments()
        shipment_advice = self.channel.shipment_advice_ids
        self.assertEqual(
            shipment_advice.arrival_date, self.date_ref.replace(hour=11, minute=0)
        )
