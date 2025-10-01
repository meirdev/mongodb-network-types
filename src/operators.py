import struct
from ipaddress import IPv4Address, IPv4Network, IPv6Address, IPv6Network
from typing import Any, Mapping

from bson.int64 import Int64


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
        high, low = struct.unpack(">qq", int(address).to_bytes(length=16))
        high, low = Int64(high), Int64(low)

        return {
            "$and": [
                {
                    f"{field}.version": 6,
                },
                {
                    "$or": [
                        {
                            f"{field}.network_address.0": {"$lt": high},
                        },
                        {
                            "$and": [
                                {
                                    f"{field}.network_address.0": high,
                                },
                                {
                                    f"{field}.network_address.1": {"$lte": low},
                                },
                            ],
                        },
                    ],
                },
                {
                    "$or": [
                        {
                            f"{field}.broadcast_address.0": {"$gt": high},
                        },
                        {
                            "$and": [
                                {
                                    f"{field}.broadcast_address.0": high,
                                },
                                {
                                    f"{field}.broadcast_address.1": {"$gte": low},
                                },
                            ],
                        },
                    ],
                },
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
        net_high, net_low = struct.unpack(
            ">qq", int(address.network_address).to_bytes(length=16)
        )
        net_high, net_low = Int64(net_high), Int64(net_low)

        bcast_high, bcast_low = struct.unpack(
            ">qq", int(address.broadcast_address).to_bytes(length=16)
        )
        bcast_high, bcast_low = Int64(bcast_high), Int64(bcast_low)

        def lte_128(addr_prefix: str, target_high: Int64, target_low: Int64):
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

        def gte_128(addr_prefix: str, target_high: Int64, target_low: Int64):
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

        return {
            f"{field}.version": 6,
            "$or": [
                {
                    "$and": [
                        lte_128(f"{field}.network_address", net_high, net_low),
                        gte_128(f"{field}.network_address", bcast_high, bcast_low),
                    ],
                },
                {
                    "$and": [
                        lte_128(f"{field}.broadcast_address", net_high, net_low),
                        gte_128(f"{field}.broadcast_address", bcast_high, bcast_low),
                    ],
                },
                {
                    "$and": [
                        lte_128(f"{field}.network_address", net_high, net_low),
                        gte_128(f"{field}.broadcast_address", bcast_high, bcast_low),
                    ],
                },
                {
                    "$and": [
                        gte_128(f"{field}.network_address", net_high, net_low),
                        lte_128(f"{field}.broadcast_address", bcast_high, bcast_low),
                    ],
                },
            ],
        }
