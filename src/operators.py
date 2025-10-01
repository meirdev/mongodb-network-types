import struct
from ipaddress import IPv4Address, IPv4Network, IPv6Address, IPv6Network
from typing import Any, Mapping

from bson.int64 import Int64


def _lte_128(addr_prefix: str, target_high: Int64, target_low: Int64):
    return {
        "$or": [
            {f"{addr_prefix}.0": {"$lt": target_high}},
            {
                "$and": [
                    {f"{addr_prefix}.0": target_high},
                    {f"{addr_prefix}.1": {"$lte": target_low}},
                ],
            },
        ],
    }


def _gte_128(addr_prefix: str, target_high: Int64, target_low: Int64):
    return {
        "$or": [
            {f"{addr_prefix}.0": {"$gt": target_high}},
            {
                "$and": [
                    {f"{addr_prefix}.0": target_high},
                    {f"{addr_prefix}.1": {"$gte": target_low}},
                ],
            },
        ],
    }


def _unpack_ipv6(address: IPv6Address) -> tuple[Int64, Int64]:
    high, low = struct.unpack(">qq", int(address).to_bytes(length=16))
    return Int64(high), Int64(low)


def address_contains(
    field: str,
    address: IPv4Address | IPv6Address,
) -> Mapping[str, Any]:
    if isinstance(address, IPv4Address):
        return {
            f"{field}.version": 4,
            f"{field}.network_address": {
                "$lte": Int64(address),
            },
            f"{field}.broadcast_address": {
                "$gte": Int64(address),
            },
        }
    else:
        high, low = _unpack_ipv6(address)

        return {
            "$and": [
                {
                    f"{field}.version": 6,
                },
                _lte_128(f"{field}.network_address", high, low),
                _gte_128(f"{field}.broadcast_address", high, low),
            ],
        }


def address_overlaps(
    field: str,
    address: IPv4Network | IPv6Network,
) -> Mapping[str, Any]:
    if isinstance(address, IPv4Network):
        return {
            f"{field}.version": 4,
            "$or": [
                {
                    f"{field}.network_address": {
                        "$lte": Int64(address.network_address),
                        "$gte": Int64(address.broadcast_address),
                    },
                },
                {
                    f"{field}.broadcast_address": {
                        "$lte": Int64(address.network_address),
                        "$gte": Int64(address.broadcast_address),
                    },
                },
                {
                    f"{field}.network_address": {
                        "$lte": Int64(address.network_address)
                    },
                    f"{field}.broadcast_address": {
                        "$gte": Int64(address.broadcast_address)
                    },
                },
                {
                    f"{field}.network_address": {
                        "$gte": Int64(address.network_address)
                    },
                    f"{field}.broadcast_address": {
                        "$lte": Int64(address.broadcast_address)
                    },
                },
            ],
        }
    else:
        net_high, net_low = _unpack_ipv6(address.network_address)
        bcast_high, bcast_low = _unpack_ipv6(address.broadcast_address)

        return {
            f"{field}.version": 6,
            "$or": [
                {
                    "$and": [
                        _lte_128(f"{field}.network_address", net_high, net_low),
                        _gte_128(f"{field}.network_address", bcast_high, bcast_low),
                    ],
                },
                {
                    "$and": [
                        _lte_128(f"{field}.broadcast_address", net_high, net_low),
                        _gte_128(f"{field}.broadcast_address", bcast_high, bcast_low),
                    ],
                },
                {
                    "$and": [
                        _lte_128(f"{field}.network_address", net_high, net_low),
                        _gte_128(f"{field}.broadcast_address", bcast_high, bcast_low),
                    ],
                },
                {
                    "$and": [
                        _gte_128(f"{field}.network_address", net_high, net_low),
                        _lte_128(f"{field}.broadcast_address", bcast_high, bcast_low),
                    ],
                },
            ],
        }
