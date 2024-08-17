from abc import ABC

from app.apdapter.orm import DEFAULT_SESSION_FACTORY
from app.apdapter.repository import CommonRDBRepository
from app.apdapter.uow import AbstractUnitOfWork
from app.application.admin.account.event import AdminAccountEventHandler
from app.application.admin.account.model import AdminAccount


class AdminAccountRDBUow(AbstractUnitOfWork, ABC):
    def __init__(self, session_factory=DEFAULT_SESSION_FACTORY):
        super().__init__()
        self.session_factory = session_factory
        self.event_handler = AdminAccountEventHandler()

    def __enter__(self, *args):
        self.session = self.session_factory()
        self.admin_account_repo = CommonRDBRepository[AdminAccount](
            self.session,
            AdminAccount,  # type: ignore
        )
        return super().__enter__(*args)

    def __exit__(self, *args):
        super().__exit__(*args)
        self.session.close()

    def _handle_events(self):
        for admin_account in self.admin_account_repo.seen:
            while admin_account.events:
                event = admin_account.events.popleft()
                self.event_handler.handle(event, self, self.session)

    def _commit(self):
        self.session.commit()

    def _rollback(self):
        self.session.rollback()

    def _flush(self):
        self.session.flush()
