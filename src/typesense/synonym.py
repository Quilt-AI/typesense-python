class Synonym(object):
    def __init__(self, api_call, collection_name, synonym_id):
        self.api_call = api_call
        self.collection_name = collection_name
        self.synonym_id = synonym_id

    def _endpoint_path(self):
        from .synonyms import Synonyms
        from .collections import Collections
        return u"{0}/{1}/{2}/{3}".format(Collections.RESOURCE_PATH, self.collection_name, Synonyms.RESOURCE_PATH,
                                         self.synonym_id)

    async def retrieve(self):
        return await self.api_call.get(self._endpoint_path())

    async def delete(self):
        return await self.api_call.delete(self._endpoint_path())
