# Copyright 2025 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from .common import SaleStockReleaseChannelCommon


class TestSaleStockReleaseChannel(SaleStockReleaseChannelCommon):
    def test_candidate_domain(self):
        """Test domain returns a value"""
        domain = self.so._release_channel_possible_candidate_domain_base
        self.assertIsInstance(domain, list)
