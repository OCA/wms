# Copyright 2020 Camptocamp
# License OPL-1

import datetime
import logging
import time

import dateutil
from pytz import timezone

from odoo import _, api, exceptions, fields, models
from odoo.tools.safe_eval import safe_eval, test_python_expr

_logger = logging.getLogger(__name__)


class StockReleaseChannel(models.Model):
    _name = "stock.release.channel"
    _description = "Stock Release Channels"
    _order = "sequence, id"

    DEFAULT_PYTHON_CODE = (
        "# Available variables:\n"
        "#  - env: Odoo Environment on which the action is triggered\n"
        "#  - records: pickings to filter\n"
        "#  - time, datetime, dateutil, timezone: useful Python libraries\n"
        "#\n"
        "# By default, all pickings are kept.\n"
        "# To filter a selection of pickings, assign: pickings = ...\n\n\n\n\n"
    )

    name = fields.Char(required=True)
    sequence = fields.Integer(default=lambda self: self._default_sequence())
    color = fields.Integer()
    rule_domain = fields.Char(
        string="Domain",
        default=[],
        help="Domain based on Transfers, filter for entering the channel.",
    )
    code = fields.Text(
        string="Python Code",
        groups="base.group_system",
        default=DEFAULT_PYTHON_CODE,
        help="Write Python code to filter out pickings.",
    )
    active = fields.Boolean(default=True)

    picking_ids = fields.One2many(
        string="Transfers",
        comodel_name="stock.picking",
        inverse_name="release_channel_id",
    )

    # beware not to store any value which can be changed by concurrent
    # stock.picking (e.g. the state cannot be stored)

    count_picking_all = fields.Integer(
        string="All Transfers", compute="_compute_picking_count"
    )
    count_picking_release_ready = fields.Integer(
        string="Release Ready Transfers", compute="_compute_picking_count"
    )
    count_picking_released = fields.Integer(
        string="Released Transfers", compute="_compute_picking_count"
    )
    count_picking_assigned = fields.Integer(
        string="Available Transfers", compute="_compute_picking_count"
    )
    count_picking_waiting = fields.Integer(
        string="Waiting Transfers", compute="_compute_picking_count"
    )
    count_picking_late = fields.Integer(
        string="Late Transfers", compute="_compute_picking_count"
    )
    count_picking_priority = fields.Integer(
        string="Priority Transfers", compute="_compute_picking_count"
    )
    count_picking_done = fields.Integer(
        string="Transfers Done Today", compute="_compute_picking_count"
    )

    count_move_all = fields.Integer(
        string="All Moves (Estimate)", compute="_compute_picking_count"
    )
    count_move_release_ready = fields.Integer(
        string="Release Ready Moves (Estimate)", compute="_compute_picking_count"
    )
    count_move_released = fields.Integer(
        string="Released Moves (Estimate)", compute="_compute_picking_count"
    )
    count_move_assigned = fields.Integer(
        string="Available Moves (Estimate)", compute="_compute_picking_count"
    )
    count_move_waiting = fields.Integer(
        string="Waiting Moves (Estimate)", compute="_compute_picking_count"
    )
    count_move_late = fields.Integer(
        string="Late Moves (Estimate)", compute="_compute_picking_count"
    )
    count_move_priority = fields.Integer(
        string="Priority Moves (Estimate)", compute="_compute_picking_count"
    )
    count_move_done = fields.Integer(
        string="Moves Done Today (Estimate)", compute="_compute_picking_count"
    )

    last_done_picking_id = fields.Many2one(
        string="Last Done Transfer",
        comodel_name="stock.picking",
        compute="_compute_last_done_picking",
    )
    last_done_picking_name = fields.Char(compute="_compute_last_done_picking")
    last_done_picking_date_done = fields.Datetime(compute="_compute_last_done_picking")

    def _field_picking_domains(self):
        return {
            "count_picking_all": [],
            "count_picking_release_ready": [
                ("release_ready", "=", True),
                # FIXME not TZ friendly
                (
                    "scheduled_date",
                    "<",
                    fields.Datetime.now().replace(hour=23, minute=59),
                ),
            ],
            "count_picking_released": [
                ("need_release", "=", False),
                ("state", "in", ("assigned", "waiting", "confirmed")),
            ],
            "count_picking_assigned": [("state", "=", "assigned")],
            "count_picking_waiting": [
                ("need_release", "=", False),
                ("state", "in", ("waiting", "confirmed")),
            ],
            "count_picking_late": [
                ("scheduled_date", "<", fields.Datetime.now()),
                ("state", "in", ("assigned", "waiting", "confirmed")),
                ("need_release", "=", False),
            ],
            "count_picking_priority": [
                ("priority", ">", "1"),
                ("state", "in", ("assigned", "waiting", "confirmed")),
                ("need_release", "=", False),
            ],
            "count_picking_done": [
                ("state", "=", "done"),
                ("date_done", ">", fields.Datetime.now().replace(hour=0, minute=0)),
            ],
        }

    # TODO maybe we have to do raw SQL to include the picking + moves counts in
    # a single query
    def _compute_picking_count(self):
        domains = self._field_picking_domains()
        picking_ids_per_field = {}
        for field, domain in domains.items():
            data = self.env["stock.picking"].read_group(
                domain + [("release_channel_id", "in", self.ids)],
                ["release_channel_id", "picking_ids:array_agg(id)"],
                ["release_channel_id"],
            )
            count = {
                row["release_channel_id"][0]: row["release_channel_id_count"]
                for row in data
                if row["release_channel_id"]
            }

            picking_ids_per_field.update(
                {
                    (row["release_channel_id"][0], field): row["picking_ids"]
                    for row in data
                    if row["release_channel_id"]
                }
            )

            for record in self:
                record[field] = count.get(record.id, 0)

        all_picking_ids = [
            pid for picking_ids in picking_ids_per_field.values() for pid in picking_ids
        ]
        data = self.env["stock.move"].read_group(
            # TODO for now we do estimates, later we may improve the domains per
            # field, but now we can run one sql query on stock.move for all fields
            [("picking_id", "in", all_picking_ids), ("state", "!=", "cancel")],
            ["picking_id"],
            ["picking_id"],
        )
        move_count = {
            row["picking_id"][0]: row["picking_id_count"]
            for row in data
            if row["picking_id"]
        }
        for field, __ in domains.items():
            move_field = field.replace("picking", "move")
            for record in self:
                picking_ids = picking_ids_per_field.get((record.id, field), [])
                move_estimate = sum(
                    move_count.get(picking_id, 0) for picking_id in picking_ids
                )
                record[move_field] = move_estimate

    # TODO this duplicated with shopfloor_kanban
    def _compute_last_done_picking(self):
        for channel in self:
            # TODO we have one query per channel, could be better
            domain = self._field_picking_domains()["count_picking_done"]
            domain += [("release_channel_id", "=", channel.id)]
            picking = self.env["stock.picking"].search(
                domain, limit=1, order="date_done DESC"
            )
            channel.last_done_picking_id = picking
            channel.last_done_picking_name = picking.name
            channel.last_done_picking_date_done = picking.date_done

    def _default_sequence(self):
        default_channel = self.env.ref(
            "stock_release_channel.stock_release_channel_default",
            raise_if_not_found=False,
        )
        domain = []
        if default_channel:
            domain = [("id", "!=", default_channel.id)]
        maxrule = self.search(domain, order="sequence desc", limit=1)
        if maxrule:
            return maxrule.sequence + 10
        else:
            return 0

    @api.constrains("code")
    def _check_python_code(self):
        for action in self.sudo().filtered("code"):
            msg = test_python_expr(expr=action.code.strip(), mode="exec")
            if msg:
                raise exceptions.ValidationError(msg)

    def _prepare_domain(self):
        domain = safe_eval(self.rule_domain) or []
        return domain

    def assign_release_channel(self, pickings):
        pickings = pickings.filtered(
            lambda picking: picking.need_release
            and picking.state not in ("cancel", "done")
        )
        if not pickings:
            return
        # do a single query rather than one for each rule*picking
        for channel in self.search([]):
            domain = channel._prepare_domain()

            if domain:
                current = pickings.filtered_domain(domain)
            else:
                current = pickings

            if not current:
                continue

            if channel.code:
                current = channel._eval_code(current)

            if not current:
                continue

            current.release_channel_id = channel

            pickings -= current
            if not pickings:
                break

        if pickings:
            # by this point, all pickings should have been assigned
            _logger.warning(
                "%s transfers could not be assigned to a channel,"
                " you should add a final catch-all rule",
                len(pickings),
            )
        return True

    def _eval_context(self, pickings):
        """Prepare the context used when for the python rule evaluation

        :returns: dict -- evaluation context given to (safe_)safe_eval
        """
        eval_context = {
            "uid": self.env.uid,
            "user": self.env.user,
            "time": time,
            "datetime": datetime,
            "dateutil": dateutil,
            "timezone": timezone,
            # orm
            "env": self.env,
            # record
            "self": self,
            "pickings": pickings,
        }
        return eval_context

    def _eval_code(self, pickings):
        expr = self.code.strip()
        eval_context = self._eval_context(pickings)
        try:
            safe_eval(expr, eval_context, mode="exec", nocopy=True)
        except Exception as err:
            raise exceptions.UserError(
                _("Error when evaluating the channel's code:\n %s \n(%s)")
                % (self.name, err)
            )
        # normally "pickings" is always set as we set it in the eval context,
        # but let assume the worst case with someone using "del pickings"
        return eval_context.get("pickings", self.env["stock.picking"].browse())

    def action_picking_all(self):
        return self._action_picking_for_field(
            "count_picking_all", context={"search_default_release_ready": 1}
        )

    def action_picking_release_ready(self):
        return self._action_picking_for_field("count_picking_release_ready")

    def action_picking_released(self):
        return self._action_picking_for_field("count_picking_released")

    def action_picking_assigned(self):
        return self._action_picking_for_field("count_picking_assigned")

    def action_picking_waiting(self):
        return self._action_picking_for_field("count_picking_waiting")

    def action_picking_late(self):
        return self._action_picking_for_field("count_picking_late")

    def action_picking_priority(self):
        return self._action_picking_for_field("count_picking_priority")

    def action_picking_done(self):
        return self._action_picking_for_field("count_picking_done")

    def _action_picking_for_field(self, field_domain, context=None):
        domain = self._field_picking_domains()[field_domain]
        domain += [("release_channel_id", "in", self.ids)]
        pickings = self.env["stock.picking"].search(domain)
        field_descr = self._fields[field_domain]._description_string(self.env)
        return self._build_action(
            "stock_available_to_promise_release.stock_picking_release_action",
            pickings,
            field_descr,
            context=context,
        )

    def action_move_all(self):
        return self._action_move_for_field(
            "count_picking_all", context={"search_default_release_ready": 1}
        )

    def action_move_release_ready(self):
        return self._action_move_for_field(
            "count_picking_release_ready", context={"search_default_release_ready": 1}
        )

    def action_move_released(self):
        return self._action_move_for_field("count_picking_released")

    def action_move_assigned(self):
        return self._action_move_for_field("count_picking_assigned")

    def action_move_waiting(self):
        return self._action_move_for_field("count_picking_waiting")

    def action_move_late(self):
        return self._action_move_for_field("count_picking_late")

    def action_move_priority(self):
        return self._action_move_for_field("count_picking_priority")

    def action_move_done(self):
        return self._action_move_for_field("count_picking_done")

    def _action_move_for_field(self, field_domain, context=None):
        domain = self._field_picking_domains()[field_domain]
        domain += [("release_channel_id", "in", self.ids)]
        pickings = self.env["stock.picking"].search(domain)
        field_descr = self._fields[field_domain]._description_string(self.env)
        xmlid = "stock_available_to_promise_release.stock_move_release_action"
        action = self.env.ref(xmlid).read()[0]
        action["display_name"] = "{} ({})".format(
            ", ".join(self.mapped("display_name")), field_descr
        )
        action["context"] = context if context else {}
        action["domain"] = [("picking_id", "in", pickings.ids)]
        return action

    def _build_action(self, xmlid, records, description, context=None):
        action = self.env.ref(xmlid).read()[0]
        action["display_name"] = "{} ({})".format(
            ", ".join(self.mapped("display_name")), description
        )
        action["context"] = context if context else None
        action["domain"] = [("id", "in", records.ids)]
        return action

    def action_picking_all_related(self):
        """Open all chained transfers for released deliveries"""
        domain = self._field_picking_domains()["count_picking_released"]
        domain += [("release_channel_id", "=", self.id)]
        released = self.env["stock.picking"].search(domain)
        all_related_ids = set()
        current_moves = released.move_lines
        while current_moves:
            all_related_ids |= set(current_moves.picking_id.ids)
            current_moves = current_moves.move_orig_ids

        all_related = self.env["stock.picking"].browse(all_related_ids)

        return self._build_action(
            "stock.action_picking_tree_all",
            all_related,
            _("All Related Transfers"),
            context={"search_default_available": 1, "search_default_picking_type": 1},
        )

    # TODO extract to glue module with ddmrp
    def action_ddmrp_buffer(self):
        domain = self._field_picking_domains()["count_picking_released"]
        domain += [("release_channel_id", "=", self.id)]
        released = self.env["stock.picking"].search(domain)
        buffers = released.move_lines.product_id.buffer_ids
        return self._build_action(
            "ddmrp.action_stock_buffer", buffers, _("DDMRP Buffers")
        )

    # TODO almost duplicated with stock_picking_type_kanban
    def get_action_picking_form(self):
        self.ensure_one()
        action = self.env.ref("stock.action_picking_form").read()[0]
        action["context"] = {}
        if not self.last_done_picking_id:
            raise exceptions.UserError(
                _("Channel {} has no validated transfer yet.").format(name=self.name)
            )
        action["res_id"] = self.last_done_picking_id.id
        return action
