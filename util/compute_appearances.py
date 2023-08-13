import datetime
import sys
import os
import argparse
import psycopg2
from psycopg2 import extras
from dotenv import load_dotenv

holidays = {
  2022: {
    1: {
      17: True
    },
    4: {
      15: True
    },
    5: {
      30: True
    },
    7: {
      4: True
    },
    9: {
      5: True
    },
    11: {
      11: True, 24: True, 25: True
    },
    12: {
      23: True, 26: True, 27: True
    }
  },
  2023: {
    1: {
      2: True, 16: True
    },
    4: {
      7: True
    }, 
    7: {
      4: True
    }, 
    9: {
      4: True
    },
    11: {
      10: True, 23: True, 24: True
    },
    12: {
      25: True, 26: True, 27: True
    }
  },
  2024: {
    1: {
      1: True
    }
  }
}

firstAppearanceDays = 1
bondDays = 1

def computeNextAppearance(day, ndays): # today is string
  #day = datetime.datetime.strptime(today, '%Y-%m-%d')
  days = datetime.timedelta(ndays)
  nextAppearance = day + days
  found = False
  while (not found):
    dayOfWeek = nextAppearance.weekday()
    if dayOfWeek > 4:
      nextAppearance += datetime.timedelta(7-dayOfWeek)
    found = True
    # Now check if holiday
    if nextAppearance.year in holidays:
      if nextAppearance.month in holidays[nextAppearance.year]:
        if nextAppearance.day in holidays[nextAppearance.year][nextAppearance.month]:
          found = False
          nextAppearance += datetime.timedelta(1)
  # Now we have a non-holiday
  return nextAppearance.strftime('%Y-%m-%d')

####################################
# Main program
####################################

def computeAllAppearances(start):
  HOST = os.environ.get('JDB_HOST')
  DBNAME = os.environ.get('JDB_NAME')
  PASSWORD = os.environ.get('JDB_PASSWORD')
  USER = os.environ.get('JDB_USER')
  
  conn = psycopg2.connect(
    host = HOST,
    dbname = DBNAME,
    password = PASSWORD,
    user = USER
  )
  cur = conn.cursor()
  sql = 'select * from jaildata.stays order by start_date asc'
  cur.execute(sql)

  staySet = cur.fetchall()
  print('Entries: ', len(staySet))
  for i in range(len(staySet)):
    id, defendant_id, name, gender, race, startDate, endDate, useFlag, note = staySet[i]
    print(staySet[i])
    next = computeNextAppearance(startDate, bondDays)
    print (next)
    if i > 1000:
      break

  conn.commit()
  cur.close()
  conn.close()

load_dotenv()
startDate = '2022-01-18'
#nextDate = computeNextAppearance(startDate, bondDays)
computeAllAppearances(startDate)
#print(startDate, nextDate)
