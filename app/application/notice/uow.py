from abc import ABC

from app.apdapter.orm import DEFAULT_SESSION_FACTORY
from app.apdapter.repository import CommonRDBRepository
from app.apdapter.uow import AbstractUnitOfWork
from app.application.notice.event import NoticeEventHandler
from app.application.notice.model import Notice


class NoticeRDBUow(AbstractUnitOfWork, ABC):
    def __init__(self, session_factory=DEFAULT_SESSION_FACTORY):
        super().__init__()
        self.session_factory = session_factory
        self.event_handler = NoticeEventHandler()

    def __enter__(self, *args):
        self.session = self.session_factory()
        self.notice_repo = CommonRDBRepository[Notice](self.session, Notice)  # type: ignore
        return super().__enter__(*args)

    def __exit__(self, *args):
        super().__exit__(*args)
        self.session.close()

    def _handle_events(self):
        for notice in self.notice_repo.seen:
            while notice.events:
                event = notice.events.popleft()
                self.event_handler.handle(event, self, self.session)

    def _commit(self):
        self.session.commit()

    def _rollback(self):
        self.session.rollback()

    def _flush(self):
        self.session.flush()
