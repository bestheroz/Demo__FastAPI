create table notice
(
    id       bigint auto_increment
        primary key,
    title     text  not null,
    content     text  not null,

    use_flag tinyint    not null,
    removed_flag     tinyint  not null,
    removed_at     timestamp,

    created_at timestamp not null,
    created_by_id bigint not null,
    created_object_type varchar(10) not null,
    updated_at timestamp not null,
    updated_by_id bigint not null,
    updated_object_type varchar(10) not null
) default charset = utf8mb4
    collate = utf8mb4_general_ci;
