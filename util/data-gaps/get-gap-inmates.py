import datetime
import sys
import os
import argparse
import csv
import requests
import psycopg2
from psycopg2 import extras
import xlsxwriter

from dotenv import load_dotenv

def getContent(itm):
  value = None
  if itm.contents and len(itm.contents) > 0:
    value = itm.contents[0]
  return value

def processOneColumn(itm, element):
  tag = element.label.contents[0].lower().replace(' ', '_')
  itm[tag] = getContent(element.span)

def processColumns(itm, elements):
  for e in elements:
    if (e.name == 'div'):
      processOneColumn(itm, e)
  return
  
def loadToDatabase(inmates):
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
  count = 0
  for m in inmates:
    count += 1
    if count%25 == 0:
      sys.stdout.write('...'+str(count))
      sys.stdout.flush()
    sql = 'insert into jaildata.daily_inmates ' + \
    '(import_date, name, age, gender, race, arrested, court_date, released, primary_charge, holding_facility, total_bond) ' +\
    'VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) returning id'
    cur.execute(sql, (
      m['import_date'], m['name'], m['age'], m['gender'], m['race'],
      m['arrested'], m['court_date'], m['released'], m['primary_charge'],
      m['holding_facility'], m['total_bond']
    ))
    id = cur.fetchone()[0]

    values = []
    for c in m['charges']:
      values.append((
          id, c['charge'], c['description'], c['status'], c['docket_number'],
          c['bond_type'], c['bond_status'], c['bond_amount']
        ))
    sql = 'insert into jaildata.daily_charges ' \
      '(defendant_id, charge, description, status, docket_number, bond_type, bond_status, bond_amount) ' + \
      'VALUES %s'
    try:
      extras.execute_values(cur, sql, values)
    except psycopg2.Error as e:
      print(e)

  conn.commit()
  cur.close()
  conn.close()
  print('')


cutoffDate = None
previousInmateMap = {}
checkPrevious = True

def createArgParser():
  parser = argparse.ArgumentParser()
  parser.add_argument('fileName1')
  parser.add_argument('fileName2')
  parser.add_argument('-i', '--importDate', help='IMPORTDATE of the form YYYY-MM-DD')
  parser.add_argument('-d', '--database', type=int, help='1 to load to the database, 0 to skip')
  return parser

def process_name(row, allCharges, importDate):
  inmate = {}
  inmate['book_id'] = row[1]
  inmate['import_date'] = importDate
  inmate['name'] = row[2].strip()
  inmate['age'] = row[3]
  inmate['race'] = row[4]
  inmate['gender'] = row[5]
  inmate['arrested'] = None
  inmate['court_date'] = None
  inmate['released'] = None
  inmate['holding_facility'] = row[6].strip()
  inmate['primary_charge'] = row[7].strip()
  inmate['total_bond'] = None
  inmate['charges'] = []
  chargesIn = allCharges[inmate['book_id']]
  if chargesIn is None:
    raise Exception('No charges found for booking id ', row[1])
  
  for item in chargesIn:
    charge = {}
    aDate = datetime.datetime.strptime(item[2], '%m/%d/%Y')
    if inmate['arrested'] is None:
      inmate['arrested'] = aDate;
    else:
      if aDate > inmate['arrested']:
        inmate['arrested'] = aDate

    ncharges = int(item[9])
    tmp = item[4].strip().split(':')
    if len(tmp) != 2:
      raise Exception('Weird charge string ', item[4])
    charge['charge'] = tmp[0]
    charge['description'] = tmp[1]
    charge['status'] = item[5].strip()
    charge['docket_number'] = item[3].strip()
    charge['bond_type'] = item[7].strip()
    charge['bond_status'] = item[8].strip()
    val = item[6]
    if val:
      val = val.replace(',','').replace('$','')
    charge['bond_amount'] = int(float(val))
    for i in range(ncharges):
      inmate['charges'].append(charge)
  return inmate

def getInmateList(inputFileName1, inputFileName2, importDate):
  # Available dates: 1/28/2023-2/1/2023 and 5/22/2023-6/2/2023
  print(importDate)
  iDate = datetime.datetime.strptime(importDate, '%Y-%m-%d')
  count = 0
  selected = 0
  charges = {}
  with open(inputFileName2) as csvfile:
    rdr = csv.reader(csvfile, delimiter=',')
    for row in rdr:
      if count > 0:
        bid = row[0].strip()
        if bid not in charges:
          charges[bid] = []
        charges[bid].append(row)
      count = count + 1
  print('Total ids in charges: ', len(charges))

  count = 0
  inmates = []
  with open(inputFileName1) as csvfile:
    rdr = csv.reader(csvfile, delimiter=',')
    for row in rdr:
      dt = None
      if count > 0:
        itm = {}
        dt = datetime.datetime.strptime(row[0], '%m/%d/%Y %I:%M:%S %p')
        if dt.date() == iDate.date():
          selected = selected + 1
          inmate = process_name(row, charges, importDate)
          if count < 2:
            print('')
            print(inmate)
            print('')
          inmates.append(inmate)
      count = count + 1


  print('Count is ', count, ' Selected is ', selected)
  print('Inmate list length: ', len(inmates))
  return inmates

############################
####    Main program    ####
############################

load_dotenv()

importFileName = None
importDate = datetime.datetime.now().strftime('%Y-%m-%d')
backDays = 1

parser = createArgParser()
args = parser.parse_args()
inputFileName1 = args.fileName1
inputFileName2 = args.fileName2
useDB = False if args.database == 0 else True

print(args)
if args.importDate:
  importDate = args.importDate

print('Input file: ', inputFileName1, ' input date: ', importDate, ', useDB = ', useDB)

inmates = getInmateList(inputFileName1, inputFileName2, importDate)

if useDB:
  loadToDatabase(inmates)
