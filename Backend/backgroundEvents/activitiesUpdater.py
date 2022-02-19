from anyio import create_task_group

from Backend.backgroundEvents.base import BaseEvent
from Backend.core.destiny.activities import DestinyActivities
from Backend.crud import discord_users
from Backend.database.base import get_async_sessionmaker


class ActivitiesUpdater(BaseEvent):
    """Check for Activity Updates 4 times a day"""

    def __init__(self):
        interval_minutes = 60 * 4
        super().__init__(scheduler_type="interval", interval_minutes=interval_minutes)

    async def run(self):
        async with get_async_sessionmaker().begin() as db:
            all_users = await discord_users.get_all(db=db)

            registered_users = []

            # loop through all users
            for user in all_users:
                # make sure they have a token
                if await discord_users.token_is_expired(db=db, user=user):
                    continue

                activities = DestinyActivities(db=db, user=user)

                # add that to task list
                registered_users.append(activities.update_activity_db)

            # update them in anyio tasks
            async with create_task_group() as tg:
                for func in registered_users:
                    tg.start_soon(func)

            # try to get the missing pgcr
            await activities.update_missing_pgcr()
