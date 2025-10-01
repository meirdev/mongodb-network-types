# MongoDB Network Types

Example of how to save an IPv4 or IPv6 network type in MongoDB using Python.

## Explanation

Unlike PostgreSQL, MongoDB does not have built-in support for network types like `inet` or `cidr`.

To work with network types in MongoDB, we convert the network addresses to integer representations and store them as `int64` values. This allows us to perform range queries and other operations on the network addresses.

For IPv6 addresses, we use array of two `int64` values, beacause MongoDB does not support 128-bit integers natively.
