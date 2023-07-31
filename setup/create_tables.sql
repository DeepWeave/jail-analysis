CREATE TABLE jaildata.daily_inmates (
    id serial PRIMARY KEY,
    import_date date,
    name text NOT NULL,
    age integer,
    gender varchar(1),
    race varchar(2),
    height varchar(10),
    weight varchar(10),
    arrested date,
    court_date date,
    released date,
    primary_charge text,
    holding_facility varchar(10),
    total_bond integer
);

CREATE TABLE jaildata.daily_charges (
  defendant_id integer,
  charge text,
  description text,
  status varchar(32),
  docket_number varchar(128),
  bond_type varchar(32), 
  bond_status varchar(32),
  bond_amount integer
);

CREATE TABLE jaildata.stays (
  id serial PRIMARY KEY,
  defendant_id integer,
  name text NOT NULL,
  gender varchar(1),
  race varchar(2),
  start_date date,
  end_date date,
  use_flag integer default 1
)

CREATE TABLE jaildata.charge_definitions (
  id serial PRIMARY KEY,
  rank integer, 
  level varchar(5),
  charge text,
  description text,
  is_violent smallint,
  is_dwi smallint,
  is_violation smallint
)
