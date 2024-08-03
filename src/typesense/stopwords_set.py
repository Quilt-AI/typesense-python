class StopwordsSet(object):
    def __init__(self, api_call, stopwords_set_id):
        self.stopwords_set_id = stopwords_set_id
        self.api_call = api_call

    def _endpoint_path(self):
        from .stopwords import Stopwords
        return u"{0}/{1}".format(Stopwords.RESOURCE_PATH, self.stopwords_set_id)

    async def retrieve(self):
        return await self.api_call.get(self._endpoint_path())

    async def delete(self):
        return await self.api_call.delete(self._endpoint_path())
