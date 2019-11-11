# Copyright 2019 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class StockLocationStorageType(models.Model):

    _inherit = 'stock.location.storage.type'

    only_empty = fields.Boolean(
        help="If checked, moves to the destination location will only be "
             "allowed if there are not any existing quant nor planned move on "
             "this location")
    do_not_mix_lots = fields.Boolean(
        help="If checked, moves to the destination location will only be "
             "allowed if the location contains product of the same "
             "lot."
    )
    do_not_mix_products = fields.Boolean(
        help="If checked, moves to the destination location will only be "
             "allowed if the location contains the same product."
    )
    # max_height = fields.Boolean(
    #     help="If checked, moves to the destination location will only be "
    #          "allowed if the packaging height is lower than this maximum."
    # )
    # max_height_value = fields.Float()
    # max_volume = fields.Boolean(
    #     help="If checked, moves to the destination location will only be "
    #          "allowed if the packaging volume is lower than this maximum."
    # )
    # max_volume_value = fields.Float()

    @api.constrains('only_empty', 'do_not_mix_lots', 'do_not_mix_products')
    def _check_empty_mix(self):
        for location_storage_type in self:
            if (
                location_storage_type.only_empty and (
                    location_storage_type.do_not_mix_lots or
                    location_storage_type.do_not_mix_products
                )
            ):
                raise ValidationError(_(
                    "You cannot set 'Do not mix lots' or 'Do not mix products'"
                    " with 'Only empty' constraint."
                ))

    @api.constrains('do_not_mix_lots', 'do_not_mix_products')
    def _check_do_not_mix(self):
        for location_storage_type in self:
            if (
                location_storage_type.do_not_mix_lots and
                not location_storage_type.do_not_mix_products
            ):
                raise ValidationError(_(
                    "You cannot set 'Do not mix lots' without setting 'Do not"
                    " mix products' constraint."
                ))

    @api.onchange('do_not_mix_products')
    def _onchange_do_not_mix_products(self):
        if not self.do_not_mix_products:
            self.do_not_mix_lots = False

    # @api.constrains('max_height', 'max_height_value', 'max_height_uom')
    # def _check_max_height(self):
    #     pass
    #     # A value must be specified
    #
    # @api.constrains('max_volume', 'max_volume_value', 'max_volume_uom')
    # def _check_max_volume(self):
    #     pass
    #     # A value must be specified
