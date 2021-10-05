# -*- coding: utf-8 -*-
# Copyright 2021 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import math

from odoo import _, api, fields, models, tools
from odoo.exceptions import UserError


class MakePickingBatch(models.TransientModel):

    _name = "make.picking.batch"

    picking_type_ids = fields.Many2many(
        comodel_name="stock.picking.type",
        relation="make_picking_batch_picking_type_rel",
        column1="batch_id",
        column2="picking_type_id",
        string="Default operation types",
        help="Default list of eligible operation types when creating a batch transfer",
    )
    stock_device_type_ids = fields.Many2many(
        comodel_name="stock.device.type",
        relation="make_picking_batch_device_type_rel",
        column1="batch_id",
        column2="device_type_id",
        string="Default device types",
        help="Default list of eligible device types when creating a batch transfer",
    )
    user_id = fields.Many2one("res.users", string="Responsible")
    maximum_number_of_preparation_lines = fields.Integer(
        default=20,
        string="Maximum number of preparation lines for the batch",
        required=True,
    )

    @api.multi
    def create_batch(self):
        self.ensure_one()
        batch = self._create_batch()
        action = {
            "type": "ir.actions.act_window",
            "name": batch.name,
            "res_model": "stock.picking.wave",
            "res_id": batch.id,
            "view_mode": "form",
            "target": "current",
        }
        return action

    def _search_pickings(self, user=None):
        domain = self._search_pickings_domain(user=user)
        pickings = self.env["stock.picking"].search(domain)
        return pickings

    def _search_pickings_domain(self, user=None):
        domain = [
            ("picking_type_id", "in", self.picking_type_ids.ids),
            ("state", "in", ("partially_available", "assigned")),
            ("wave_id", "=", False),
            ("user_id", "=", user.id if user else False),
        ]
        if not user:
            domain.append(("printed", "=", False))
        return domain

    def _candidates_pickings_to_batch(self, user=None):
        candidates_pickings = self._search_pickings(user=user)
        if not candidates_pickings:
            candidates_pickings = self._search_pickings()
        return candidates_pickings

    def _compute_device_to_use(self, first_picking_to_batch):
        recommended_device = None
        available_devices = self.stock_device_type_ids.sorted(
            lambda d: d.sequence
        )
        picking_volume = self._picking_volume(first_picking_to_batch)
        for device in available_devices:
            if self._volume_condition_for_device_choice(
                device.min_volume, picking_volume, device.max_volume
            ):
                recommended_device = device
                break
        return recommended_device

    def _volume_condition_for_device_choice(
        self, min_volume, picking_volume, max_volume
    ):
        lower_bound = tools.float_compare(picking_volume, min_volume, 2) >= 0
        upper_bound = tools.float_compare(max_volume, picking_volume, 2) >= 0
        return lower_bound and upper_bound

    def _picking_nbr_lines(self, picking):
        return len(picking.pack_operation_ids)


    def _exclude_first_unfit_pickings_on_device(self, candidate_pickings, start_picking):
        ids = candidate_pickings.mapped("id")
        start_index = ids.index(start_picking.id)
        ids = ids[start_index:]
        pickings = self.env["stock.picking"].browse(ids)
        return pickings

    def _create_batch(self):
        user = self.user_id if self.user_id else self.env.user
        device = None
        candidates_pickings_to_batch = self._candidates_pickings_to_batch(user=user)
        if not candidates_pickings_to_batch:
            raise UserError(_("no candidate pickings to batch"))

        for picking in candidates_pickings_to_batch:
            device = self._compute_device_to_use(picking)
            if device:
                break
        if not device:
            raise UserError(_("no device found for batch picking"))

        candidates_pickings_to_batch = self._exclude_first_unfit_pickings_on_device(candidates_pickings_to_batch, picking)
        selected_pickings, unselected_pickings = self._apply_limits(
            candidates_pickings_to_batch,
            device
        )
        vals = self._create_batch_values(user, device, selected_pickings)
        batch = self.env["stock.picking.wave"].create(vals)
        self._assign_operator_on_selected_pickings(batch, user)
        return batch

    def _check_number_of_available_bins(self, first_picking, device):
        # If only one bin available: only one picking
        picking = self.env["stock.picking"].browse()
        if device.nbr_bins == 1:
            picking = first_picking
        return picking

    def _check_first_picking(self, first_picking, device):
        # If first picking is already breaking one rule : batch of one picking
        picking = self.env["stock.picking"].browse()
        first_picking.total_weight_batch_picking = self._picking_weight(first_picking)
        first_picking.total_volume_batch_picking = self._picking_volume(first_picking)
        first_picking.nbr_picking_lines = self._picking_nbr_lines(first_picking)
        volume_per_bin = device.max_volume / device.nbr_bins
        first_picking.nbr_bins_batch_picking = math.ceil(first_picking.total_volume_batch_picking / volume_per_bin)
        is_overweighted = tools.float_compare(first_picking.total_weight_batch_picking, device.max_weight, 1) == 1
        is_oversized = tools.float_compare(first_picking.total_volume_batch_picking, device.max_volume, 1) == 1
        is_big_order = (
            tools.float_compare(
                first_picking.nbr_picking_lines, self.maximum_number_of_preparation_lines, 1
            )
            == 1
        )
        is_device_full = first_picking.nbr_bins_batch_picking > device.nbr_bins
        if is_overweighted or is_oversized or is_big_order or is_device_full:
            params = (first_picking.total_weight_batch_picking, first_picking.total_volume_batch_picking, first_picking.nbr_picking_lines, first_picking.nbr_bins_batch_picking)
            msg = "The first picking does not match the device you wanted to use"
            msg2 = "First picking needs: weight %s, volume %s, number of picking lines %s, number of bins %s" % params
            raise UserError(_(msg+"\n"+ msg2))
        
        return first_picking, volume_per_bin

    def _assign_operator_on_selected_pickings(self, batch, user):
        batch.picking_ids.write({"user_id": user.id})

    def _precision_weight(self):
        return self.env["decimal.precision"].precision_get("Product Unit of Measure")

    def _precision_volume(self):
        return max(
            6,
            self.env["decimal.precision"].precision_get("Product Unit of Measure") * 2,
        )

    def _apply_limits(self, pickings, device, max_pickings=0):
        """
        Once we have the candidates pickings for clustering, we need to decide when to stop
        the cluster (i.e.,  when to stop adding pickings in it)
        1) If we only have one bin available, only one picking is selected
        because we do not mix pickings in bins
        2) If the first candidate picking for clustering is breaking one condition
        (too voluminous or too heavy or too many lines in the picking or takes all the available bins)
        3) We add pickings in the cluster as long as the conditions are respected
        """
        selected_pickings = self.env["stock.picking"].browse()
        unselected_pickings = self.env["stock.picking"].browse()

        first_picking = fields.first(pickings)
        # 1) Check the number of bins available to create the cluster
        selected_pickings = self._check_number_of_available_bins(
            first_picking, device
        )
        if selected_pickings:
            return selected_pickings, unselected_pickings
        # 2) Check weither the first picking is breaking one condition or not
        first_picking, volume_per_bin = self._check_first_picking(
            first_picking, device
        )

        # 3) add pickings as long as conditions are respected
        # Initial conditions
        total_weight = 0.0
        total_volume = 0.0
        precision_weight = self._precision_weight()
        precision_volume = self._precision_volume()

        def gt(value1, value2, digits):
            """Return True if value1 is greater than value2"""
            return tools.float_compare(value1, value2, precision_digits=digits) == 1

        # Always take the first picking even if it doesn't fullfill the
        # weight/volume criteria. This allows to always process at least
        # one picking which won't be processed otherwise
        selected_pickings = first_picking
        available_nbr_bins =  device.nbr_bins - first_picking.nbr_bins_batch_picking

        # Add pickings to the first one as long as
        # - total volume is not outreached
        # - total weight is not outreached
        # - maximum number of preparation lines is not outreached
        # - numbers of bins available is greater than 0
        # - The device for the current picking is supposed to be
        # the same as the one for the first picking
        total_weight = first_picking.total_weight_batch_picking
        total_volume = first_picking.total_volume_batch_picking
        total_nbr_picking_lines = first_picking.nbr_picking_lines
        for picking in pickings[1:]:
            if max_pickings and len(selected_pickings) == max_pickings:
                # selected enough!
                break

            # Check that the picking can go on the selected device
            picking_device = self._compute_device_to_use(picking)
            different_device_for_current_picking = device != picking_device

            picking.total_weight_batch_picking = self._picking_weight(picking)
            picking.total_volume_batch_picking = self._picking_volume(picking)
            picking.nbr_picking_lines = self._picking_nbr_lines(picking)
            picking.nbr_bins_batch_picking = math.ceil(picking.total_volume_batch_picking / volume_per_bin)

            weight_limit_outreached = device.max_weight and gt(
                total_weight + picking.total_weight_batch_picking, device.max_weight, precision_weight
            )
            volume_limit_outreached = device.max_volume and gt(
                total_volume + picking.total_volume_batch_picking, device.max_volume, precision_volume
            )
            nbr_lines_limit_outreached = (
                self.maximum_number_of_preparation_lines
                and gt(
                    total_nbr_picking_lines + picking.nbr_picking_lines,
                    self.maximum_number_of_preparation_lines,
                    1,
                )
            )
            available_bins_outreached = available_nbr_bins - picking.nbr_bins_batch_picking < 0

            if not (
                weight_limit_outreached
                or volume_limit_outreached
                or nbr_lines_limit_outreached
                or available_bins_outreached
                or different_device_for_current_picking
            ):
                # All conditions are OK : we keep the picking in the cluster
                selected_pickings |= picking
                total_weight += picking.total_weight_batch_picking
                total_volume += picking.total_volume_batch_picking
                total_nbr_picking_lines += picking.nbr_picking_lines
                available_nbr_bins -= picking.nbr_bins_batch_picking
            else:
                # At least one condition KO : we discard the picking from the cluster
                unselected_pickings |= picking

        return selected_pickings, unselected_pickings

    def _picking_weight(self, picking):
        weight = 0.0
        for line in picking.move_lines:
            weight += line.product_id.get_total_weight_from_packaging(
                line.product_uom_qty
            )
        return weight

    def _picking_volume(self, picking):
        volume = 0.0
        for line in picking.move_lines:
            product = line.product_id
            packagings_with_volume = product.with_context(
                _packaging_filter=lambda p: p.volume
            ).product_qty_by_packaging(line.product_uom_qty)
            for packaging_info in packagings_with_volume:
                if packaging_info.get("is_unit"):
                    pack_volume = product.volume
                else:
                    packaging = self.env["product.packaging"].browse(
                        packaging_info["id"]
                    )
                    pack_volume = packaging.volume

                volume += pack_volume * packaging_info["qty"]
        return volume

    def _create_batch_values(self, user, device, pickings):
        return {
            "picking_ids": [(6, 0, pickings.ids)],
            "user_id": user.id,
            "state": "draft",
            "wave_weight":sum([picking.total_weight_batch_picking for picking in pickings]),
            "wave_volume":sum([picking.total_volume_batch_picking for picking in pickings]),
            "wave_nbr_bins":sum([picking.nbr_bins_batch_picking for picking in pickings]),
            "wave_nbr_lines":sum([picking.nbr_picking_lines for picking in pickings]),
            "picking_device_id": device.id if device else None,
        }
