import asyncio
import dataclasses
import datetime
import os
import time
from base64 import b64encode

import aiohttp
import aiohttp_client_cache
import orjson

import Backend.crud as crud
from Backend.core.errors import CustomException
from Backend.database.models import DiscordUsers
from Backend.networking.bungieRoutes import auth_route
from Backend.networking.http import NetworkBase
from Backend.networking.schemas import WebResponse
from Shared.functions.helperFunctions import get_now_with_tz, localize_datetime
from Shared.functions.ratelimiter import RateLimiter
from Shared.functions.readSettingsFile import get_setting

# the limiter object which to not get rate-limited by bungie. One obj for every instance!
bungie_semaphore = asyncio.Semaphore(100)
bungie_limiter = RateLimiter()
bungie_cache = aiohttp_client_cache.RedisBackend(
    cache_name="backend",
    address=f"""redis://{os.environ.get("REDIS_HOST")}:{os.environ.get("REDIS_PORT")}""",
    allowed_methods=["GET"],
    expire_after=datetime.timedelta(minutes=5),
    urls_expire_after={
        "**/platform/app/oauth/token": 0,  # do not save token stuff
        "**/Destiny2/Stats/PostGameCarnageReport": 0,  # do not save pgcr. We save them anyway and don't look them up more than once
        "**/Destiny2/*/Profile/**components=": datetime.timedelta(minutes=30),  # profile call
        "**/Destiny2/*/Account/*/Stats": datetime.timedelta(minutes=60),  # stats
        "**/Destiny2/*/Account/*/Character/*/Stats/Activities": datetime.timedelta(minutes=5),  # activity history
        "**/GroupV2/*/Members": datetime.timedelta(minutes=60),  # all clan member stuff
        "**/GroupV2/*/AdminsAndFounder": datetime.timedelta(minutes=60),  # all clan admin stuff
        "**/GroupV2": datetime.timedelta(days=1),  # all clan stuff
    },
)
bungie_headers = {"X-API-Key": get_setting("BUNGIE_APPLICATION_API_KEY"), "Accept": "application/json"}

bungie_auth_headers = {
    "content-type": "application/x-www-form-urlencoded",
    "authorization": f"""Basic {b64encode(f"{get_setting('BUNGIE_APPLICATION_CLIENT_ID')}:{get_setting('BUNGIE_APPLICATION_CLIENT_SECRET')}".encode()).decode()}""",
}


@dataclasses.dataclass
class BungieApi(NetworkBase):
    user: DiscordUsers | None = None

    async def get(
        self,
        route: str,
        headers: dict | None = None,
        params: dict | None = None,
        use_cache: bool = True,
        with_token: bool = False,
    ) -> WebResponse:
        """Grabs JSON from the specified URL"""

        # check if we need a token
        if not with_token:
            if self.user:
                # check if the user has a private profile, if so we use oauth
                if self.user.private_profile:
                    # then we use a token
                    with_token = True

        # use the correct headers
        if not headers:
            headers = bungie_headers if not with_token else await self._get_auth_headers()

        try:
            async with aiohttp_client_cache.CachedSession(
                cache=bungie_cache,
                json_serialize=lambda x: orjson.dumps(x).decode(),
                cookie_jar=aiohttp.DummyCookieJar() if with_token else None,
            ) as session:
                # use cache for the responses
                if use_cache:
                    return await self._request(
                        session=session,
                        method="GET",
                        route=route,
                        headers=headers,
                        params=params,
                    )

                # do not use cache
                else:
                    async with session.disabled():
                        return await self._request(
                            session=session,
                            method="GET",
                            route=route,
                            headers=headers,
                            params=params,
                        )

        except CustomException as exc:
            if exc.error == "BungieDestinyPrivacyRestriction":
                # catch the BungieDestinyPrivacyRestriction error to change privacy settings in our db
                self.user = await crud.discord_users.update(db=self.db, to_update=self.user, private_profile=True)

                # then call the same endpoint again, this time with a token
                return await self.get(route=route, params=params, use_cache=use_cache, with_token=True)

            else:
                # otherwise, raise error again
                raise exc

    async def post(self, route: str, json: dict | None = None, params: dict | None = None) -> WebResponse:
        """Post data to bungie. self.discord_id must have the authentication for the action"""

        async with aiohttp_client_cache.CachedSession(cache=bungie_cache) as session:
            # do not use cache here
            async with session.disabled():
                return await self._request(
                    session=session,
                    method="POST",
                    route=route,
                    json=json,
                    headers=await self._get_auth_headers(),
                    params=params,
                )

    async def _get_auth_headers(self) -> dict:
        """Update the auth headers to include a working token. Raise an error if that doesn't exist"""

        headers = bungie_headers.copy()

        # get a working token or abort
        token = await self.get_working_token()

        headers.update(
            {
                "Authorization": f"Bearer {token}",
            }
        )

        return headers

    async def _request(
        self,
        session: aiohttp_client_cache.CachedSession | aiohttp.ClientSession,
        method: str,
        route: str,
        headers: dict = None,
        params: dict = None,
        json: dict = None,
        form_data: dict = None,
        *args,
        **kwargs,
    ) -> WebResponse:
        # wait for a token from the rate limiter
        await bungie_limiter.wait_for_token()

        # use the semaphore
        async with bungie_semaphore:
            # call the parent method
            return await super()._request(
                session=session,
                method=method,
                route=route,
                allow_redirects=method == "POST",
                headers=headers,
                params=params,
                json=json,
                form_data=form_data,
            )

    async def get_working_token(self) -> str:
        """Returns token or raises an error"""

        if not self.user:
            raise ValueError

        # check refresh token expiry and that it exists
        if await crud.discord_users.token_is_expired(db=self.db, user=self.user):
            raise CustomException("NoToken")

        token = self.user.token

        # refresh token if outdated
        current_time = get_now_with_tz()
        if current_time > self.user.token_expiry:
            token = await self._refresh_token()

        return token

    async def _refresh_token(self) -> str:
        """Updates the token and saves it to the DB. Raises an error if failed"""

        data = {
            "grant_type": "refresh_token",
            "refresh_token": str(self.user.refresh_token),
        }

        # get a new token
        async with aiohttp.ClientSession(json_serialize=lambda x: orjson.dumps(x).decode()) as session:
            current_time = int(time.time())

            try:
                response = await self._request(
                    session=session,
                    method="POST",
                    route=auth_route,
                    form_data=data,
                    headers=bungie_auth_headers,
                )
                if response:
                    access_token = response.content["access_token"]

                    await crud.discord_users.update(
                        db=self.db,
                        to_update=self.user,
                        token=access_token,
                        refresh_token=response.content["refresh_token"],
                        token_expiry=localize_datetime(
                            datetime.datetime.fromtimestamp(current_time + int(response.content["expires_in"]))
                        ),
                        refresh_token_expiry=localize_datetime(
                            datetime.datetime.fromtimestamp(current_time + int(response.content["refresh_expires_in"]))
                        ),
                    )

                    return access_token

            except CustomException as exc:
                if exc.error == "NoToken":
                    # catch the NoToken error to invalidate the db
                    await crud.discord_users.invalidate_token(db=self.db, user=self.user)

                raise exc

    async def _handle_errors(self, response: WebResponse, route_with_params: str):
        """Looks for typical bungie errors and handles / logs them"""

        # set the error vars
        error = None
        if "ErrorStatus" in response.content:
            error = response.content["ErrorStatus"]
        elif "error_description" in response.content:
            error = response.content["error_description"]
        error_code = response.content["ErrorCode"] if "ErrorCode" in response.content else None
        error_message = response.content["Message"] if "Message" in response.content else None

        match (response.status, error):
            case (_, "SystemDisabled"):
                raise CustomException("BungieDed")

            case (401, _) | (_, "invalid_grant" | "AuthorizationCodeInvalid"):
                # unauthorized
                self.logger_exceptions.warning(
                    f"'{response.status} - {error} | {error_code}': Unauthorized (too slow, user fault) request for '{route_with_params}'"
                )
                raise CustomException("BungieUnauthorized")

            case (_, "PerEndpointRequestThrottleExceeded" | "DestinyDirectBabelClientTimeout"):
                # we are getting throttled (should never be called in theory)
                self.logger.warning(
                    f"'{response.status} - {error} | {error_code}': Retrying... - Getting throttled for '{route_with_params}' - '{response}'"
                )

                throttle_seconds = response.content["ThrottleSeconds"]

                # reset the ratelimit giver
                bungie_limiter.tokens = 0
                await asyncio.sleep(throttle_seconds)

            case (_, "ClanInviteAlreadyMember"):
                # if user is in clan
                raise CustomException("BungieClanInviteAlreadyMember")

            case (_, "GroupMembershipNotFound"):
                # if user isn't in clan
                raise CustomException("BungieGroupMembershipNotFound")

            case (_, "DestinyItemNotFound"):
                # if user doesn't have that item
                raise CustomException("BungieDestinyItemNotFound")

            case (_, "DestinyPrivacyRestriction"):
                # private profile
                raise CustomException("BungieDestinyPrivacyRestriction")

            case (_, "DestinyDirectBabelClientTimeout"):
                # timeout
                self.logger.warning(
                    f"'{response.status} - {error} | {error_code}': Retrying... - Getting timeouts for '{route_with_params}' - '{response}'"
                )
                await asyncio.sleep(60)

            case (_, "DestinyServiceFailure" | "DestinyInternalError"):
                # timeout
                self.logger.warning(
                    f"'{response.status} - {error} | {error_code}': Retrying... - Bungie is having problems '{route_with_params}' - '{response}'"
                )
                await asyncio.sleep(60)

            case (_, "ClanTargetDisallowsInvites"):
                # user has disallowed clan invites
                raise CustomException("BungieClanTargetDisallowsInvites")

            case (_, "AuthorizationRecordRevoked" | "AuthorizationRecordExpired"):
                # users tokens are no longer valid
                raise CustomException("NoToken")

            case (404, error):
                # not found
                self.logger_exceptions.error(
                    f"'{response.status} - {error} | {error_code}': No stats found for '{route_with_params}' - '{response}'"
                )
                raise CustomException("BungieBadRequest")

            case (429, error):
                # rate limited
                self.logger.warning(
                    f"'{response.status} - {error} | {error_code}': Retrying... - Getting rate limited for '{route_with_params}' - '{response}'"
                )
                await asyncio.sleep(2)

            case (400, error):
                # generic bad request, such as wrong format
                self.logger_exceptions.error(
                    f"'{response.status} - {error} | {error_code}': Generic bad request for '{route_with_params}' - '{response}'"
                )
                raise CustomException("BungieBadRequest")

            case (503, error):
                self.logger.warning(
                    f"'{response.status} - {error} | {error_code}': Retrying... - Server is overloaded for '{route_with_params}' - '{response}'"
                )
                await asyncio.sleep(10)

            case (status, error):
                # catch the rest
                self.logger_exceptions.error(
                    f"'{status} - {error} | {error_code}': Retrying... - Request failed for '{route_with_params}' - '{error_message}' - '{response}'"
                )
                await asyncio.sleep(2)
