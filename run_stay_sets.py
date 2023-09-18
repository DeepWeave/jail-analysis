import datetime
import sys
import os
import argparse
import psycopg2
from psycopg2 import extras
from dotenv import load_dotenv

load_dotenv()

HOST = os.environ.get('JDB_HOST')
DBNAME = os.environ.get('JDB_NAME')
PASSWORD = os.environ.get('JDB_PASSWORD')
USER = os.environ.get('JDB_USER')

def computeYesterday(today):
  global cutoffDate
  day = datetime.datetime.strptime(today, '%Y-%m-%d')
  days = datetime.timedelta(1)
  cutoffDate = day - days
  return cutoffDate.strftime('%Y-%m-%d')

def computeDiff(date1, date2):
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
    print('id, name, gender, race')

  conn.commit()
  cur.close()
  conn.close()
  return staySet

def loadStarts(starts, startDate):
  
  conn = psycopg2.connect(
    host = HOST,
    dbname = DBNAME,
    password = PASSWORD,
    user = USER
  )
  cur = conn.cursor()
  print(startDate)
  for m in starts:
    sql = 'insert into jaildata.stays ' + \
    '(defendant_id, start_date, name, gender, race) VALUES (%s, %s, %s, %s, %s) returning id'
    print(m)
    cur.execute(sql, (m[0], startDate, m[1], m[2], m[3]))
    id = cur.fetchone()[0]
  conn.commit()
  cur.close()
  conn.close()

def loadEnds(ends, endDate):
  conn = psycopg2.connect(
    host = HOST,
    dbname = DBNAME,
    password = PASSWORD,
    user = USER
  )
  cur = conn.cursor()
  print('End date: ', endDate)
  for m in ends:
    sql = 'update jaildata.stays set end_date = %s ' + \
    'where name=%s AND gender=%s AND race=%s and end_date IS null'
    print(m)
    cur.execute(sql, (endDate, m[1], m[2], m[3]))

  conn.commit()
  cur.close()
  conn.close()

def loadStays():
  conn = psycopg2.connect(
    host = HOST,
    dbname = DBNAME,
    password = PASSWORD,
    user = USER
  )
  cur = conn.cursor()

  sql = 'select id, name, race, gender, start_date, end_date, defendant_id, use_flag from jaildata.stays'
  cur.execute(sql)
  stays = cur.fetchall()
  print('Entries: ', len(stays))
  if len(stays) > 0:
    id, name, race, gender, start_date, end_date, defendant_id, use_flag = stays[0]
    print(id, name, start_date, end_date)

  conn.commit()
  cur.close()
  conn.close()
  return stays

##############################################################
# Main program - for each stay, get all associated daily IDs
##############################################################

counter = 0
stays = loadStays()

conn = psycopg2.connect(
  host = HOST,
  dbname = DBNAME,
  password = PASSWORD,
  user = USER
)
cur = conn.cursor()
sql = 'truncate table jaildata.stay_sets'
cur.execute(sql)
today = datetime.datetime.now().strftime('%Y-%m-%d')
print(today)
for s in stays:
  endDate = s[5]
  if endDate is None:
    endDate = datetime.datetime.strptime(today, '%Y-%m-%d')

  print('record: ', s[1], s[3], s[2], s[4], endDate)
  sql = 'select id from jaildata.daily_inmates ' + \
  'where name = %s AND gender like %s AND race like %s and ' + \
  'import_date >= \'' + s[4].strftime('%Y-%m-%d') + '\' and ' + \
  'import_date <= \'' + datetime.datetime.strftime(endDate,'%Y-%m-%d') + '\' order by id asc'
#  print(sql, (s[1], s[3], s[2]))
  cur.execute(sql, (s[1], s[3], s[2]))
  res = cur.fetchall()
  ids = []
  for itm in res:
    ids.append(itm[0])
#  print(ids)
  sql = 'insert into jaildata.stay_sets values (%s, %s)'
  cur.execute(sql, (s[0], ids))
  counter = counter + 1
  # if counter > 4:
  #   break

conn.commit()
cur.close()
conn.close()
