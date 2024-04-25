--CREATE USER bdh_user WITH LOGIN SUPERUSER NOINHERIT NOCREATEDB CREATEROLE REPLICATION VALID UNTIL '2099-01-01 01:32:01-08' PASSWORD 'St33lr0d';
--CREATE SCHEMA bdh_user AUTHORIZATION bdh_user;

DROP TABLE bdh_user.result_push_validation;
DROP TABLE bdh_user.result_nightly_build;
drop sequence bdh_user.result_history_id_seq;
DROP TABLE bdh_user.catagory;
DROP TABLE bdh_user.test;
DROP TABLE bdh_user.test_run;
DROP TABLE bdh_user.job;

CREATE SEQUENCE bdh_user.result_history_id_seq;

CREATE TABLE bdh_user.result_nightly_build (result_id bigint DEFAULT NEXTVAL('result_history_id_seq'), build_id varchar(50), start_time timestamp, end_time timestamp, build_state varchar(35), vora_version varchar(50), detail_url varchar(2000), commit_history text, failure_root_cause varchar(2000) DEFAULT '', raw_data text, project varchar(50) DEFAULT 'hanalite-releasepack', primary key (result_id));

CREATE TABLE bdh_user.result_push_validation (result_id bigint DEFAULT NEXTVAL('result_history_id_seq'), build_id varchar(50), start_time timestamp, end_time timestamp, project varchar(50) DEFAULT 'hanalite-releasepack', branch varchar(50), build_state varchar(35), vora_version varchar(50), detail_url varchar(2000), commit_id varchar(50), commit_author varchar(20), commit_history text, failure_root_cause varchar(2000) DEFAULT '', raw_data text, code_change_url varchar(500), primary key (result_id));

CREATE TABLE bdh_user.test (id uuid DEFAULT gen_random_uuid() NOT NULL, name character varying(255) NOT NULL, suite character varying(255) NOT NULL, owner character varying(50), catagory_id integer NOT NULL, primary key(id));

CREATE TABLE test_run (run_id uuid DEFAULT gen_random_uuid() NOT NULL, catagory_id integer NOT NULL, build_id character varying(50) NOT NULL, job_name character varying(255) NOT NULL, job_id uuid NOT NULL, test_id uuid NOT NULL, state character varying(50) NOT NULL, duration double precision NOT NULL, message text, stack text, failure_root_cause varchar(100) default null, primary key (run_id));

CREATE TABLE bdh_user.catagory (catagory_id integer not null, catagory_name varchar(50), project varchar(50) DEFAULT 'hanalite-releasepack', use_for varchar(50), primary key(catagory_id));
insert into bdh_user.catagory values (1, 'BDH Nightly Validation', 'hanalite-releasepack', 'NIGHTLY_VALIDATION');
insert into bdh_user.catagory values (2, 'BDH Push Validation', 'hanalite-releasepack', 'PUSH_VALIDATION');

CREATE TABLE bdh_user.job (id uuid DEFAULT gen_random_uuid() NOT NULL, name character varying(255) NOT NULL, state character varying(50) NOT NULL, console_url character varying(255) NOT NULL, build_id varchar(50), catagory_id integer not null, start_time timestamp, end_time timestamp, primary key(id));

create table bdh_user.groups (id uuid DEFAULT gen_random_uuid(), group_name varchar(20), permission varchar(100), primary key (id));
insert into bdh_user.groups(group_name, permission) values ('admin', '{"read":"1","update":"1","insert":"1","delete":"1"}');
insert into bdh_user.groups(group_name, permission) values ('public', '{"read":"1","update":"0","insert":"0","delete":"0"}');

create table bdh_user.users (id uuid DEFAULT gen_random_uuid() NOT NULL, user_name varchar(10) not null, group_id uuid not null, primary key (id));
--query bdh_user.groups and get group_id
--insert into bdh_user.users (user_name, group_id) values('i320129', '7d0b308e-6712-4ce3-9e5a-c68ad13df1bd');
--insert into bdh_user.users (user_name, group_id) values('i062958', 'ac980acf-7af2-4215-8fba-e01109412955');
