# Copyright 2022 Michael Tietz (MT Software) <mtietz@mt-software.de>
# Copyright 2023 Camptocamp SA (http://www.camptocamp.com)
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

    def for_update(self, records, log_exceptions=False, skip_locked=False):
        """Lock rows for update on a specific table.

        This function will try to obtain a lock on the rows (records parameter) and
        wait until they are available for update.

        Using the SKIP LOCKED parameter (better used with only one record), it will
        not wait for the row to be available but return False if the lock could not
        be obtained.

        """
        query = "SELECT id FROM %s WHERE ID IN %%s FOR UPDATE"
        if skip_locked:
            query += " SKIP LOCKED"
        sql = query % records._table
        self.env.cr.execute(sql, (tuple(records.ids),), log_exceptions=log_exceptions)
        if skip_locked:
            rows = self.env.cr.fetchall()
            return len(rows) == len(records)
        return True
