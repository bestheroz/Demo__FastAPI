create table user
(
    id       bigint auto_increment
        primary key,
    name     varchar(255)  not null,
    use_flag tinyint    not null,

    login_id varchar(100)  not null,
    password varchar(194),
    change_password_at timestamp,
    token varchar(255) ,
    latest_active_at timestamp ,

    authorities JSON  not null,
    joined_at timestamp,
    additional_info JSON    null,

    removed_flag     tinyint  default 0 not null,
    removed_at timestamp,

    created_at timestamp not null,
    created_object_id bigint not null,
    created_object_type varchar(10) not null,
    updated_at timestamp not null,
    updated_object_id bigint not null,
    updated_object_type varchar(10) not null
) default charset = utf8mb4
    collate = utf8mb4_general_ci;

ALTER TABLE user
    ADD INDEX idx_login_id_on_user (login_id);

insert into user (id, name, use_flag, login_id, password,
authorities, removed_flag, additional_info,
created_at, created_object_id, created_object_type, updated_at, updated_object_id, updated_object_type)
values (1, '개발자(User)', 1, 'developer', '$2b$12$HbX5j99YnnKs8zWC/LokB.kyujREbh.kQ9sTNacD/hbEfm8eIP7lm',
'["NOTICE_VIEW"]', 0, '{}',
 now(), 1, 'admin', now(), 1, 'admin');

