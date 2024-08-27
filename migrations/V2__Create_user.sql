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

    joined_at timestamp,
    additional_info JSON    not null,

    removed_flag tinyint not null,
    removed_at timestamp,

    created_at timestamp not null,
    created_by_id bigint not null,
    created_object_type varchar(10) not null,
    updated_at timestamp not null,
    updated_by_id bigint not null,
    updated_object_type varchar(10) not null
) default charset = utf8mb4
    collate = utf8mb4_general_ci;

insert into user (id, name, use_flag, login_id, password,
removed_flag, additional_info,
created_at, created_by_id, created_object_type, updated_at, updated_by_id, updated_object_type)
values (1, '테스트유저', 1, 'tester', '$2b$12$oquiOuftjG94Nepvwm1s3OJe5mt40rNI2VuDRaIlL11NDbaYzKIN2',
0, '{}',
 now(), 1, 'user', now(), 1, 'user');

