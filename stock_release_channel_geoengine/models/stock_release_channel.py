# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo import fields, models

from odoo.addons.base_geoengine.fields import GeoMultiPolygon

_logger = logging.getLogger(__name__)


class StockReleaseChannel(models.Model):

    _inherit = "stock.release.channel"

    restrict_to_delivery_zone = fields.Boolean()
    delivery_zone = GeoMultiPolygon()
