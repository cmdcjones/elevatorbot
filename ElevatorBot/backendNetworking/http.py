import asyncio
import dataclasses
import logging
import time
from typing import Optional

import aiohttp
from aiohttp import ClientSession, ClientTimeout
from dis_snek.models.discord_objects.user import Member

from ElevatorBot.backendNetworking.results import BackendResult


# the limiter object to not overload the backend
class BackendRateLimiter:
    RATE = 250
    MAX_TOKENS = 10000

    def __init__(self):
        self.tokens = self.MAX_TOKENS
        self.updated_at = time.monotonic()

    async def wait_for_token(self):
        """waits until a token becomes available"""
        while self.tokens < 1:
            self.add_new_tokens()
            await asyncio.sleep(0.1)
        assert self.tokens >= 1
        self.tokens -= 1

    def add_new_tokens(self):
        """Adds a new token if eligible"""
        now = time.monotonic()
        time_since_update = now - self.updated_at
        new_tokens = time_since_update * self.RATE
        if self.tokens + new_tokens >= 1:
            self.tokens = min(self.tokens + new_tokens, self.MAX_TOKENS)
            self.updated_at = now


backend_limiter = BackendRateLimiter()


@dataclasses.dataclass
class BaseBackendConnection:
    """
    Define default backend functions such as get, post and delete.
    These can be called by subclasses, and automatically handle networking and error handling
    """

    # get logger
    logger: logging.Logger = dataclasses.field(
        default=logging.getLogger("backendNetworking"),
        init=False,
        compare=False,
        repr=False,
    )

    # give request a max timeout of half an hour
    timeout: ClientTimeout = dataclasses.field(
        default=ClientTimeout(total=30 * 60),
        init=False,
        compare=False,
        repr=False,
    )

    # discord member
    # used for error message formatting
    discord_member: Optional[Member]

    limiter = backend_limiter

    def __bool__(self):
        """Bool function to test if this exist. Useful for testing if this class got returned and not BackendResult, can be returned on errors"""

        return True

    async def _backend_request(self, method: str, route: str, params: dict = None, data: dict = None) -> BackendResult:
        """Make a request to the specified backend route and return the results"""

        async with asyncio.Lock():
            await self.limiter.wait_for_token()

            async with ClientSession(timeout=self.timeout) as session:
                async with session.request(
                    method=method,
                    url=route,
                    params=params,
                    data=data,
                ) as response:
                    result = await self.__backend_parse_response(response)

                    # if an error occurred, already do the basic formatting
                    if not result:
                        if self.discord_member:
                            result.error_message = {"discord_member": self.discord_member}

                    return result

    async def __backend_parse_response(self, response: aiohttp.ClientResponse) -> BackendResult:
        """Handle any errors and then return the content of the response"""

        result = {}
        if response.status == 200:
            success = True
            self.logger.info("%s: '%s' - '%s'", response.status, response.method, response.url)
            result.update(
                {
                    "result": await response.json(),
                }
            )

        else:
            success = False
            result.update(
                {
                    "error": await self.__backend_handle_errors(response),
                }
            )

        result.update(
            {
                "success": success,
            }
        )

        return BackendResult(**result)

    async def __backend_handle_errors(self, response: aiohttp.ClientResponse) -> Optional[str]:
        """Handles potential errors. Returns None, None if the error should not be returned to the user and str, str if something should be returned to the user"""

        if response.status == 409:
            # this means the errors isn't really an error and we want to return info to the user
            self.logger.info("%s: '%s' - '%s'", response.status, response.method, response.url)
            error_json = await response.json()
            return error_json["error"]

        else:
            # if we dont know anything, just log it with the error
            self.logger.error(
                "%s: '%s' - '%s' - '%s'",
                response.status,
                response.method,
                response.url,
                await response.json(),
            )
            return None
