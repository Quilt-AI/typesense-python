import copy
import json
import time

import aiohttp
from .exceptions import (HTTPStatus0Error, ObjectAlreadyExists,
                         ObjectNotFound, ObjectUnprocessable,
                         RequestMalformed, RequestUnauthorized, RequestForbidden,
                         ServerError, ServiceUnavailable, TypesenseClientError)
from .logger import logger

class ApiCall(object):
    API_KEY_HEADER_NAME = 'X-TYPESENSE-API-KEY'

    def __init__(self, config):
        self.config = config
        self.nodes = copy.deepcopy(self.config.nodes)
        self.node_index = 0
        self._session = aiohttp.ClientSession()
        self._initialize_nodes()

    def _initialize_nodes(self):
        if self.config.nearest_node:
            self.set_node_healthcheck(self.config.nearest_node, True)

        for node in self.nodes:
            self.set_node_healthcheck(node, True)

    async def close(self):
        await self._session.close()

    def node_due_for_health_check(self, node):
        current_epoch_ts = int(time.time())
        due_for_check = (current_epoch_ts - node.last_access_ts) > self.config.healthcheck_interval_seconds
        if due_for_check:
            logger.debug('Node {}:{} is due for health check.'.format(node.host, node.port))
        return due_for_check

    # Returns a healthy host from the pool in a round-robin fashion.
    # Might return an unhealthy host periodically to check for recovery.
    def get_node(self):
        if self.config.nearest_node:
            if self.config.nearest_node.healthy or self.node_due_for_health_check(self.config.nearest_node):
                logger.debug('Using nearest node.')
                return self.config.nearest_node
            else:
                logger.debug('Nearest node is unhealthy or not due for health check. Falling back to individual nodes.')

        i = 0
        while i < len(self.nodes):
            i += 1
            node = self.nodes[self.node_index]
            self.node_index = (self.node_index + 1) % len(self.nodes)

            if node.healthy or self.node_due_for_health_check(node):
                return node

        # None of the nodes are marked healthy, but some of them could have become healthy since last health check.
        # So we will just return the next node.
        logger.debug('No healthy nodes were found. Returning the next node.')
        return self.nodes[self.node_index]

    @staticmethod
    def get_exception(http_code):
        if http_code == 0:
            return HTTPStatus0Error
        elif http_code == 400:
            return RequestMalformed
        elif http_code == 401:
            return RequestUnauthorized
        elif http_code == 403:
            return RequestForbidden
        elif http_code == 404:
            return ObjectNotFound
        elif http_code == 409:
            return ObjectAlreadyExists
        elif http_code == 422:
            return ObjectUnprocessable
        elif http_code == 500:
            return ServerError
        elif http_code == 503:
            return ServiceUnavailable
        else:
            return TypesenseClientError

    # Makes the actual http request, along with retries
    async def make_request(self, fn, endpoint, as_json, **kwargs):
        num_tries = 0
        last_exception = None

        logger.debug('Making {} {}'.format(fn.__name__, endpoint))

        while num_tries < (self.config.num_retries + 1):
            num_tries += 1
            node = self.get_node()

            logger.debug('Try {} to node {}:{} -- healthy? {}'.format(num_tries, node.host, node.port, node.healthy))

            try:
                url = node.url() + endpoint
                if kwargs.get('data') and not (isinstance(kwargs['data'], str) or isinstance(kwargs['data'], bytes)):
                    kwargs['data'] = json.dumps(kwargs['data'])

                r = await fn(url, headers={ApiCall.API_KEY_HEADER_NAME: self.config.api_key}, **kwargs)

                # Treat any status code > 0 and < 500 to be an indication that node is healthy
                # We exclude 0 since some clients return 0 when request fails
                if 0 < r.status < 500:
                    logger.debug('{}:{} is healthy. Status code: {}'.format(node.host, node.port, r.status))
                    self.set_node_healthcheck(node, True)

                # We should raise a custom exception if status code is not 20X
                if not 200 <= r.status < 300:
                    if r.headers.get('Content-Type', '').startswith('application/json'):
                        error_message = (await r.json()).get('message', 'API error.')
                    else:
                        error_message = 'API error.'
                    # Raised exception will be caught and retried
                    raise ApiCall.get_exception(r.status)(r.status, error_message)

                return await (r.json() if as_json else r.text())
            except (HTTPStatus0Error, ServerError, ServiceUnavailable, aiohttp.ClientConnectionError,
                    aiohttp.ServerTimeoutError) as e:
                # Catch the exception and retry
                self.set_node_healthcheck(node, False)
                logger.debug('Request to {}:{} failed because of {}'.format(node.host, node.port, e))
                logger.debug('Sleeping for {} and retrying...'.format(self.config.retry_interval_seconds))
                last_exception = e
                time.sleep(self.config.retry_interval_seconds)

        logger.debug('No retries left. Raising last exception: {}'.format(last_exception))
        raise last_exception

    def set_node_healthcheck(self, node, is_healthy):
        node.healthy = is_healthy
        node.last_access_ts = int(time.time())

    @staticmethod
    def normalize_params(params):
        for key in params.keys():
            if params[key] == True:
                params[key] = 'true'
            elif params[key] == False:
                params[key] = 'false'

    async def get(self, endpoint, params=None, as_json=True):
        params = params or {}
        return await self.make_request(self._session.get, endpoint, as_json,
                                 params=params,
                                 timeout=self.config.connection_timeout_seconds, verify_ssl=self.config.verify)

    async def post(self, endpoint, body, params=None, as_json=True):
        params = params or {}
        ApiCall.normalize_params(params)
        return await self.make_request(self._session.post, endpoint, as_json,
                                 params=params, data=body,
                                 timeout=self.config.connection_timeout_seconds, verify_ssl=self.config.verify)

    async def put(self, endpoint, body, params=None):
        return await self.make_request(self._session.put, endpoint, True,
                                 params=params, data=body,
                                 timeout=self.config.connection_timeout_seconds, verify_ssl=self.config.verify)

    async def patch(self, endpoint, body, params=None):
        return await self.make_request(self._session.patch, endpoint, True,
                                 params=params, data=body,
                                 timeout=self.config.connection_timeout_seconds, verify_ssl=self.config.verify)

    async def delete(self, endpoint, params=None):
        return await self.make_request(self._session.delete, endpoint, True,
                                 params=params, timeout=self.config.connection_timeout_seconds,
                                 verify_ssl=self.config.verify)
