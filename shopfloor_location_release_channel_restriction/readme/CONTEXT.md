As in shopfloor, we don't transfer immediately the movement after having set
the destination, we needed to find a way to restrict the location.

The only way was to set the restriction when setting the destination (which differs from
the base module).

We used also the `is_dest_location_valid()` function which is called before setting the 
destination in order to return the error to the user.
