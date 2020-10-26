An API key is created in the Demo data (for development), using
the Demo user. The key to use in the HTTP header ``API-KEY`` is: 72B044F7AC780DAC

Curl example::

  curl -X POST "http://localhost:8069/shopfloor/user/menu" -H  "accept: */*" -H  "Content-Type: application/json" -H "API-KEY: 72B044F7AC780DAC"
