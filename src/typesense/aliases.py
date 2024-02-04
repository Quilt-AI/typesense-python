from typesense.alias import Alias


class Aliases(object):
    RESOURCE_PATH = '/aliases'

    def __init__(self, api_call):
        self.api_call = api_call
        self.aliases = {}

    def __getitem__(self, name):
        if name not in self.aliases:
            self.aliases[name] = Alias(self.api_call, name)

        return self.aliases.get(name)

    def _endpoint_path(self, alias_name):
        return u"{0}/{1}".format(Aliases.RESOURCE_PATH, alias_name)

    async def upsert(self, name, mapping):
        return await self.api_call.put(self._endpoint_path(name), mapping)

    async def retrieve(self):
        return await self.api_call.get(Aliases.RESOURCE_PATH)
