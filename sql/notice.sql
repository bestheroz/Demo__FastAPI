create table notice
(
    id       bigint auto_increment
        primary key,
    service_id bigint  not null,
    content     text  not null,
    tags     JSON  not null,

    removed_flag     tinyint  not null,
    removed_at     timestamp,
    removed_reason     varchar(1000),

    created_at timestamp not null,
    created_by_id bigint not null,
    created_object_type varchar(10) not null,
    updated_at timestamp not null,
    updated_by_id bigint not null,
    updated_object_type varchar(10) not null
) default charset = utf8mb4
    collate = utf8mb4_general_ci;
