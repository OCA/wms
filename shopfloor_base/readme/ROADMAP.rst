* /!\ IMPORTANT /!\ due to a bug in `endpoint_route_handler` when working w/ multiple workers
  you MUST restart the instance every time you add or modify a Shopfloor app from the UI
  otherwise is not granted that the routing map
  is going to be up to date on all workers
  and your app won't work.

  @simahawk has already a POC to fix this.

* improve documentation
* change shopfloor.scenario.key to selection? See comment in model
