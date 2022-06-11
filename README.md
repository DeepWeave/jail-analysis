# Jail Analysis

This Buncombe County jail analysis project currently contains 2 scripts. 

The first, ```get-daily-inmates.py```, extracts a list of inmate and charges data from a previously downloaded HTML file and uploads it to a database. It also creates a formatted Excel file of everyone with an arrest date within the previous day (except on Mondays when it does 3 days; this can be overridden with the ```-b``` option).

The second, ```compute-stay-starts.py``` looks at entries in the database as of a specified date (hardcoded for now) and creates/updates jail stays that start/end since the previous day.

I run both scripts each morning (typically between 6 and 7:30) and then send the Excel file to one of the public defenders for use during first appearances that day. For consistency of the analysis what is most important is to capture the data each morning. The goal is to have at least a year of daily data (the project started on 1/3/2022). 
