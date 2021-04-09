======================
Stock Release Channels
======================

.. |badge1| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3
.. |badge2| image:: https://img.shields.io/badge/github-camptocamp%2Fwms--workload-lightgray.png?logo=github
    :target: https://github.com/camptocamp/wms-workload/tree/13.0/stock_release_channel
    :alt: camptocamp/wms-workload

|badge1| |badge2|

Release channels are:

* Release channels are created by stock managers (only pallets, only parcels, ...)
* A release channel has a sequence, a domain + possibility to use python code
* When a delivery is: created from a sales order / created as backorder /
  released, each release channel is evaluated against it (domain + python code),
  the delivery is assigned to the first channel that matches
* A release channel can change over time: for instance the evaluation of a
  domain or rule can change if a delivery is only partially released
* A kanban board allows tracking how many [To Do Today, Released, Done Today,
  Waiting, Late, Priority] Transfers are in each channel, plus quick access to
  all the pick/pack transfers for released deliveries and to DDMRP buffers of
  released deliveries (if DDMRP is installed)
* A button on each channel allows to release the next X (configured on the
  channel) transfers (max X at a time, it releases X - currently released and
  not done)

**Table of contents**

.. contents::
   :local:

Configuration
=============

In Inventory > Configuration > Release Channels.
Only Stock Managers have write permissions.

Usage
=====

Use Inventory > Operations > Release Channels to access to the dashboard.

Each channel has a dashboard with statistics about the number of transfers
to release and of the progress of the released transfers.

When clicking on the "box" button, transfers are released automatically, to
reach a total of <Max Transfers to release> (option configured in the channel
settings).


Credits
=======

Authors
~~~~~~~

* Camptocamp

Contributors
~~~~~~~~~~~~

* Guewen Baconnier <guewen.baconnier@camptocamp.com>
* Matthieu Méquignon <matthieu.mequignon@camptocamp.com>

Maintainers
~~~~~~~~~~~

This module is maintained by the Camptocamp
