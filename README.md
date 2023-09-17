# Jail Analysis

This Buncombe County jail analysis project currently contains 2 scripts. 

The first, ```get-daily-inmates.py```, extracts a list of inmate and charges data from a previously downloaded HTML file and uploads it to a database. It also creates a formatted Excel file of everyone with an arrest date within the previous day (except on Mondays when it does 3 days; this can be overridden with the ```-b``` option).

The second, ```compute-stay-starts.py``` looks at entries in the database as of a specified date (hardcoded for now) and creates/updates jail stays that start/end since the previous day.

I run both scripts each morning (typically between 6 and 7:30) and then send the Excel file to one of the public defenders for use during first appearances that day. For consistency of the analysis what is most important is to capture the data each morning. 


## Data Notes
I have daily downloads for almost every day since 1/3/2022. There are a few dates with issues

Stays that began on 1/3/22 should not be used since we don't know when they actually began. 

For the following date ranges I was unable to do daily downloads. Lee Crayton of Buncombe County provided bookings data for these dates, but the charges listed there are as of the date he pulled the data, not the date of booking, so they should not be used for charge analysis (they are also as of midnight, not later in the morning):

- start_date >= '2023-01-28' and start_date <= '2023-02-01' (the site was down). 
- start_date >= '2023-05-23' and start_date <= '2023-06-02' (I was on vacation)

Data for the following dates were downloaded at a different time than normal:
- start_date = '2023-09-16' - downloaded at 6:30pm

