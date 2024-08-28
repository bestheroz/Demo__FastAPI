from abc import ABC

from app.apdapter.orm import DEFAULT_SESSION_FACTORY
from app.apdapter.repository import CommonRDBRepository
from app.apdapter.uow import AbstractUnitOfWork
from app.application.user.event import UserEventHandler
from app.application.user.model import User


class UserRDBUow(AbstractUnitOfWork, ABC):
    def __init__(self, session_factory=DEFAULT_SESSION_FACTORY):
        super().__init__()
        self.session_factory = session_factory
        self.event_handler = UserEventHandler()

    async def __aenter__(self, *args):
        self.session = self.session_factory()
        self.user_repo = CommonRDBRepository[User](self.session, User)  # type: ignore
        return await super().__aenter__(*args)

    async def __aexit__(self, *args):
        await super().__aexit__(*args)
        await self.session.close()

    async def _handle_events(self):
        for seen in self.user_repo.seen:
            while seen.events:
                event = seen.events.popleft()
                await self.event_handler.handle(event, self, self.session)

    async def _commit(self):
        await self.session.commit()

    async def _rollback(self):
        await self.session.rollback()

    async def _flush(self):
        await self.session.flush()
