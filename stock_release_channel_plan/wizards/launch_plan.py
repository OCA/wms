# Copyright 2023 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class StockReleaseChannelPlanWizardLaunch(models.TransientModel):
    _name = "stock.release.channel.plan.wizard.launch"
    _description = "Stock Release Channel Plan Launch Wizard"

    def _default_plan_id(self):
        if (
            self.env.context.get("active_model")
            == "stock.release.channel.preparation.plan"
        ):
            return self.env.context.get("active_id")
        return False

    preparation_plan_id = fields.Many2one(
        "stock.release.channel.preparation.plan",
        required=True,
        default=lambda s: s._default_plan_id(),
    )

    @api.model
    def _action_launch(self, channels):
        channels.filtered("is_action_unlock_allowed").action_unlock()

        channels_to_wakeup = channels.filtered("is_action_wake_up_allowed")
        channels_to_wakeup.action_wake_up()

    def action_launch(self):
        self.ensure_one()
        channels_to_launch = self.preparation_plan_id._get_channels_to_launch()
        self._action_launch(channels_to_launch)
        action = self.env["ir.actions.actions"]._for_xml_id(
            "stock_release_channel.stock_release_channel_act_window"
        )
        action["context"] = {"search_default_filter_open": True}
        return action
