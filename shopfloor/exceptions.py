# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)


class ConcurentWorkOnTransfer(Exception):
    """Some user already processed some transfers."""
