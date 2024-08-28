from abc import ABC

from app.apdapter.orm import DEFAULT_SESSION_FACTORY
from app.apdapter.repository import CommonRDBRepository
from app.apdapter.uow import AbstractUnitOfWork
from app.application.admin.event import AdminEventHandler
from app.application.admin.model import Admin


class AdminRDBUow(AbstractUnitOfWork, ABC):
    def __init__(self, session_factory=DEFAULT_SESSION_FACTORY):
        super().__init__()
        self.session_factory = session_factory
        self.event_handler = AdminEventHandler()

    async def __aenter__(self, *args):
        self.session = self.session_factory()
        self.admin_repo = CommonRDBRepository[Admin](self.session, Admin)  # type: ignore
        return await super().__aenter__(*args)

    async def __aexit__(self, *args):
        await super().__aexit__(*args)
        await self.session.close()

    async def _handle_events(self):
        for seen in self.admin_repo.seen:
            while seen.events:
                event = seen.events.popleft()
                await self.event_handler.handle(event, self, self.session)

    async def _commit(self):
        await self.session.commit()

    async def _rollback(self):
        await self.session.rollback()

    async def _flush(self):
        await self.session.flush()
