import datetime
import sys
import os
import argparse
import psycopg2
from psycopg2 import extras
from dotenv import load_dotenv

def computeYesterday(today):
  global cutoffDate
  day = datetime.datetime.strptime(today, '%Y-%m-%d')
  days = datetime.timedelta(1)
  cutoffDate = day - days
  return cutoffDate.strftime('%Y-%m-%d')

def computeDiff(date1, date2):
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

  print('Dates = ', date1, date2)
  sql = 'select t1.id, t1.name, t1.gender, t1.race from (\
      select * from jaildata.daily_inmates where import_date = %s\
    ) t1 \
    left join ( \
      select name, gender, race from jaildata.daily_inmates where import_date = %s \
    ) t2 \
    on t2.name = t1.name and t2.gender = t1.gender and t2.race = t1.race \
    where t2.name is null'

  cur.execute(sql, (date1, date2))
  staySet = cur.fetchall()
  print('Entries: ', len(staySet))
  if len(staySet) > 0:
    id, name, gender, race = staySet[0]
    #print('id, name, gender, race')

  conn.commit()
  cur.close()
  conn.close()
  return staySet

def loadStarts(starts, startDate):
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
  for m in starts:
    sql = 'insert into jaildata.stays ' + \
    '(defendant_id, start_date, name, gender, race) VALUES (%s, %s, %s, %s, %s) returning id'
    cur.execute(sql, (m[0], startDate, m[1], m[2], m[3]))
    id = cur.fetchone()[0]
  conn.commit()
  cur.close()
  conn.close()

def loadEnds(ends, endDate):
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
  for m in ends:
    sql = 'update jaildata.stays set end_date = %s ' + \
    'where name=%s AND gender=%s AND race=%s and end_date IS null'
    cur.execute(sql, (endDate, m[1], m[2], m[3]))

  conn.commit()
  cur.close()
  conn.close()

####################################
# Main program
####################################

load_dotenv()
start_day = '2022-01-03'
today = datetime.datetime.now().strftime('%Y-%m-%d')
current_day = start_day
while current_day <= today:
  yesterday = computeYesterday(current_day)
  print(current_day, yesterday)

  # Find starting stays
  starts = computeDiff(current_day, yesterday)
  loadStarts(starts, current_day)

  # Find ending stays
  ends = computeDiff(yesterday, current_day)
  loadEnds(ends, yesterday)

  global newDate
  day = datetime.datetime.strptime(current_day, '%Y-%m-%d')
  days = datetime.timedelta(1)
  newDate = day + days
  current_day = newDate.strftime('%Y-%m-%d')

