import csv
import ipaddress
from dataclasses import dataclass
from typing import Any, NotRequired, TypedDict

import click
import pytricia  # type: ignore
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.server_api import ServerApi
from treelib import Tree

from src.operators import address_contains
from src.schema import NETWORKS_INDEXES, NETWORKS_VALIDATOR_SCHEMA
from src.types import to_mongodb_ip_network, to_python_ip_network


@dataclass
class ContextObj:
    client: MongoClient[Any]

    database_name: str
    collection_name: str

    @property
    def database(self) -> Database:
        return self.client[self.database_name]

    @property
    def collection(self) -> Collection:
        return self.database[self.collection_name]


class NetworkInsert(TypedDict):
    description: NotRequired[str]
    address: ipaddress.IPv4Network | ipaddress.IPv6Network


@click.group()
@click.option(
    "--mongodb-uri",
    default="mongodb://localhost:27017",
    envvar="MONGODB_URI",
)
@click.option(
    "--mongodb-database",
    default="testing",
    envvar="MONGODB_DATABASE",
)
@click.option(
    "--mongodb-collection",
    default="networks",
    envvar="MONGODB_COLLECTION",
)
@click.pass_context
def cli(
    ctx: click.Context, mongodb_uri: str, mongodb_database: str, mongodb_collection: str
):
    client = MongoClient[Any](mongodb_uri, server_api=ServerApi("1"))

    ctx.obj = ContextObj(
        client=client,
        database_name=mongodb_database,
        collection_name=mongodb_collection,
    )


@cli.command()
@click.pass_context
def initdb(ctx: click.Context):
    obj: ContextObj = ctx.obj

    obj.database.create_collection(
        obj.database_name, validator=NETWORKS_VALIDATOR_SCHEMA
    )

    for index in NETWORKS_INDEXES:
        obj.collection.create_index([index])


@cli.command()
@click.pass_context
def dropdb(ctx: click.Context):
    obj: ContextObj = ctx.obj

    obj.database.drop_collection(obj["collection_name"])


@cli.command()
@click.argument("file", type=click.Path(exists=True, dir_okay=False))
@click.pass_context
def load(ctx: click.Context, file):
    obj: ContextObj = ctx.obj

    with open(file) as csvfile:
        docs = []

        for row in csv.DictReader(csvfile):
            address = ipaddress.ip_network(row["address"])

            network_entity = {
                "address": to_mongodb_ip_network(address),
            }

            if "description" in row:
                network_entity["description"] = row["description"]

            docs.append(network_entity)

    return obj.collection.insert_many(docs)


@cli.command()
@click.argument("address", type=str)
@click.pass_context
def find(ctx: click.Context, address: str):
    obj: ContextObj = ctx.obj

    result = obj.collection.find(
        address_contains("address", ipaddress.ip_address(address))
    )

    if not result:
        click.echo("No results found.")
    else:
        for doc in result:
            click.echo(
                f"{doc['address']['address']} - {doc.get('description', 'No description')}"
            )


@cli.command()
@click.pass_context
def pretty_print(ctx: click.Context):
    obj: ContextObj = ctx.obj

    ip_trie = pytricia.PyTricia()

    for result in obj.collection.find():
        address = to_python_ip_network(result["address"])

        ip_trie.insert(address, result["description"])

    tree = Tree()
    tree.create_node("root", "root")

    for address in ip_trie.keys():
        description = ip_trie[address]

        parent = ip_trie.parent(address)

        tree.create_node(
            f"{address} - {description}",
            address,
            parent=parent if parent else "root",
        )

    click.echo(tree.show())


if __name__ == "__main__":
    cli()
