

class Key(object):
    def __init__(self, api_call, key_id):
        self.key_id = key_id
        self.api_call = api_call

    def _endpoint_path(self):
        from .keys import Keys
        return u"{0}/{1}".format(Keys.RESOURCE_PATH, self.key_id)

    async def retrieve(self):
        return await self.api_call.get(self._endpoint_path())

    async def delete(self):
        return await self.api_call.delete(self._endpoint_path())
