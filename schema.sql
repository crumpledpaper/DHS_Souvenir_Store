drop table if exists merchandise;
create table merchandise (
  pid integer primary key autoincrement,
  name string not null,
  price smallmoney not null,
  image blob
);

drop table if exists orders;
create table orders (
  pid integer primary key autoincrement,
  email string not null,
  merchandise_id integer not null,
  merchandise_name string not null,
  quantity integer not null,
  cost smallmoney not null,
  order_date date not null
);

drop table if exists user;
create table user (
  email string primary key,
  password string not null
);
