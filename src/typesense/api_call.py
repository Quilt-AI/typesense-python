"""
This module provides functionality for making API calls to a Typesense server.

It contains the ApiCall class, which is responsible for executing HTTP requests
to the Typesense API, handling retries, and managing node health.

Key features:
- Support for GET, POST, PUT, PATCH, and DELETE HTTP methods
- Automatic retries on server errors
- Node health management
- Type-safe request execution with overloaded methods

Classes:
    ApiCall: Manages API calls to the Typesense server.

Dependencies:
    - requests: For making HTTP requests
    - typesense.configuration: Provides Configuration and Node classes
    - typesense.exceptions: Custom exception classes
    - typesense.node_manager: Provides NodeManager class
    - typesense.request_handler: Provides RequestHandler class

Usage:
    from typesense.configuration import Configuration
    from api_call import ApiCall

    config = Configuration(...)
    api_call = ApiCall(config)
    response = api_call.get("/collections", SomeEntityType)

Note: This module is part of the Typesense Python client library and is used internally
by other components of the library.
"""

import sys

import aiohttp

from typesense.configuration import Configuration, Node
from typesense.exceptions import (
    HTTPStatus0Error,
    ServerError,
    ServiceUnavailable,
    TypesenseClientError,
)
from typesense.node_manager import NodeManager
from typesense.request_handler import RequestHandler, SessionFunctionKwargs

if sys.version_info >= (3, 11):
    import typing
else:
    import typing_extensions as typing

TParams = typing.TypeVar("TParams")
TBody = typing.TypeVar("TBody")
TEntityDict = typing.TypeVar("TEntityDict")


_SERVER_ERRORS: typing.Final[
    typing.Tuple[
        typing.Type[aiohttp.client.ServerTimeoutError],
        typing.Type[aiohttp.client.ClientConnectionError],
        typing.Type[aiohttp.client.ClientResponseError],
        typing.Type[aiohttp.client.ClientPayloadError],
        typing.Type[aiohttp.client.ClientSSLError],
        typing.Type[HTTPStatus0Error],
        typing.Type[ServerError],
        typing.Type[ServiceUnavailable],
    ]
] = (
    aiohttp.client.ServerTimeoutError,
    aiohttp.client.ClientConnectionError,
    aiohttp.client.ClientResponseError,
    aiohttp.client.ClientPayloadError,
    aiohttp.client.ClientSSLError,
    HTTPStatus0Error,
    ServerError,
    ServiceUnavailable,
)


class ApiCall:
    """
    Manages API calls to the Typesense server.

    This class handles the execution of HTTP requests to the Typesense API,
    including retries, node health management, and error handling.

    Attributes:
        config (Configuration): The configuration object for the Typesense client.
        node_manager (NodeManager): Manages the nodes in the Typesense cluster.
        request_handler (RequestHandler): Handles the execution of individual requests.
    """

    def __init__(self, config: Configuration):
        """
        Initialize the ApiCall instance.

        Args:
            config (Configuration): The configuration object for the Typesense client.
        """
        self.config = config
        self.node_manager = NodeManager(config)
        self.request_handler = RequestHandler(config)
        self._session = aiohttp.ClientSession()

    @typing.overload
    async def get(
        self,
        endpoint: str,
        entity_type: typing.Type[TEntityDict],
        as_json: typing.Literal[False],
        params: typing.Union[TParams, None] = None,
    ) -> str:
        """
        Execute a GET request to the Typesense API.

        Args:
            endpoint (str): The API endpoint to call.
            entity_type (Type[TEntityDict]): The expected type of the response entity.
            as_json (False): Whether to return the response as JSON. Defaults to True.
            params (Union[TParams, None], optional): Query parameters for the request.

        Returns:
            str: The response, as a string.
        """

    @typing.overload
    async def get(
        self,
        endpoint: str,
        entity_type: typing.Type[TEntityDict],
        as_json: typing.Literal[True],
        params: typing.Union[TParams, None] = None,
    ) -> TEntityDict:
        """
        Execute a GET request to the Typesense API.

        Args:
            endpoint (str): The API endpoint to call.
            entity_type (Type[TEntityDict]): The expected type of the response entity.
            as_json (True): Whether to return the response as JSON. Defaults to True.
            params (Union[TParams, None], optional): Query parameters for the request.

        Returns:
            EntityDict: The response, as a JSON object.
        """

    async def get(
        self,
        endpoint: str,
        entity_type: typing.Type[TEntityDict],
        as_json: typing.Union[typing.Literal[True], typing.Literal[False]] = True,
        params: typing.Union[TParams, None] = None,
    ) -> typing.Union[TEntityDict, str]:
        """
        Execute a GET request to the Typesense API.

        Args:
            endpoint (str): The API endpoint to call.
            entity_type (Type[TEntityDict]): The expected type of the response entity.
            as_json (bool): Whether to return the response as JSON. Defaults to True.
            params (Union[TParams, None], optional): Query parameters for the request.

        Returns:
            Union[TEntityDict, str]: The response, either as a JSON object or a string.
        """
        return await self._execute_request(
            self._session.get,
            endpoint,
            entity_type,
            as_json,
            params=params,
        )

    @typing.overload
    async def post(
        self,
        endpoint: str,
        entity_type: typing.Type[TEntityDict],
        as_json: typing.Literal[False],
        params: typing.Union[TParams, None] = None,
        body: typing.Union[TBody, None] = None,
    ) -> str:
        """
        Execute a GET request to the Typesense API.

        Args:
            endpoint (str): The API endpoint to call.
            entity_type (Type[TEntityDict]): The expected type of the response entity.
            as_json (False): Whether to return the response as JSON. Defaults to True.
            params (Union[TParams, None], optional): Query parameters for the request.

        Returns:
            str: The response, as a string.
        """

    @typing.overload
    async def post(
        self,
        endpoint: str,
        entity_type: typing.Type[TEntityDict],
        as_json: typing.Literal[True],
        params: typing.Union[TParams, None] = None,
        body: typing.Union[TBody, None] = None,
    ) -> TEntityDict:
        """
        Execute a POST request to the Typesense API.

        Args:
            endpoint (str): The API endpoint to call.
            entity_type (Type[TEntityDict]): The expected type of the response entity.
            as_json (True): Whether to return the response as JSON. Defaults to True.
            params (Union[TParams, None], optional): Query parameters for the request.

        Returns:
            EntityDict: The response, as a JSON object.
        """

    async def post(
        self,
        endpoint: str,
        entity_type: typing.Type[TEntityDict],
        as_json: typing.Union[typing.Literal[True], typing.Literal[False]] = True,
        params: typing.Union[TParams, None] = None,
        body: typing.Union[TBody, None] = None,
    ) -> typing.Union[str, TEntityDict]:
        """
        Execute a POST request to the Typesense API.

        Args:
            endpoint (str): The API endpoint to call.
            entity_type (Type[TEntityDict]): The expected type of the response entity.
            as_json (bool): Whether to return the response as JSON. Defaults to True.
            params (Union[TParams, None], optional): Query parameters for the request.

        Returns:
            Union[TEntityDict, str]: The response, either as a JSON object or a string.
        """
        return await self._execute_request(
            self._session.post,
            endpoint,
            entity_type,
            as_json,
            params=params,
            data=body,
        )

    async def put(
        self,
        endpoint: str,
        entity_type: typing.Type[TEntityDict],
        body: TBody,
        params: typing.Union[TParams, None] = None,
    ) -> TEntityDict:
        """
        Execute a PUT request to the Typesense API.

        Args:
            endpoint (str): The API endpoint to call.
            entity_type (Type[TEntityDict]): The expected type of the response entity.
            params (Union[TParams, None], optional): Query parameters for the request.

        Returns:
            EntityDict: The response, as a JSON object.
        """
        return await self._execute_request(
            self._session.put,
            endpoint,
            entity_type,
            as_json=True,
            params=params,
            data=body,
        )

    async def patch(
        self,
        endpoint: str,
        entity_type: typing.Type[TEntityDict],
        body: TBody,
        params: typing.Union[TParams, None] = None,
    ) -> TEntityDict:
        """
        Execute a PATCH request to the Typesense API.

        Args:
            endpoint (str): The API endpoint to call.
            entity_type (Type[TEntityDict]): The expected type of the response entity.
            params (Union[TParams, None], optional): Query parameters for the request.

        Returns:
            EntityDict: The response, as a JSON object.
        """
        return await self._execute_request(
            self._session.patch,
            endpoint,
            entity_type,
            as_json=True,
            params=params,
            data=body,
        )

    async def delete(
        self,
        endpoint: str,
        entity_type: typing.Type[TEntityDict],
        params: typing.Union[TParams, None] = None,
    ) -> TEntityDict:
        """
        Execute a DELETE request to the Typesense API.

        Args:
            endpoint (str): The API endpoint to call.
            entity_type (Type[TEntityDict]): The expected type of the response entity.
            params (Union[TParams, None], optional): Query parameters for the request.

        Returns:
            EntityDict: The response, as a JSON object.
        """
        return await self._execute_request(
            self._session.delete,
            endpoint,
            entity_type,
            as_json=True,
            params=params,
        )

    @typing.overload
    async def _execute_request(
        self,
        fn: typing.Callable[..., typing.Awaitable[aiohttp.ClientResponse]],
        endpoint: str,
        entity_type: typing.Type[TEntityDict],
        as_json: typing.Literal[True],
        last_exception: typing.Union[None, Exception] = None,
        num_retries: int = 0,
        **kwargs: SessionFunctionKwargs[TParams, TBody],
    ) -> TEntityDict:
        """
        Execute a request to the Typesense API with retry logic.

        This method handles the actual execution of the request, including
        node selection, error handling, and retries.

        Args:
            fn (Callable): The HTTP method function to use (e.g., session.get).

            endpoint (str): The API endpoint to call.

            entity_type (Type[TEntityDict]): The expected type of the response entity.

            as_json (bool): Whether to return the response as JSON. Defaults to True.

            last_exception (Union[None, Exception], optional): The last exception encountered.

            num_retries (int): The current number of retries attempted.

            kwargs: Additional keyword arguments for the request.

        Returns:
            TEntityDict: The response, as a JSON object.

        Raises:
            TypesenseClientError: If all nodes are unhealthy or max retries are exceeded.
        """

    @typing.overload
    async def _execute_request(
        self,
        fn: typing.Callable[..., typing.Awaitable[aiohttp.ClientResponse]],
        endpoint: str,
        entity_type: typing.Type[TEntityDict],
        as_json: typing.Literal[False],
        last_exception: typing.Union[None, Exception] = None,
        num_retries: int = 0,
        **kwargs: SessionFunctionKwargs[TParams, TBody],
    ) -> str:
        """
        Execute a request to the Typesense API with retry logic.

        This method handles the actual execution of the request, including
        node selection, error handling, and retries.

        Args:
            fn (Callable): The HTTP method function to use (e.g., session.get).

            endpoint (str): The API endpoint to call.

            entity_type (Type[TEntityDict]): The expected type of the response entity.

            as_json (bool): Whether to return the response as JSON. Defaults to True.

            last_exception (Union[None, Exception], optional): The last exception encountered.

            num_retries (int): The current number of retries attempted.

            kwargs: Additional keyword arguments for the request.

        Returns:
            str: The response, as a string.

        Raises:
            TypesenseClientError: If all nodes are unhealthy or max retries are exceeded.
        """

    async def _execute_request(
        self,
        fn: typing.Callable[..., typing.Awaitable[aiohttp.ClientResponse]],
        endpoint: str,
        entity_type: typing.Type[TEntityDict],
        as_json: typing.Union[typing.Literal[True], typing.Literal[False]] = True,
        last_exception: typing.Union[None, Exception] = None,
        num_retries: int = 0,
        **kwargs: SessionFunctionKwargs[TParams, TBody],
    ) -> typing.Union[TEntityDict, str]:
        """
        Execute a request to the Typesense API with retry logic.

        This method handles the actual execution of the request, including
        node selection, error handling, and retries.

        Args:
            fn (Callable): The HTTP method function to use (e.g., session.get).

            endpoint (str): The API endpoint to call.

            entity_type (Type[TEntityDict]): The expected type of the response entity.

            as_json (bool): Whether to return the response as JSON. Defaults to True.

            last_exception (Union[None, Exception], optional): The last exception encountered.

            num_retries (int): The current number of retries attempted.

            kwargs: Additional keyword arguments for the request.

        Returns:
            Union[TEntityDict, str]: The response, either as a JSON object or a string.

        Raises:
            TypesenseClientError: If all nodes are unhealthy or max retries are exceeded.
        """
        if num_retries > self.config.num_retries:
            if last_exception:
                raise last_exception
            raise TypesenseClientError("All nodes are unhealthy")

        node, url, kwargs = self._prepare_request_params(endpoint, **kwargs)

        try:
            return await self._make_request_and_process_response(
                fn,
                url,
                entity_type,
                as_json,
                **kwargs,
            )
        except _SERVER_ERRORS as server_error:
            self.node_manager.set_node_health(node, is_healthy=False)
            return await self._execute_request(
                fn,
                endpoint,
                entity_type,
                as_json,
                last_exception=server_error,
                num_retries=num_retries + 1,
                **kwargs,
            )

    async def _make_request_and_process_response(
        self,
        fn: typing.Callable[..., typing.Awaitable[aiohttp.ClientResponse]],
        url: str,
        entity_type: typing.Type[TEntityDict],
        as_json: bool,
        **kwargs: SessionFunctionKwargs[TParams, TBody],
    ) -> typing.Union[TEntityDict, str]:
        """Make the API request and process the response."""
        request_response = await self.request_handler.make_request(
            fn=fn,
            url=url,
            as_json=as_json,
            entity_type=entity_type,
            **kwargs,
        )
        self.node_manager.set_node_health(self.node_manager.get_node(), is_healthy=True)
        return (
            typing.cast(TEntityDict, request_response)
            if as_json
            else typing.cast(str, request_response)
        )

    def _prepare_request_params(
        self,
        endpoint: str,
        **kwargs: SessionFunctionKwargs[TParams, TBody],
    ) -> typing.Tuple[Node, str, SessionFunctionKwargs[TParams, TBody]]:
        node = self.node_manager.get_node()
        url = node.url() + endpoint

        params = kwargs.get("params")
        if params:
            self.request_handler.normalize_params(params)

        return node, url, kwargs

    async def close(self):
        await self._session.close()
