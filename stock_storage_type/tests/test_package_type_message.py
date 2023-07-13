# Copyright 2022 ACSONE SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo.tests import TransactionCase


class TestStorageType(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

        cls.stock_location = cls.env.ref("stock.stock_location_stock")
        cls.pallets_location_storage_type = cls.env.ref(
            "stock_storage_type.location_storage_type_pallets"
        )
        cls.pallets_uk_location_storage_type = cls.env.ref(
            "stock_storage_type.location_storage_type_pallets_uk"
        )
        cls.cardboxes_location_storage_type = cls.env.ref(
            "stock_storage_type.location_storage_type_cardboxes"
        )
        cls.cardboxes_stock = cls.env.ref("stock_storage_type.stock_location_cardboxes")
        cls.cardboxes_bin_1 = cls.env.ref(
            "stock_storage_type.stock_location_cardboxes_bin_1"
        )
        cls.cardboxes_bin_2 = cls.env.ref(
            "stock_storage_type.stock_location_cardboxes_bin_2"
        )
        cls.cardboxes_bin_3 = cls.env.ref(
            "stock_storage_type.stock_location_cardboxes_bin_3"
        )
        cls.cardboxes_bin_4 = cls.env.ref(
            "stock_storage_type.stock_location_cardboxes_bin_4"
        )
