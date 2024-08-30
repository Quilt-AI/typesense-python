from __future__ import annotations

import sys
from email.policy import default
from typing import TYPE_CHECKING

if sys.version_info >= (3, 11):
    import typing
else:
    import typing_extensions as typing

from typesense.api_call import ApiCall
from typesense.types.collection import CollectionCreateSchema, CollectionSchema
from typesense.types.document import DocumentSchema

from .collection import Collection

TDoc = typing.TypeVar("TDoc", bound=DocumentSchema)


class Collections(typing.Generic[TDoc]):
    RESOURCE_PATH = "/collections"

    def __init__(self, api_call: ApiCall):
        self.api_call = api_call
        self.collections: typing.Dict[str, Collection[TDoc]] = {}

    def __getitem__(self, collection_name: str) -> Collection[TDoc]:
        if not self.collections.get(collection_name):
            self.collections[collection_name] = Collection(
                self.api_call, collection_name
            )
        return self.collections[collection_name]

    def create(self, schema: CollectionCreateSchema) -> CollectionSchema:
        call: CollectionSchema = self.api_call.post(
            endpoint=Collections.RESOURCE_PATH,
            entity_type=CollectionSchema,
            as_json=True,
            body=schema,
        )
        return call

    def retrieve(self) -> typing.List[CollectionSchema]:
        call: typing.List[CollectionSchema] = self.api_call.get(
            endpoint=Collections.RESOURCE_PATH,
            as_json=True,
            entity_type=typing.List[CollectionSchema],
        )
        return call
