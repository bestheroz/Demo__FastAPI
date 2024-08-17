create table admin_account
(
    id       bigint auto_increment
        primary key,
    name     varchar(255)  not null,
    login_id varchar(100)  not null,
    use_flag tinyint(1)    not null,
    manager_flag tinyint(1)    not null,
    image_url varchar(1000)  null,
    marketing_terms JSON    not null,

    password tinyblob,
    change_password_at timestamp,
    token varchar(255) ,
    latest_active_at timestamp ,

    joined_flag tinyint(1) not null,
    joined_at timestamp,

    verify_token varchar(32),
    verify_flag tinyint(1) not null,
    verify_at timestamp,

    removed_flag tinyint(1) not null,
    removed_at timestamp,

    created_at timestamp not null,
    updated_at timestamp not null
) default charset = utf8mb4
    collate = utf8mb4_general_ci;

-- 초기 세팅를 위해 INSERT
INSERT INTO admin_account (id, name, login_id, password,
use_flag, manager_flag, joined_flag, verify_flag, removed_flag,
marketing_terms,
created_at, updated_at)
VALUES (1, '시스템', 'no-reply@no-it.io', '0xA96896D3EB721A6D9E8D21205F1422405E72BFC855903E74DEB27EB5302EED66900519C7D3E0BA1FE9BCB6881AF48531C9339D4704E0C9815B3C65214A2F694BAC2447B1A2A544E15A2423AF97443DFA1C7B6B81C4F26B2ED92675276D88FB93',
1, 1, 1, 1, 0,
'{"email_agree_flag": true,"email_agree_at": null,"sms_agree_flag": false,"sms_agree_at": null,"call_agree_flag": false,"call_agree_at": null,"post_agree_flag": false,"post_agree_at": null}',
 now(), now());

create table admin
(
    id       bigint auto_increment
        primary key,
    account_id bigint not null,
    name     varchar(255)  not null,
    use_flag tinyint(1)    not null,
    manager_flag tinyint(1)    not null,

    image_url varchar(1000)  null,
    role_name varchar(255)  not null,
    email_id varchar(100)  not null,
    authorities JSON  not null,
    service_id bigint not null,
    invited_at timestamp,
    joined_flag tinyint(1) not null,
    joined_at timestamp,
    latest_active_at timestamp ,

    verify_token varchar(32),
    verify_flag tinyint(1) not null,
    verify_at timestamp,

    removed_flag tinyint(1) not null,
    removed_at timestamp,

    created_at timestamp not null,
    created_by_id bigint not null,
    created_object_type varchar(10) not null,
    updated_at timestamp not null,
    updated_by_id bigint not null,
    updated_object_type varchar(10) not null
) default charset = utf8mb4
    collate = utf8mb4_general_ci;

-- 초기 세팅를 위해 INSERT
INSERT INTO admin (id, account_id, name, use_flag, manager_flag,
role_name, email_id, authorities, service_id, invited_at, joined_flag, joined_at, latest_active_at, verify_flag, removed_flag,
created_at, created_by_id, created_object_type, updated_at, updated_by_id, updated_object_type)
VALUES (1, 1, '시스템', 1, 1,
'시스템', 'no-reply@no-it.io', '[]', 1, now(), 1, now(), now(), 1, 0,
 now(), 1, 'admin', now(), 1, 'admin');

create table admin_account_terms (
    id bigint auto_increment
        primary key,
    account_id bigint not null,
    terms_id bigint not null,
    agree_flag tinyint(1) not null,
    agree_at timestamp,
    created_at timestamp not null,
    created_by_id bigint not null,
    created_object_type varchar(10) not null,
    updated_at timestamp not null,
    updated_by_id bigint not null,
    updated_object_type varchar(10) not null
) default charset = utf8mb4
    collate = utf8mb4_general_ci;
