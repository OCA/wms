# Copyright 2020 Camptocamp
# Copyright 2022 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# Copyright 2023 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import logging
from collections import defaultdict
from copy import deepcopy

from pytz import timezone

from odoo import _, api, exceptions, fields, models
from odoo.osv.expression import NEGATIVE_TERM_OPERATORS
from odoo.tools.safe_eval import (
    datetime as safe_datetime,
    dateutil as safe_dateutil,
    safe_eval,
    test_python_expr,
    time as safe_time,
)

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
    release_forbidden = fields.Boolean(string="Forbid to release this channel")
    sequence = fields.Integer(default=lambda self: self._default_sequence())
    color = fields.Integer()
    warehouse_id = fields.Many2one(
        "stock.warehouse",
        string="Warehouse",
        index=True,
        help="Warehouse for which this channel is relevant",
    )
    picking_type_ids = fields.Many2many(
        "stock.picking.type",
        "stock_release_channel_warehouse_rel",
        "channel_id",
        "picking_type_id",
        string="Operation Types",
        domain="warehouse_id"
        " and [('warehouse_id', '=', warehouse_id), ('code', '=', 'outgoing')]"
        " or [('code', '=', 'outgoing')]",
    )
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
    release_mode = fields.Selection(
        [("batch", "Batch (Manual)")], required=True, default="batch"
    )
    batch_mode = fields.Selection(
        selection=[("max", "Max")],
        default="max",
        required=True,
        help="Max: release N transfers to have a configured max of X deliveries"
        " in progress.",
    )
    max_batch_mode = fields.Integer(
        string="Max Transfers to release",
        default=10,
        help="When clicking on the package icon, it releases X transfers minus "
        " on-going ones not shipped (X - Waiting)."
        " This field defines X.",
    )

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
    count_picking_full_progress = fields.Integer(
        string="Full Progress",
        compute="_compute_picking_count",
        help="The total number of pickings to achieve 100% of progress.",
    )

    picking_chain_ids = fields.Many2many(
        comodel_name="stock.picking",
        compute="_compute_picking_chain",
        help="All transfers required to bring goods to the deliveries.",
    )
    count_picking_chain = fields.Integer(
        string="All Related Transfers", compute="_compute_picking_chain"
    )
    count_picking_chain_in_progress = fields.Integer(
        string="In progress Related Transfers", compute="_compute_picking_chain"
    )
    count_picking_chain_done = fields.Integer(
        string="All Done Related Transfers", compute="_compute_picking_chain"
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
    state = fields.Selection(
        selection=[("open", "Open"), ("locked", "Locked"), ("asleep", "Asleep")],
        help="The state allows you to control the availability of the release channel.\n"
        "* Open: Manual and automatic picking assignment to the release is effective "
        "and release operations are allowed.\n "
        "* Locked: Release operations are forbidden. (Assignement processes are "
        "still working)\n"
        "* Asleep: Assigned pickings not processed are unassigned from the release "
        "channel.\n",
        default="asleep",
    )
    is_action_lock_allowed = fields.Boolean(
        compute="_compute_is_action_lock_allowed",
        help="Technical field to check if the " "action 'Lock' is allowed.",
    )
    is_action_unlock_allowed = fields.Boolean(
        compute="_compute_is_action_unlock_allowed",
        help="Technical field to check if the " "action 'Unlock' is allowed.",
    )
    is_action_sleep_allowed = fields.Boolean(
        compute="_compute_is_action_sleep_allowed",
        help="Technical field to check if the " "action 'Sleep' is allowed.",
    )
    is_action_wake_up_allowed = fields.Boolean(
        compute="_compute_is_action_wake_up_allowed",
        help="Technical field to check if the " "action 'Wake Up' is allowed.",
    )
    is_release_allowed = fields.Boolean(
        compute="_compute_is_release_allowed",
        search="_search_is_release_allowed",
        help="Technical field to check if the "
        "action 'Release Next Batch' is allowed.",
    )
    partner_ids = fields.Many2many(
        comodel_name="res.partner",
        relation="res_partner_stock_release_channel_rel",
        column1="channel_id",
        column2="partner_id",
        string="Partners",
        context={"active_test": False},
    )
    show_last_picking_done = fields.Boolean(
        compute="_compute_show_last_picking_done",
    )
    is_manual_assignment = fields.Boolean("Manual assignment")

    @api.depends("state")
    def _compute_is_action_lock_allowed(self):
        for rec in self:
            rec.is_action_lock_allowed = rec.state == "open"

    @api.depends("state")
    def _compute_is_action_unlock_allowed(self):
        for rec in self:
            rec.is_action_unlock_allowed = rec.state == "locked"

    @api.depends("state")
    def _compute_is_action_sleep_allowed(self):
        for rec in self:
            rec.is_action_sleep_allowed = rec.state in ("open", "locked")

    @api.depends("state")
    def _compute_is_action_wake_up_allowed(self):
        for rec in self:
            rec.is_action_wake_up_allowed = rec.state == "asleep"

    @api.depends("state", "release_forbidden")
    def _compute_is_release_allowed(self):
        for rec in self:
            rec.is_release_allowed = rec.state == "open" and not rec.release_forbidden

    def _compute_show_last_picking_done(self):
        for rec in self:
            rec.show_last_picking_done = (
                self.env.company.release_channel_show_last_picking_done
            )

    @api.model
    def _get_is_release_allowed_domain(self):
        return [("state", "=", "open"), ("release_forbidden", "=", False)]

    @api.model
    def _get_is_release_not_allowed_domain(self):
        return ["|", ("state", "!=", "open"), ("release_forbidden", "=", True)]

    @api.model
    def _search_is_release_allowed(self, operator, value):
        if "in" in operator:
            raise ValueError(f"Invalid operator {operator}")
        negative_op = operator in NEGATIVE_TERM_OPERATORS
        is_release_allowed = (value and not negative_op) or (not value and negative_op)
        domain = self._get_is_release_allowed_domain()
        if not is_release_allowed:
            domain = self._get_is_release_not_allowed_domain()
        return domain

    def _get_picking_to_unassign_domain(self):
        return [
            ("release_channel_id", "in", self.ids),
            ("state", "not in", ("done", "cancel")),
        ]

    @api.model
    def _get_picking_to_assign_domain(self):
        return [
            ("release_channel_id", "=", False),
            ("state", "not in", ("done", "cancel")),
            ("picking_type_id.code", "=", "outgoing"),
            ("need_release", "=", True),
        ]

    def _field_picking_domains(self):
        return {
            "all": [],
            "release_ready": [
                ("release_ready", "=", True),
                # FIXME not TZ friendly
                (
                    "scheduled_date",
                    "<",
                    fields.Datetime.now().replace(hour=23, minute=59),
                ),
            ],
            "released": [
                ("last_release_date", "!=", False),
                ("state", "in", ("assigned", "waiting", "confirmed")),
            ],
            "assigned": [
                ("last_release_date", "!=", False),
                ("state", "=", "assigned"),
            ],
            "waiting": [
                ("last_release_date", "!=", False),
                ("state", "in", ("waiting", "confirmed")),
            ],
            "late": [
                ("last_release_date", "!=", False),
                ("scheduled_date", "<", fields.Datetime.now()),
                ("state", "in", ("assigned", "waiting", "confirmed")),
            ],
            "priority": [
                ("last_release_date", "!=", False),
                ("priority", "=", "1"),
                ("state", "in", ("assigned", "waiting", "confirmed")),
            ],
            "done": [
                ("state", "=", "done"),
                ("date_done", ">", fields.Datetime.now().replace(hour=0, minute=0)),
            ],
        }

    @api.model
    def _get_picking_read_group_fields(self):
        "Additional fields to read on read_group of stock.pickings"
        return []

    @api.model
    def _get_picking_compute_fields(self):
        """This returns a list of tuples
        the first value of the tuple represents the prefix of computed field
        and the second value represents the field used to set the computed field"""
        return [("count", "release_channel_id_count")]

    @api.model
    def _get_move_read_group_fields(self):
        "Additional fields to read on read_group of stock.moves"
        return []

    @api.model
    def _get_move_compute_fields(self):
        """This returns a list of tuples
        the first value of the tuple represents the prefix of computed field
        and the second value represents the field used to set the computed field"""
        return [("count", "picking_id_count")]

    @api.model
    def _get_compute_field_name(self, prefix, name, domain_name):
        return f"{prefix}_{name}_{domain_name}"

    @api.model
    def _get_default_aggregate_values(self):
        picking_compute_fields = self._get_picking_compute_fields()
        move_compute_fields = self._get_move_compute_fields()
        default_values = {}
        for domain_name, _d in self._field_picking_domains().items():
            for prefix, _fetch in picking_compute_fields:
                field = self._get_compute_field_name(prefix, "picking", domain_name)
                default_values[field] = 0
            for prefix, _fetch in move_compute_fields:
                field = self._get_compute_field_name(prefix, "move", domain_name)
                default_values[field] = 0
        return default_values

    # TODO maybe we have to do raw SQL to include the picking + moves counts in
    # a single query
    def _compute_picking_count(self):
        domains = self._field_picking_domains()
        picking_channels = defaultdict(
            lambda: {"channel_id": False, "matched_domains": []}
        )
        all_picking_ids = set()
        channels_aggregate_values = defaultdict(lambda: defaultdict(lambda: 0))
        picking_read_fields = self._get_picking_read_group_fields()
        picking_compute_fields = self._get_picking_compute_fields()
        for domain_name, domain in domains.items():
            data = self.env["stock.picking"].read_group(
                domain + [("release_channel_id", "in", self.ids)],
                ["release_channel_id", "picking_ids:array_agg(id)"]
                + picking_read_fields,
                ["release_channel_id"],
            )
            for row in data:
                channel_id = row["release_channel_id"] and row["release_channel_id"][0]
                if not channel_id:
                    continue
                picking_ids = row["picking_ids"]
                all_picking_ids.update(picking_ids)
                for picking_id in picking_ids:
                    picking_channels[picking_id]["channel_id"] = channel_id
                    picking_channels[picking_id]["matched_domains"].append(domain_name)

                for prefix, fetch in picking_compute_fields:
                    field = self._get_compute_field_name(prefix, "picking", domain_name)
                    channels_aggregate_values[channel_id][field] = row[fetch]
        move_read_fields = self._get_move_read_group_fields()
        move_compute_fields = self._get_move_compute_fields()
        data = self.env["stock.move"].read_group(
            # TODO for now we do estimates, later we may improve the domains per
            # field, but now we can run one sql query on stock.move for all fields
            [("picking_id", "in", list(all_picking_ids)), ("state", "!=", "cancel")],
            ["picking_id"] + move_read_fields,
            ["picking_id"],
        )
        for row in data:
            picking_id = row["picking_id"][0]
            for matched_domain in picking_channels[picking_id]["matched_domains"]:
                for prefix, fetch in move_compute_fields:
                    field = self._get_compute_field_name(prefix, "move", matched_domain)
                    channel_id = picking_channels[picking_id]["channel_id"]
                    channels_aggregate_values[channel_id][field] += row[fetch]

        default_aggregate_values = self._get_default_aggregate_values()
        for record in self:
            values = deepcopy(default_aggregate_values)
            values.update(channels_aggregate_values.get(record.id, {}))
            for prefix, _fetch in self._get_picking_compute_fields():
                values[f"{prefix}_picking_full_progress"] = (
                    values[f"{prefix}_picking_release_ready"]
                    + values[f"{prefix}_picking_released"]
                    + values[f"{prefix}_picking_done"]
                )
            record.write(values)

    def _query_get_chain(self, pickings):
        """Get all stock.picking before an outgoing one

        Follow recursively the move_orig_ids.
        Outgoing picking ids are excluded
        """
        query = """
        WITH RECURSIVE
        pickings AS (
            SELECT move.picking_id,
                   true as outgoing,
                   ''::varchar as state,  -- no need it, we exclude outgoing
                   move.id as move_orig_id
            FROM stock_move move
            WHERE move.picking_id in %s

            UNION

            SELECT move.picking_id,
                   false as outgoing,
                   picking.state,
                   rel.move_orig_id
            FROM stock_move_move_rel rel
            INNER JOIN pickings
            ON pickings.move_orig_id = rel.move_dest_id
            INNER JOIN stock_move move
            ON move.id = rel.move_orig_id
            INNER JOIN stock_picking picking
            ON picking.id = move.picking_id
        )
        SELECT DISTINCT picking_id, state FROM pickings
        WHERE outgoing is false;
        """
        return (query, (tuple(pickings.ids),))

    def _compute_picking_chain(self):
        self.env["stock.move"].flush_model(
            ["move_dest_ids", "move_orig_ids", "picking_id"]
        )
        self.env["stock.picking"].flush_model(["state"])
        for channel in self:
            domain = self._field_picking_domains()["released"]
            domain += [("release_channel_id", "=", channel.id)]
            released = self.env["stock.picking"].search(domain)

            if not released:
                channel.picking_chain_ids = False
                channel.count_picking_chain = 0
                channel.count_picking_chain_in_progress = 0
                channel.count_picking_chain_done = 0
                continue

            self.env.cr.execute(*self._query_get_chain(released))
            rows = self.env.cr.dictfetchall()
            channel.picking_chain_ids = [row["picking_id"] for row in rows]
            channel.count_picking_chain_in_progress = sum(
                [1 for row in rows if row["state"] not in ("cancel", "done")]
            )
            channel.count_picking_chain_done = sum(
                [1 for row in rows if row["state"] == "done"]
            )
            channel.count_picking_chain = (
                channel.count_picking_chain_done
                + channel.count_picking_chain_in_progress
            )

    def _compute_last_done_picking(self):
        for channel in self:
            # TODO we have one query per channel, could be better
            domain = self._field_picking_domains()["done"]
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
        if not self.rule_domain:
            return []
        domain = safe_eval(self.rule_domain) or []
        return domain

    @api.model
    def assign_release_channel(self, picking):
        picking.ensure_one()
        if picking.picking_type_id.code != "outgoing" or picking.state in (
            "cancel",
            "done",
        ):
            return
        message = ""
        for channel in picking._find_release_channel_possible_candidate():
            current = picking
            domain = channel._prepare_domain()
            code = channel.sudo().code
            if not domain and not code:
                current.release_channel_id = channel
            if domain:
                current = picking.filtered_domain(domain)
            if not current:
                continue
            if code:
                current = channel._eval_code(current)
            if not current:
                continue
            current = channel._assign_release_channel_additional_filter(current)
            if not current:
                continue
            if current.release_channel_id != channel:
                current.release_channel_id = channel
            break

        if not picking.release_channel_id:
            # by this point, the picking should have been assigned
            message_template = (
                "Transfer %(picking_name)s could not be assigned to a "
                "channel, you should add a final catch-all rule"
            )
            _logger.warning(message_template, {"picking_name": picking.name})
            message = _(message_template, picking_name=picking.name)
        return message

    def _assign_release_channel_additional_filter(self, pickings):
        self.ensure_one()
        return pickings

    def _eval_context(self, pickings):
        """Prepare the context used when for the python rule evaluation

        :returns: dict -- evaluation context given to (safe_)eval
        """
        eval_context = {
            "uid": self.env.uid,
            "user": self.env.user,
            "time": safe_time,
            "datetime": safe_datetime,
            "dateutil": safe_dateutil,
            "timezone": timezone,
            # orm
            "env": self.env,
            # record
            "self": self,
            "pickings": pickings,
        }
        return eval_context

    def _eval_code(self, pickings):
        code = self.sudo().code
        expr = code.strip()
        eval_context = self._eval_context(pickings)
        try:
            safe_eval(expr, eval_context, mode="exec", nocopy=True)
        except Exception as err:
            raise exceptions.UserError(
                _(
                    "Error when evaluating the channel's code:\n %(name)s \n(%(error)s)",
                    name=self.name,
                    error=err,
                )
            ) from err
        # normally "pickings" is always set as we set it in the eval context,
        # but let assume the worst case with someone using "del pickings"
        return eval_context.get("pickings", self.env["stock.picking"].browse())

    def action_picking_all(self):
        return self._action_picking_for_field("all")

    def action_picking_release_ready(self):
        return self._action_picking_for_field("release_ready")

    def action_picking_released(self):
        return self._action_picking_for_field("released")

    def action_picking_assigned(self):
        return self._action_picking_for_field("assigned")

    def action_picking_waiting(self):
        return self._action_picking_for_field("waiting")

    def action_picking_late(self):
        return self._action_picking_for_field("late")

    def action_picking_priority(self):
        return self._action_picking_for_field("priority")

    def action_picking_done(self):
        return self._action_picking_for_field("done")

    def _action_picking_for_field(self, field_domain, context=None):
        domain = self._field_picking_domains()[field_domain]
        domain += [("release_channel_id", "in", self.ids)]
        pickings = self.env["stock.picking"].search(domain)
        field = self._get_compute_field_name("count", "picking", field_domain)
        field_descr = self._fields[field]._description_string(self.env)
        return self._build_action(
            "stock_available_to_promise_release.stock_picking_release_action",
            pickings,
            field_descr,
            context=context,
        )

    def action_move_all(self):
        return self._action_move_for_field(
            "all", context={"search_default_release_ready": 1}
        )

    def action_move_release_ready(self):
        return self._action_move_for_field("release_ready")

    def action_move_released(self):
        return self._action_move_for_field("released")

    def action_move_assigned(self):
        return self._action_move_for_field("assigned")

    def action_move_waiting(self):
        return self._action_move_for_field("waiting")

    def action_move_late(self):
        return self._action_move_for_field("late")

    def action_move_priority(self):
        return self._action_move_for_field("priority")

    def action_move_done(self):
        return self._action_move_for_field("done")

    def _action_move_for_field(self, field_domain, context=None):
        domain = self._field_picking_domains()[field_domain]
        domain += [("release_channel_id", "in", self.ids)]
        pickings = self.env["stock.picking"].search(domain)
        field = self._get_compute_field_name("count", "picking", field_domain)
        field_descr = self._fields[field]._description_string(self.env)
        xmlid = "stock_available_to_promise_release.stock_move_release_action"
        action = self.env["ir.actions.act_window"]._for_xml_id(xmlid)
        action["display_name"] = "{} ({})".format(
            ", ".join(self.mapped("display_name")), field_descr
        )
        action["context"] = context if context else {}
        action["domain"] = [("picking_id", "in", pickings.ids)]
        return action

    def _build_action(self, xmlid, records, description, context=None):
        action = self.env["ir.actions.act_window"]._for_xml_id(xmlid)
        action["display_name"] = "{} ({})".format(
            ", ".join(self.mapped("display_name")), description
        )
        # we already have this column in the view's title, save space on the
        # screen
        base_context = {"hide_release_channel_id": True}
        if context:
            base_context.update(context)
        action["context"] = base_context
        action["domain"] = [("id", "in", records.ids)]
        return action

    def action_picking_all_related(self):
        """Open all chained transfers for released deliveries"""
        return self._build_action(
            "stock.action_picking_tree_all",
            self.picking_chain_ids,
            _("All Related Transfers"),
            context={"search_default_available": 1, "search_default_picking_type": 1},
        )

    def get_action_picking_form(self):
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "stock.action_picking_form"
        )
        action["context"] = {}
        if not self.last_done_picking_id:
            raise exceptions.UserError(
                _("Channel %(name)s has no validated transfer yet.", name=self.name)
            )
        action["res_id"] = self.last_done_picking_id.id
        return action

    @staticmethod
    def _pickings_sort_key(picking):
        return (-int(picking.priority or 1), picking.date_priority, picking.id)

    def _get_next_pickings(self):
        return getattr(self, "_get_next_pickings_{}".format(self.batch_mode))()

    def _get_pickings_to_release(self):
        """Get the pickings to release."""
        domain = self._field_picking_domains()["release_ready"]
        domain += [("release_channel_id", "in", self.ids)]
        return self.env["stock.picking"].search(domain)

    def _get_next_pickings_max(self):
        if not self.max_batch_mode:
            raise exceptions.UserError(_("No Max transfers to release is configured."))

        waiting_domain = self._field_picking_domains()["waiting"]
        waiting_domain += [("release_channel_id", "=", self.id)]
        released_in_progress = self.env["stock.picking"].search_count(waiting_domain)

        release_limit = max(self.max_batch_mode - released_in_progress, 0)
        if not release_limit:
            raise exceptions.UserError(
                _(
                    "The number of released transfers in"
                    " progress is already at the maximum."
                )
            )
        next_pickings = self._get_pickings_to_release()
        # We have to use a python sort and not a order + limit on the search
        # because "date_priority" is computed and not stored. If needed, we
        # should evaluate making it a stored field in the module
        # "stock_available_to_promise_release".
        return next_pickings.sorted(self._pickings_sort_key)[:release_limit]

    def _check_is_release_allowed(self):
        for rec in self:
            if not rec.is_release_allowed:
                raise exceptions.UserError(
                    _(
                        "The release of pickings is not allowed for channel %(name)s.",
                        name=rec.name,
                    )
                )

    def release_next_batch(self):
        self._check_is_release_allowed()
        self.ensure_one()
        next_pickings = self._get_next_pickings()
        if not next_pickings:
            return {
                "effect": {
                    "fadeout": "fast",
                    "message": _("Nothing in the queue!"),
                    "img_url": "/web/static/src/img/smile.svg",
                    "type": "rainbow_man",
                }
            }
        next_pickings.release_available_to_promise()

    def _check_is_action_lock_allowed(self):
        for rec in self:
            if not rec.is_action_lock_allowed:
                raise exceptions.UserError(
                    _(
                        "Action 'Lock' is not allowed for channel %(name)s.",
                        name=rec.name,
                    )
                )

    def _check_is_action_unlock_allowed(self):
        for rec in self:
            if not rec.is_action_unlock_allowed:
                raise exceptions.UserError(
                    _(
                        "Action 'Unlock' is not allowed for channel %(name)s.",
                        name=rec.name,
                    )
                )

    def _check_is_action_sleep_allowed(self):
        for rec in self:
            if not rec.is_action_sleep_allowed:
                raise exceptions.UserError(
                    _(
                        "Action 'Sleep' is not allowed for channel %(name)s.",
                        name=rec.name,
                    )
                )

    def _check_is_action_wake_up_allowed(self):
        for rec in self:
            if not rec.is_action_wake_up_allowed:
                raise exceptions.UserError(
                    _(
                        "Action 'Wake Up' is not allowed for channel %(name)s.",
                        name=rec.name,
                    )
                )

    def action_lock(self):
        self._check_is_action_lock_allowed()
        self.write({"state": "locked"})

    def action_unlock(self):
        self._check_is_action_unlock_allowed()
        self.write({"state": "open"})

    def action_sleep(self):
        self._check_is_action_sleep_allowed()
        pickings_to_unassign = self.env["stock.picking"].search(
            self._get_picking_to_unassign_domain()
        )
        pickings_to_unassign.write({"release_channel_id": False})
        pickings_to_unassign.unrelease()
        self.write({"state": "asleep"})

    def action_wake_up(self):
        self._check_is_action_wake_up_allowed()
        self.write({"state": "open"})
        self.assign_pickings()

    @api.model
    def assign_pickings(self):
        pickings = self.env["stock.picking"].search(
            self._get_picking_to_assign_domain()
        )
        for pick in pickings:
            pick._delay_assign_release_channel()

    def _get_expected_date(self):
        """Return the new date to set on move chain"""
        self.ensure_one()
        return False
