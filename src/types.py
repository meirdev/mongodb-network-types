import ipaddress
import struct
from typing import overload

from bson import Int64

from src.schema import IPv4Network, IPv6Network


@overload
def to_mongodb_ip_network(
    ip_network: ipaddress.IPv4Network,
) -> IPv4Network: ...


@overload
def to_mongodb_ip_network(
    ip_network: ipaddress.IPv6Network,
) -> IPv6Network: ...


def to_mongodb_ip_network(
    ip_network: ipaddress.IPv4Network | ipaddress.IPv6Network,
) -> IPv4Network | IPv6Network:
    if isinstance(ip_network, ipaddress.IPv4Network):
        return {
            "version": 4,
            "address": str(ip_network),
            "mask": ip_network.prefixlen,
            "network_address": Int64(int(ip_network.network_address)),
            "broadcast_address": Int64(int(ip_network.broadcast_address)),
        }
    else:
        n1, n2 = struct.unpack(
            ">qq", int(ip_network.network_address).to_bytes(length=16)
        )
        b1, b2 = struct.unpack(
            ">qq", int(ip_network.broadcast_address).to_bytes(length=16)
        )

        return {
            "version": 6,
            "address": str(ip_network),
            "mask": ip_network.prefixlen,
            "network_address": (Int64(n1), Int64(n2)),
            "broadcast_address": (Int64(b1), Int64(b2)),
        }


@overload
def to_python_ip_network(
    mongodb_ip_network: IPv4Network,
) -> ipaddress.IPv4Network: ...


@overload
def to_python_ip_network(
    mongodb_ip_network: IPv6Network,
) -> ipaddress.IPv6Network: ...


def to_python_ip_network(
    mongodb_ip_network: IPv4Network | IPv6Network,
) -> ipaddress.IPv4Network | ipaddress.IPv6Network:
    if mongodb_ip_network["version"] == 4:
        return ipaddress.IPv4Network(mongodb_ip_network["address"])
    else:
        return ipaddress.IPv6Network(mongodb_ip_network["address"])
