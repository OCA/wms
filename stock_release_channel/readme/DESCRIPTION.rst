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
  all the pick/pack transfers for released deliveries
* A button on each channel allows to release the next X (configured on the
  channel) transfers (max X at a time, it releases X - currently released and
  not done)
