# Copyright 2025 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)

from freezegun import freeze_time

from odoo import fields

from .common import (
    FakeModelLoader,
    ReleaseChannelCase,
    StockReleaseChannelDeliveryDateCommon,
    TransactionCase,
)

to_datetime = fields.Datetime.to_datetime


class TestReleaseChannelDeliveryDateFake(StockReleaseChannelDeliveryDateCommon):
    @freeze_time("2025-01-02 10:00:00")
    def test_delivery_date(self):
        """Test generator on channel object"""
        now = fields.Datetime.now()
        dt = self.channel._get_earliest_delivery_date(self.partner, now)
        self.assertEqual(dt, to_datetime("2025-01-04 10:00:00"))


class TestReleaseChannelDeliveryDateImpossible(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.loader = FakeModelLoader(cls.env, cls.__module__)
        cls.loader.backup_registry()
        from .models.generator_test_impossible import StockReleaseChannel

        cls.loader.update_registry((StockReleaseChannel,))

        cls.partner = cls.env.ref("base.main_partner")
        cls.channel = cls.env.ref("stock_release_channel.stock_release_channel_default")

    @classmethod
    def tearDownClass(cls):
        cls.loader.restore_registry()
        return super().tearDownClass()

    @freeze_time("2025-01-02 10:00:00")
    def test_delivery_date(self):
        """Test generator on channel object"""
        now = fields.Datetime.now()
        dt = self.channel._get_earliest_delivery_date(self.partner, now)
        self.assertEqual(dt, None)


class TestReleaseChannelDeliveryDate(ReleaseChannelCase):
    def test_compute_delivery_date(self):
        """Test delivery date computes with registered generators

        This test will run with other modules loaded.
        """
        now = fields.Datetime.now()
        partner = self.env.ref("base.main_partner")
        self.default_channel._get_earliest_delivery_date(partner, now)
