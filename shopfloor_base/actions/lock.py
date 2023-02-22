# Copyright 2022 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
import hashlib
import struct

from odoo.addons.component.core import Component


class LockAction(Component):
    """Provide methods to create database locks"""

    _name = "shopfloor.lock.action"
    _inherit = "shopfloor.process.action"
    _usage = "lock"

    def advisory(self, name):
        """
        Create a blocking advisory lock
        The lock is released at the commit or rollback of the transaction.
        """
        hasher = hashlib.sha1(str(name).encode())
        # pg_lock accepts an int8 so we build an hash composed with
        # contextual information and we throw away some bits
        int_lock = struct.unpack("q", hasher.digest()[:8])

        self.env.cr.execute("SELECT pg_advisory_xact_lock(%s);", (int_lock,))
        self.env.cr.fetchone()[0]

    def for_update(self, records, log_exceptions=False):
        """Lock a table FOR UPDATE"""
        sql = "SELECT id FROM %s WHERE ID IN %%s FOR UPDATE" % records._table
        self.env.cr.execute(sql, (tuple(records.ids),), log_exceptions=False)
