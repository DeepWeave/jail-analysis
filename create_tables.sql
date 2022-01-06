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

insert into jaildata.daily_inmates (import_date, name, age, gender, race, height, weight, arrested, court_date,
released, primary_charge, holding_facility, total_bond)
values (
	'2022-01-03', 'ZOLNOSKI, NOAH ALEXANDER ', 24, 'M', 'W', 
	'5'' 10"', '210 lbs', '2021-07-14', null, null, '14-415.1|5224|G POSSESSION OF FIREARM BY FELON',
	'CENTRAL', 5000
)
