create table admin
(
    id       bigint auto_increment
        primary key,
    name     varchar(255)  not null,
    use_flag tinyint    not null,
    manager_flag tinyint    not null,

    login_id varchar(100)  not null,
    password varchar(194),
    token varchar(255) ,

    change_password_at timestamp,
    latest_active_at timestamp ,

    authorities JSON  not null,
    joined_at timestamp,

    removed_flag tinyint    not null,
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
INSERT INTO admin (id, name, use_flag, manager_flag,
login_id, password,
authorities, joined_at, removed_flag,
created_at, created_by_id, created_object_type, updated_at, updated_by_id, updated_object_type)
VALUES (1, '시스템', 1, 1,
'system', '0xA96896D3EB721A6D9E8D21205F1422405E72BFC855903E74DEB27EB5302EED66900519C7D3E0BA1FE9BCB6881AF48531C9339D4704E0C9815B3C65214A2F694BAC2447B1A2A544E15A2423AF97443DFA1C7B6B81C4F26B2ED92675276D88FB93',
'[]', now(), 0,
 now(), 1, 'admin', now(), 1, 'admin');
