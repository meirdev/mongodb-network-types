from typing import Annotated, Literal, NotRequired, TypedDict

from annotated_types import Ge, Le
from bson import ObjectId
from bson.int64 import Int64
from pymongo import ASCENDING


class IPv4Network(TypedDict):
    version: Literal[4]
    address: str
    mask: Annotated[int, Ge(1), Le(32)]
    network_address: Int64
    broadcast_address: Int64


class IPv6Network(TypedDict):
    version: Literal[6]
    address: str
    mask: Annotated[int, Ge(1), Le(128)]
    network_address: tuple[Int64, Int64]
    broadcast_address: tuple[Int64, Int64]


class NetworkEntity(TypedDict):
    _id: ObjectId
    description: NotRequired[str]
    address: IPv4Network | IPv6Network


NETWORKS_VALIDATOR_SCHEMA = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["address"],
        "properties": {
            "address": {
                "bsonType": "object",
                "oneOf": [
                    {
                        "bsonType": "object",
                        "required": [
                            "version",
                            "address",
                            "mask",
                            "network_address",
                            "broadcast_address",
                        ],
                        "properties": {
                            "version": {
                                "enum": [4],
                            },
                            "address": {
                                "bsonType": "string",
                            },
                            "mask": {
                                "bsonType": "int",
                                "minimum": 1,
                                "maximum": 32,
                            },
                            "network_address": {
                                "bsonType": "long",
                            },
                            "broadcast_address": {
                                "bsonType": "long",
                            },
                        },
                    },
                    {
                        "bsonType": "object",
                        "required": [
                            "version",
                            "address",
                            "mask",
                            "network_address",
                            "broadcast_address",
                        ],
                        "properties": {
                            "version": {
                                "enum": [6],
                            },
                            "address": {
                                "bsonType": "string",
                            },
                            "mask": {
                                "bsonType": "int",
                                "minimum": 1,
                                "maximum": 128,
                            },
                            "network_address": {
                                "bsonType": ["array"],
                                "items": {
                                    "bsonType": ["long"],
                                },
                                "minItems": 2,
                                "maxItems": 2,
                            },
                            "broadcast_address": {
                                "bsonType": ["array"],
                                "items": {
                                    "bsonType": ["long"],
                                },
                                "minItems": 2,
                                "maxItems": 2,
                            },
                        },
                    },
                ],
            },
            "description": {
                "bsonType": "string",
                "description": "Optional description of the network",
            },
        },
    },
}

NETWORKS_INDEXES = [
    ("address.version", ASCENDING),
    # Ipv4
    ("address.network_address", ASCENDING),
    ("address.broadcast_address", ASCENDING),
    # Ipv6
    ("address.network_address.0", ASCENDING),
    ("address.network_address.1", ASCENDING),
    ("address.broadcast_address.0", ASCENDING),
    ("address.broadcast_address.1", ASCENDING),
]
