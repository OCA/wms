# -*- coding: utf-8 -*-
# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
import uuid

from psycopg2 import sql

from odoo.api import Environment

from odoo.addons.component.core import Component


class SavepointBuilder(Component):
    """Return a new Savepoint instance"""

    _name = "shopfloor.savepoint.action"
    _inherit = "shopfloor.process.action"
    _usage = "savepoint"

    def new(self):
        return Savepoint(self.env.cr)


class Savepoint(object):
    """Wrapper for SQL Savepoint

    Close to "cr.savepoint()" context manager but this class gives more control
    over when the release/rollback are called.
    """

    def __init__(self, cr):
        self._cr = cr
        self.name = uuid.uuid1().hex
        self._execute("SAVEPOINT {}")

    def rollback(self):
        self._clear_env()
        self._execute("ROLLBACK TO SAVEPOINT {}")

    def release(self):
        self._execute("RELEASE SAVEPOINT {}")

    def _execute(self, query):
        # pylint: disable=sql-injection
        self._cr.execute(sql.SQL(query).format(sql.Identifier(self.name)))

    def _clear_env(self):
        for env in list(Environment.envs):
            if env.cr is self.cr:
                env.clear()
                break
