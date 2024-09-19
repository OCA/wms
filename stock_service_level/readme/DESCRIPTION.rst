Base module to manage route / reservation rules per service level.

This module enhances Odoo with service level capabilities for stock moves.
It enables differentiation of service offerings for the same physical product.

A service level refers to a distinct type of service provision associated
with a product. It allows for selling a product with various service
offerings or levels, facilitating customized customer experiences.

Features:

- Enables selling/requesting the same physical product with different service levels.
- Avoids splitting products into separate procurement groups, preserving
  flexibility in logistics chain operations.
- Allows definition of different routes for products based on service level
  cf `stock_service_level_route` module.
- Select service level on sale order using `sale_stock_service_level` module.

The module integrates seamlessly with Odoo's stock management system.
Users can configure service levels and associated rules through the
interface, enabling efficient management of product variants and service
offerings within the logistics framework.
