create table notice
(
    id       bigint auto_increment
        primary key,
    title     varchar(200)  not null,
    content     text  not null,

    use_flag tinyint    not null,
    removed_flag     tinyint  default 0 not null,
    removed_at     timestamp,

    created_at timestamp not null,
    created_object_id bigint not null,
    created_object_type varchar(10) not null,
    updated_at timestamp not null,
    updated_object_id bigint not null,
    updated_object_type varchar(10) not null
) default charset = utf8mb4
    collate = utf8mb4_general_ci;
