# Jail Analysis

[Raising Jails series in CPP](https://carolinapublicpress.org/raising-jails/?mc_cid=953e4e3e12&mc_eid=56d4f57a2d)


select import_date, count(id) from jaildata.daily_inmates
group by import_date

From Trevor:
I checked out the jail web site. Here is a `curl` command line you can use to automatically retrieve the data:

curl -d '{"FilterOptionsParameters":{"IntersectionSearch":true,"SearchText":"","Parameters":[]},"IncludeCount":true,"PagingOptions":{"SortOptions":[{"Name":"LastName","SortDirection":"Ascending","Sequence":1}],"Take":10,"Skip":0}}' -H 'Content-Type: application/json;charset=UTF-8' https://buncombecountyso.policetocitizen.com/api/Inmates/23 > inmates.json

This saves the data as a JSON file. The `Take` parameter is what determines how many results to return and the `Skip` parameter indicates at which record to start retrieving. If you set `Take` to something like 500, it should return the entire dataset. Otherwise, there's a `Total` property at the root of the JSON object that indicates how many records there are and you should be able to easily write a script to do multiple API calls and page through the data.

Oh, and in case it matters, 23 is the agency ID. It looks like there is only one agency for this page, so it will always be 23.