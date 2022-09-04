import datetime
import sys
import os
import argparse
import psycopg2
from psycopg2 import extras
from dotenv import load_dotenv
import csv
import boto3

def get_daily_occupants():
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

  sql = 'select id, import_date, age, gender, race, arrested, primary_charge, total_bond from jaildata.daily_inmates'

  cur.execute(sql)
  result = cur.fetchall()
  print('Length: ', len(result))
  if len(result) > 0:
    print(result[0])

  conn.commit()
  cur.close()
  conn.close()
  
  return result

def get_daily_occupant_charges():
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

  sql = 'select defendant_id, charge, description, status, bond_type, bond_status, bond_amount from daily_charges'

  cur.execute(sql)
  result = cur.fetchall()
  print('Length: ', len(result))
  if len(result) > 0:
    print(result[0])

  conn.commit()
  cur.close()
  conn.close()
  
  return result

def get_charge_definitions():
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

  sql = 'select id, charge, description, class_type, class, level, nominal_level, min_level, max_level, estimate, violent, drugs, dwi, violation, not_primary_custodian, note from jaildata.charge_definitions'

  cur.execute(sql)
  result = cur.fetchall()
  print('Length: ', len(result))
  if len(result) > 0:
    print(result[0])

  conn.commit()
  cur.close()
  conn.close()
  
  return result

# Main Program
load_dotenv()

filedir = os.environ.get('TEMP_FILE_DIRECTORY')

daily_inmates = get_daily_occupants()
with open(filedir+'/daily_bcdf_occupants.csv', 'w', newline='') as csvfile:
    w = csv.writer(csvfile, delimiter=',',
                            quoting=csv.QUOTE_MINIMAL)
    w.writerow(['id', 'import_date', 'age', 'gender', 'race', 'arrested', 'primary_charge', 'total_bond'])
    for row in daily_inmates:
      w.writerow(row)

daily_inmates = get_daily_occupant_charges()

with open(filedir+'/daily_bcdf_occupant_charges.csv', 'w', newline='') as csvfile:
    w = csv.writer(csvfile, delimiter=',',
                            quoting=csv.QUOTE_MINIMAL)
    w.writerow(['defendant_id', 'charge', 'description', 'status', 'bond_type', 'bond_status', 'bond_amount'])
    for row in daily_inmates:
      w.writerow(row)

charge_definitions = get_charge_definitions()
with open(filedir+'/charge_definitions.csv', 'w', newline='') as csvfile:
    w = csv.writer(csvfile, delimiter=',',
                            quoting=csv.QUOTE_MINIMAL)
    w.writerow(['id', 'charge', 'description', 'class_type', 'class', 'level', 'nominal_level', 'min_level', 'max_level', 'estimate', 'violent', 'drugs', 'dwi', 'violation', 'not_primary_custodian', 'note'])
    for row in charge_definitions:
      w.writerow(row)

session = boto3.Session(
  aws_access_key_id= os.environ.get('AWS_ACCESS_KEY_ID'),
  aws_secret_access_key=os.environ.get('AWS_ACCESS_SECRET')
)

#Creating S3 Resource From the Session.
s3 = session.resource('s3')

print('Upload daily occupants')
object = s3.Object('on-background-data', 'buncombe-county-jail-data/daily_bcdf_occupants.csv')

result = object.put(Body=open(filedir+'/daily_bcdf_occupants.csv', 'rb'))

res = result.get('ResponseMetadata')

if res.get('HTTPStatusCode') == 200:
    print('File Uploaded Successfully')
else:
    print('File Not Uploaded')

print('Upload daily occupant charges')
object = s3.Object('on-background-data', 'buncombe-county-jail-data/daily_bcdf_occupant_charges.csv')

result = object.put(Body=open(filedir+'/daily_bcdf_occupant_charges.csv', 'rb'))

res = result.get('ResponseMetadata')

if res.get('HTTPStatusCode') == 200:
    print('File Uploaded Successfully')
else:
    print('File Not Uploaded')

print('Upload charge definitions')
object = s3.Object('on-background-data', 'buncombe-county-jail-data/bcdf_charge_definitions.csv')

result = object.put(Body=open(filedir+'/charge_definitions.csv', 'rb'))

res = result.get('ResponseMetadata')

if res.get('HTTPStatusCode') == 200:
    print('File Uploaded Successfully')
else:
    print('File Not Uploaded')