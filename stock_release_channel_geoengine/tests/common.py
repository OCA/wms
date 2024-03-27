# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from shapely.geometry.multipolygon import MultiPolygon
from shapely.geometry.polygon import Point, Polygon

from odoo.addons.stock_release_channel.tests.common import ChannelReleaseCase


class TestStockReleaseChannelGeoengineCommon(ChannelReleaseCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.multipolygon = MultiPolygon(
            [
                Polygon(
                    [
                        [3.157493, 50.776306],
                        [3.157075, 50.776594],
                        [3.156601, 50.777019],
                        [3.156126, 50.777434],
                        [3.155595, 50.777824],
                    ]
                )
            ]
        )
        cls.empty_multipolygon = MultiPolygon([Polygon()])
        cls.point1 = Point(3.157493, 50.776306)
        cls.point2 = Point(3.157075, 50.776594)
        cls.point3 = Point(3.156601, 50.777019)
        cls.outside_point = Point(708922.106609628, 5870795.4022844)
        cls.channel = cls.env.ref("stock_release_channel.stock_release_channel_default")
        cls.channel.delivery_zone = cls.multipolygon
        cls.channel.restrict_to_delivery_zone = True
        cls.pickings = cls.picking + cls.picking2 + cls.picking3
        cls.pickings.write({"release_channel_id": False})
