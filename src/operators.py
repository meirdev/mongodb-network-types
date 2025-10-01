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
            ],
        }
    else:
        raise NotImplementedError("IPv6 address overlaps not implemented yet.")
