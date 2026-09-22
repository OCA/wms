# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
# pylint: disable=missing-return
from odoo_test_helper import FakeModelLoader

from odoo.exceptions import UserError

from odoo.addons.shopfloor_base.tests.common import CommonCase as BaseCommonCase


class StockIssueStrategyCommonCase(BaseCommonCase):
    @classmethod
    def setUpClassVars(cls, *args, **kwargs):
        super().setUpClassVars(*args, **kwargs)
        cls.menu = cls.env.ref("shopfloor.shopfloor_menu_demo_cluster_picking")

    @classmethod
    def setUpClassBaseData(cls, *args, **kwargs):
        super().setUpClassBaseData(*args, **kwargs)

    def setUp(self):
        super().setUp()
        self.service = self.get_service(
            "cluster_picking", menu=self.menu, profile=self.profile
        )

    def test_scenario_has_stock_issue_strategy_option(self):
        self.assertTrue(self.menu.scenario_id.has_option("uses_stock_issue"))


class TestStockIssueStrategyNoExtension(StockIssueStrategyCommonCase):
    def test_stock_issue_strategy_is_not_possible(self):
        self.assertFalse(self.menu.stock_issue_strategy_is_possible)


class TestStockIssueStrategy(StockIssueStrategyCommonCase):
    @classmethod
    def setUpClass(cls):
        try:
            super().setUpClass()
        except BaseException:
            # ensure that the registry is restored in case of error in setUpClass
            # since tearDownClass is not called in this case and our _load_test_models
            # loads fake models
            if hasattr(cls, "loader"):
                cls.loader.restore_registry()
            raise

    @classmethod
    def _load_test_models(cls):
        cls.loader = FakeModelLoader(cls.env, cls.__module__)
        cls.loader.backup_registry()
        from .models import ShopfloorMenuFakeStockIssue

        cls.loader.update_registry((ShopfloorMenuFakeStockIssue,))

    @classmethod
    def tearDownClass(cls):
        cls.loader.restore_registry()
        super().tearDownClass()

    @classmethod
    def setUpClassBaseData(cls, *args, **kwargs):
        super().setUpClassBaseData(*args, **kwargs)
        cls._load_test_models()

    def test_stock_issue_strategy_is_possible(self):
        self.assertTrue(self.menu.stock_issue_strategy_is_possible)

    def test_call_stock_issue_strategy_witout_implementation_raises(self):
        self.menu.sudo().stock_issue_strategy = "test"
        with self.assertRaisesRegex(UserError, "Invalid stock issue strategy"):
            self.service.inventory.handle_stock_issue(
                object(), object(), object(), object(), object()
            )
