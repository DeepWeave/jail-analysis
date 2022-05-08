# Jail Analysis

[Raising Jails series in CPP](https://carolinapublicpress.org/raising-jails/?mc_cid=953e4e3e12&mc_eid=56d4f57a2d)

## Check for new charge types:
  select * from (
    select distinct c.charge as ccharge, c.description as cdesc, d.charge as dcharge, d.description as ddesc from jaildata.daily_charges d
    left outer join jaildata.charge_definitions c
    on d.charge = c.charge AND d.description = c.description
  ) a
  where ccharge IS null or cdesc is null

## Adding in new charge types
insert into jaildata.charge_definitions (id, level, f_or_m, rank, flag, estimate, not_primary_custodian, 
										 notes, charge, description, is_violent, is_dwi, is_violation)
values 
    (40x, 'NONE', 'U', 0, 0, 0, 0, '','20-150.1|4552|NONE','IMPROPER PASSING ON RIGHT', 0,0,0),
    (40y, '2', 'M', 2, 0, 0, 0, '','20-63(G)|5573|2','COVERING/DISGUISING REG PLATE', 0,0,0)
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

From Trevor:
I checked out the jail web site. Here is a `curl` command line you can use to automatically retrieve the data:

curl -d '{"FilterOptionsParameters":{"IntersectionSearch":true,"SearchText":"","Parameters":[]},"IncludeCount":true,"PagingOptions":{"SortOptions":[{"Name":"LastName","SortDirection":"Ascending","Sequence":1}],"Take":10,"Skip":0}}' -H 'Content-Type: application/json;charset=UTF-8' https://buncombecountyso.policetocitizen.com/api/Inmates/23 > inmates.json

This saves the data as a JSON file. The `Take` parameter is what determines how many results to return and the `Skip` parameter indicates at which record to start retrieving. If you set `Take` to something like 500, it should return the entire dataset. Otherwise, there's a `Total` property at the root of the JSON object that indicates how many records there are and you should be able to easily write a script to do multiple API calls and page through the data.

Oh, and in case it matters, 23 is the agency ID. It looks like there is only one agency for this page, so it will always be 23.

update jaildata.charge_definitions
set f_or_m = 'F', rank=8, notes='F-I, assume F' where id = 354

