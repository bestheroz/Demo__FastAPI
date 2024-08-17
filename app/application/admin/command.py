from sqlalchemy import delete, select
from sqlalchemy.sql.functions import count

from app.application.admin.account.command import _create_refresh_token
from app.application.admin.account.model import AdminAccount
from app.application.admin.account.schema import AdminAccountToken, AdminAccountVerify
from app.application.admin.event import AdminInviteCanceled, AdminInvited
from app.application.admin.handler import send_email_for_admin_invited
from app.application.admin.model import Admin
from app.application.admin.schema import (
    AdminInvite,
    AdminInvitedEvent,
    AdminResponse,
    AdminUpdate,
    AdminVerify,
)
from app.application.admin.uow import AdminRDBUow
from app.application.service.model import Service
from app.application.terms.model import Terms
from app.common.code import Code
from app.common.exception import RequestException400
from app.common.schema import ImageUrlUpdate


def invite_admin(
    data: AdminInvite,
    service_id: int,
    operator_id: int,
    uow: AdminRDBUow,
) -> AdminResponse:
    with uow.autocommit():
        service = uow.admin_repo.session.scalar(
            select(Service).filter_by(id=service_id)
        )
        if service is None:
            raise RequestException400(Code.UNKNOWN_SERVICE)
        admin_count_in_service = uow.admin_repo.session.scalar(
            select(count(Admin.id))
            .filter_by(service_id=service_id)
            .filter_by(removed_flag=False)
        )
        if admin_count_in_service and admin_count_in_service >= service.number_of_admin:
            raise RequestException400(Code.LIMIT_INVITED_ADMIN_ACCOUNT)

        admin_account = uow.admin_repo.session.scalar(
            select(AdminAccount)
            .filter_by(login_id=data.login_id)
            .filter_by(removed_flag=False)
        )

        admin = uow.admin_repo.session.scalar(
            select(Admin)
            .filter_by(service_id=service_id)
            .filter_by(email_id=data.email_id)
            .filter_by(removed_flag=False)
        )
        if admin:
            raise RequestException400(Code.ALREADY_JOINED_ADMIN)

        if admin_account is None:
            admin_account = AdminAccount.new(data)

        admin = Admin.invite(data, admin_account, service_id, operator_id)
        uow.admin_repo.add(admin)
        return admin.on_created()


def cancel_invitation(
    service_id: int,
    admin_id: int,
    uow: AdminRDBUow,
) -> None:
    with uow.autocommit():
        admin = uow.admin_repo.get(admin_id)
        if (
            admin is None
            or admin.service_id != service_id
            or admin.removed_flag is True
        ):
            raise RequestException400(Code.UNKNOWN_MEMBER)
        uow.admin_repo.session.execute(
            delete(Admin).filter_by(service_id=service_id).filter_by(id=admin_id)
        )
        admin_account = uow.admin_repo.session.scalar(
            select(AdminAccount).filter_by(id=admin.account_id)
        )
        if admin_account is None:
            raise RequestException400(Code.UNKNOWN_ACCOUNT)
        # 관리자 초대가 취소되었기 때문에 초대 받은 계정도 함께 삭제한다.
        if len(admin_account.profiles) == 0 and admin_account.verify_flag is False:
            uow.admin_repo.session.execute(
                delete(AdminAccount).filter_by(id=admin.account_id)
            )
        admin.events.append(
            AdminInviteCanceled(data=AdminInvitedEvent.model_validate(admin))
        )


def re_send_invitation(
    service_id: int,
    admin_id: int,
    uow: AdminRDBUow,
) -> None:
    with uow.autocommit():
        admin = uow.admin_repo.get(admin_id)
        if (
            admin is None
            or admin.service_id != service_id
            or admin.removed_flag is True
        ):
            raise RequestException400(Code.UNKNOWN_MEMBER)
        if admin.joined_flag is True:
            raise RequestException400(Code.ALREADY_JOINED_ADMIN)
        event_data = AdminInvitedEvent.model_validate(admin)
        send_email_for_admin_invited(AdminInvited(data=event_data), True)


def verify_admin(
    service_id: int,
    admin_id: int,
    data: AdminAccountVerify,
    uow: AdminRDBUow,
) -> AdminAccountToken:
    with uow.autocommit():
        admin = uow.admin_repo.get(admin_id)
        if (
            admin is None
            or admin.service_id != service_id
            or admin.removed_flag is True
        ):
            raise RequestException400(Code.UNKNOWN_MEMBER)
        if admin.joined_flag:
            raise RequestException400(Code.ALREADY_JOINED_ADMIN)
        if data.verify_token != admin.verify_token:
            raise RequestException400(Code.INVALID_VERIFY_TOKEN)
        if admin.account is None or admin.account.removed_flag is True:
            raise RequestException400(Code.UNKNOWN_ACCOUNT)

        # 여러 서비스 관리자 초대 메일이 갈수 있으므로 이미 가입되어 있는 경우 생략
        if admin.account.joined_flag is False and data.name is not None:
            uow.admin_repo.add_seen(admin.account)
            required_terms_count = uow.admin_repo.session.scalar(
                select(count(Terms.id)).filter_by(service_id=0).filter_by(use_flag=True)
            )
            terms_ids = [t.terms_id for t in data.terms]
            if required_terms_count != len(terms_ids):
                raise RequestException400(Code.INVALID_TERMS_IDS)
            required_terms = uow.admin_repo.session.scalars(
                select(Terms.id)
                .filter_by(service_id=0)
                .filter_by(required_flag=True)
                .filter_by(use_flag=True)
                .filter(Terms.id.in_([t.terms_id for t in data.terms]))
            ).all()
            for terms_id in required_terms:
                if (
                    terms_id not in terms_ids
                    or next(
                        (t.agree_flag for t in data.terms if t.terms_id == terms_id),
                        None,
                    )
                    is False
                ):
                    raise RequestException400(Code.REQUIRED_TERMS_NOT_ACCEPTED)
            admin.account.verify(data)

        # 서비스에 최초 가입자는 관리자로 설정
        verified_admin_count = uow.admin_repo.session.scalar(
            select(count(Admin.id))
            .filter_by(service_id=service_id)
            .filter_by(verify_flag=True)
            .filter_by(joined_flag=True)
            .filter_by(removed_flag=False)
        )
        if verified_admin_count == 0:
            admin.manager_flag = True
            admin.role_name = "대표자(Master)"
        admin.verify(AdminVerify(verify_token=data.verify_token))
        admin.account.on_updated()

        admin.account.renew_token(_create_refresh_token(admin.account))
        return admin.account.on_logged_in()


def update_admin(
    service_id: int,
    admin_id: int,
    data: AdminUpdate,
    operator_id: int,
    uow: AdminRDBUow,
) -> AdminResponse:
    with uow.autocommit():
        admin = uow.admin_repo.get(admin_id)
        if (
            admin is None
            or admin.service_id != service_id
            or admin.removed_flag is True
        ):
            raise RequestException400(Code.UNKNOWN_MEMBER)
        if admin.service_id != service_id:
            raise RequestException400(Code.UNKNOWN_MEMBER)
        if admin.manager_flag is False and admin.id == operator_id:
            raise RequestException400(Code.CANNOT_UPDATE_YOURSELF)

        admin.update(data, operator_id)
        return admin.on_updated()


def update_admin_image_url(
    service_id: int,
    admin_id: int,
    data: ImageUrlUpdate,
    operator_id: int,
    uow: AdminRDBUow,
) -> AdminResponse:
    with uow.autocommit():
        admin = uow.admin_repo.get(admin_id)
        if (
            admin is None
            or admin.service_id != service_id
            or admin.removed_flag is True
        ):
            raise RequestException400(Code.UNKNOWN_ACCOUNT)
        admin.update_image_url(data.image_url, operator_id)
        return admin.on_updated()


def remove_admin_image_url(
    service_id: int,
    admin_id: int,
    operator_id: int,
    uow: AdminRDBUow,
) -> AdminResponse:
    with uow.autocommit():
        admin = uow.admin_repo.get(admin_id)
        if (
            admin is None
            or admin.service_id != service_id
            or admin.removed_flag is True
        ):
            raise RequestException400(Code.UNKNOWN_ACCOUNT)
        admin.update_image_url(None, operator_id)
        return admin.on_updated()


def remove_admin(
    service_id: int,
    admin_id: int,
    operator_id: int,
    uow: AdminRDBUow,
) -> None:
    with uow.autocommit():
        admin = uow.admin_repo.get(admin_id)
        if admin is None or admin.service_id != service_id:
            raise RequestException400(Code.UNKNOWN_MEMBER)
        if admin.id == operator_id:
            raise RequestException400(Code.CANNOT_REMOVE_YOURSELF)
        admin.remove(operator_id)
        admin.on_removed()
