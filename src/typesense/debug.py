class Debug(object):
    RESOURCE_PATH = '/debug'

    def __init__(self,api_call):
        self.api_call = api_call
        self.collections = {}

    async def retrieve(self):
        return await self.api_call.get('{0}'.format(Debug.RESOURCE_PATH))
