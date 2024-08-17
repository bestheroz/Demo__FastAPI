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

    def __enter__(self, *args):
        self.session = self.session_factory()
        self.admin_repo = CommonRDBRepository[Admin](self.session, Admin)  # type: ignore
        return super().__enter__(*args)

    def __exit__(self, *args):
        super().__exit__(*args)
        self.session.close()

    def _handle_events(self):
        for admin in self.admin_repo.seen:
            while admin.events:
                event = admin.events.popleft()
                self.event_handler.handle(event, self, self.session)

    def _commit(self):
        self.session.commit()

    def _rollback(self):
        self.session.rollback()

    def _flush(self):
        self.session.flush()
