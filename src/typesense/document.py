class Document(object):
    def __init__(self, api_call, collection_name, document_id):
        self.api_call = api_call
        self.collection_name = collection_name
        self.document_id = document_id

    def _endpoint_path(self):
        from .documents import Documents
        from .collections import Collections
        return u"{0}/{1}/{2}/{3}".format(Collections.RESOURCE_PATH, self.collection_name, Documents.RESOURCE_PATH,
                                         self.document_id)

    async def retrieve(self):
        return await self.api_call.get(self._endpoint_path())

    async def update(self, document, params=None):
        return await self.api_call.patch(self._endpoint_path(), document, params)

    async def delete(self):
        return await self.api_call.delete(self._endpoint_path())
