create table user
(
    id       bigint auto_increment
        primary key,
    name     varchar(255)  not null,
    email_id varchar(100)  not null,
    use_flag tinyint(1)    not null,
    image_url varchar(1000)  null,

    login_id varchar(100)  not null,
    password tinyblob,
    change_password_at timestamp,
    token varchar(255) ,
    latest_active_at timestamp ,

    service_id bigint not null,
    platform_version varchar(20),
    join_platform varchar(20),
    join_type varchar(20),

    joined_flag tinyint(1) not null,
    joined_at timestamp,
    marketing_terms JSON    not null,
    additional_info JSON    not null,

    verify_token varchar(32),
    verify_flag tinyint(1) not null,
    verify_at timestamp,

    withdraw_flag tinyint(1) not null,
    withdraw_at timestamp,
    withdraw_reason varchar(2000),
    recovery_reason varchar(2000),

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

insert into user (id, name, email_id, use_flag, login_id, service_id, joined_flag, verify_flag, withdraw_flag, removed_flag,
marketing_terms,
additional_info,
created_at, created_by_id, created_object_type, updated_at, updated_by_id, updated_object_type)
values (1, '시스템', 'no-reply@no-it.io', 1, 'no-reply@no-it.io', 0, 1, 1, 0, 0,
'{"email_agree_flag": true,"email_agree_at": null,"sms_agree_flag": false,"sms_agree_at": null,"call_agree_flag": false,"call_agree_at": null,"post_agree_flag": false,"post_agree_at": null}',
'{}',
 now(), 1, 'user', now(), 1, 'user');

create table user_discipline
(
    id       bigint auto_increment
        primary key,
    user_id bigint not null,
    start_at timestamp,
    end_at timestamp,
    reason     varchar(2000)  not null,
    release_flag tinyint(1) not null,
    release_reason     varchar(2000),
    release_at timestamp,

    created_at timestamp not null,
    created_by_id bigint not null,
    created_object_type varchar(10) not null,
    updated_at timestamp not null,
    updated_by_id bigint not null,
    updated_object_type varchar(10) not null
) default charset = utf8mb4
    collate = utf8mb4_general_ci;

create table user_history (
    id bigint auto_increment
        primary key,
    user_id bigint not null,
    description varchar(100) not null,
    created_at timestamp not null,
    created_by_id bigint not null,
    created_object_type varchar(10) not null
) default charset = utf8mb4
    collate = utf8mb4_general_ci;

create table user_terms (
    id bigint auto_increment
        primary key,
    user_id bigint not null,
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


create table user_report (
id bigint auto_increment
        primary key,
        user_id bigint not null,
        reason     varchar(2000)  not null,
        created_at timestamp not null,
        created_by_id bigint not null,
        created_object_type varchar(10) not null
) default charset = utf8mb4
      collate = utf8mb4_general_ci;

create table user_block (
id bigint auto_increment
        primary key,
        user_id bigint not null,
        created_at timestamp not null,
        created_by_id bigint not null,
        created_object_type varchar(10) not null
) default charset = utf8mb4
      collate = utf8mb4_general_ci;
