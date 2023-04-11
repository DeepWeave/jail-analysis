# Some Helpful SQL queries

## Check for new charge types:
    select * from (
      select distinct c.charge as ccharge, c.description as cdesc, d.charge as dcharge, d.description as ddesc from jaildata.daily_charges d
      left outer join jaildata.charge_definitions c
      on d.charge = c.charge AND d.description = c.description
    ) a
    where ccharge IS null or cdesc is null
    select count (*) from stays where end_date is null
    select count (*) from daily_inmates where import_date = '2023-03-08'
## Adding in new charge types
insert into jaildata.charge_definitions (id, class, class_type, level, estimate, not_primary_custodian, 
										 note, charge, description, violent, dwi, drugs, theft, violation, min_level,
										 max_level, nominal_level, vet)
values 
    (561, '2', 'M', 2, 0, 0, '','20-7|5523|2','OPERATORS LIC VIOL', 0,0,0,0,0, 2, 2, 2, 1)
  ;
-- select * from charge_definitions order by id desc
  
## Updating multiple charge types
update jaildata.charge_definitions a
set f_or_m = c.f_or_m, rank=c.rank, flag=c.flag, estimate = c.estimate, 
	not_primary_custodian = c.not_primary_custodian, notes=c.notes, is_violent = c.violent
from (values
		(32x,'F',11,1,1,0,'All over the map, but max seems to be class C felony', 0),
		(32y,'F',12,1,1,0,'Marked as *violent*. Again all over the map, but max is B1 felony', 1),
		(32z,'M',1,1,1,0,'M-1 - flag', 0)
	 ) as c(id, f_or_m, rank, flag, estimate, not_primary_custodian, notes, violent)
where a.id = c.id


## Daily inmate count
select import_date, count(id) from jaildata.daily_inmates
group by import_date order by import_date desc

OR

select import_date, count(id) from jaildata.daily_inmates a
LEFT JOIN charges_summary c on a.id = c.defendant_id
where c.not_primary_custodian = 1
group by import_date order by import_date desc

## Get level from charge field
select distinct 
  substring(charge,'\|([^\|]*$)') as lvl,
  charge, description from jaildata.daily_charges

## Distribution of stay lengths
  select days, count(name) from (
    select name,
    DATE_PART('day', end_date::timestamp - start_date) as days
    from jaildata.stays
    where use_flag = 1 and end_date is not null ) s
    group by days
    order by days asc
	
## Multiple stay names:
  select * from (
    select name, MIN(days) as min, MAX(days) as max, STRING_AGG(days::text, ','), count(name) as cnt
    from (
      select name, DATE_PART('day', end_date::timestamp - start_date) as days
      from jaildata.stays
      where use_flag = 1 and end_date is not null
    ) a
  group by a.name) b
  where cnt > 1
  ORDER BY cnt desc

## Entries & Exits
  select count(defendant_id), start_date from jaildata.stays
  where use_flag = 1 and end_date is not null
  group by start_date
  order by start_date asc

  select count(defendant_id), end_date from jaildata.stays
  where use_flag = 1 and end_date is not null
  group by end_date
  order by end_date asc

## Sent to Lee 3/30
select s.start_date as date, d.arrested, s.name,
	c.charge, c.description, c.docket_number, c.status, c.bond_type, c.bond_status, c.bond_amount,
	 s.race, s.gender
from stays s
left join daily_charges c
on s.defendant_id = c.defendant_id
left join daily_inmates d
on d.id = s.defendant_id
where s.use_flag = 1

# Count by race over time
select date, race, group_total, total, round(100.0 * group_total/total, 2) as pct from (
	select * from (
		select import_date as date, race, count(name) as group_total from (
			select import_date, name, age, gender, race from daily_inmates
		) a
		group by import_date, race
	) d
	left join (
		select import_date, count(name) as total from (
			select * from daily_inmates
		) b
		group by import_date
	) c on date = c.import_date
) x
where race = 'W'
order by date asc, race desc

# Count by gender over time
select date, gender, group_total, total, round(100.0 * group_total/total, 2) as pct from (
	select * from (
		select import_date as date, gender, count(name) as group_total from (
			select import_date, name, age, gender, race from daily_inmates
		) a
		group by import_date, gender
	) d
	left join (
		select import_date, count(name) as total from (
			select * from daily_inmates
		) b
		group by import_date
	) c on date = c.import_date
) x
where gender = 'F'
order by date asc, gender desc


# For Nolan
select s.*, c.* from stays_summarized s
  left join (
select defendant_id as defendant_id2, min(rank) as min_rank, max(rank) as max_rank, count(*) as total_charges,
string_agg(charge, E'\n') as charges,
string_agg(description, E'\n') as descriptions,
sum(abs(violent)) as sum_violent,
sum(drugs) as sum_drugs,
sum(theft) as sum_theft,
sum(dwi) as sum_dwi, sum(violation) as sum_violation,
sum(not_primary_custodian) as sum_not_primary_custodian,
sum(is_pretrial) as sum_pretrial
from daily_charges_coded
group by defendant_id2
  ) c
  on s.defendant_id = c.defendant_id2 where s.rank = c.max_rank
order by defendant_id
