import datetime
import sys
import os
import argparse
from bs4 import BeautifulSoup
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
  
def processCharges(rows):
  charges = []
  for row in rows:
    charge = {}
    cols = list(filter(lambda r: r.name == 'td', row.contents))
    charge['charge'] = getContent(cols[0])
    charge['description'] = getContent(cols[1])
    charge['status'] = getContent(cols[2])
    charge['docket_number'] = getContent(cols[3])
    charge['bond_type'] = getContent(cols[4])
    charge['bond_status'] = getContent(cols[5])
    charge['bond_amount'] = getContent(cols[6])
    val = getContent(cols[6])
    if val:
      val = val.replace(',','').replace('$','')
    charge['bond_amount'] = int(float(val) * 100)

    charges.append(charge)
  return charges

races = {
  'WHITE': 'W',
  'BLACK': 'B',
  'ASIAN / PACIFIC ISLANDER/': 'A',
  'AMERICAN INDIAN / ALASKAN NATIVE': 'I',
  'UNKNOWN': 'U',
  'DO NOT USE --LOOKING FOR ERRORS': 'U'
}

def processInmateRecord(itm, importDate):
  inmate = {}
  inmate['import_date'] = importDate
  inmate['name'] = itm['name'].strip()
  inmate['age'] = int(itm['age'])
  inmate['gender'] = itm['gender'][0]
  if itm['race'] not in races:
    raise('Unknown race ', itm['race'])
  inmate['race'] = races[itm['race']]
  val = itm['arrested']
  inmate['arrested'] = val if val is None else datetime.datetime.strptime(val, '%m/%d/%Y').strftime('%Y-%m-%d')
  val = itm['court_date']
  inmate['court_date'] = val if val is None else datetime.datetime.strptime(val, '%m/%d/%Y').strftime('%Y-%m-%d')
  val = itm['released']
  inmate['released'] = val if val is None else datetime.datetime.strptime(val, '%m/%d/%Y').strftime('%Y-%m-%d')
  inmate['primary_charge'] = itm['primary_charge'].strip()
  inmate['holding_facility'] = itm['holding_facility'].strip() if itm['holding_facility'] else None
  val = None
  val = itm['total_bond_amount:']
  if val:
    val = val.replace(',','').replace('$','')
  inmate['total_bond'] = int(float(val) * 100)
  inmate['charges'] = itm['charges']
  return inmate

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

def checkDate(itm):
  global cutoffDate
  val = False
  if itm['arrested']:
    iDate = datetime.datetime.strptime(itm['arrested'], '%Y-%m-%d').date()
    val =  iDate >= cutoffDate
  return val

def chargeLine(c):
  line = c['charge'] + '; ' + c ['description'] + '; ' 
  line += (c['status'] if c['status'] else 'None') + '; '
  line += (c['docket_number'] if c['docket_number'] else 'None') + '; '
  line += (c['bond_type'] if c['bond_type'] else '?') + '; '
  line += ("${:,.2f}".format(c['bond_amount']/100) if c['bond_amount'] else '-') + '\n'
  return line

def computeBackDays(defaultValue):
  if defaultValue:
    return defaultValue
  today = datetime.date.today()
  backDays = 3 if today.weekday() == 0 else 1
  return backDays

def createRecentArrestsFile(inmates, backdays):
  global cutoffDate
  today = datetime.date.today()
#  backdays = 3 if today.weekday() == 0 else 1
  days = datetime.timedelta(backdays)
  cutoffDate = today - days
  latest = list(filter(checkDate, inmates))
  print('Total arrests over past ', backdays, ' days: ', len(latest))
  rows = []
  for itm in latest:
    inmate = {}
    inmate['cal'] = None
    inmate['name'] = itm['name']
    inmate['atty_on_this'] = None
    inmate['atty_on_other'] = None
    inmate['notes'] = None
    inmate['PDO appt\'d'] = None
    inmate['total_bond'] = "${:,.2f}".format(itm['total_bond']/100)
    inmate['bond chg'] = None
    inmate['add_to_bond_cal'] = None
    inmate['charges'] = ''
    inmate['gender'] = itm['gender']
    inmate['age'] = itm['age']
    inmate['race'] = itm['race']
    inmate['arrested'] = itm['arrested']
    inmate['court_date'] = itm['court_date']
    inmate['released'] = itm['released']
    inmate['holding_facility'] = itm['holding_facility']

    for c in itm['charges']:
      inmate['charges'] += chargeLine(c)
    rows.append(inmate)
  prefix = 'latest_arrests-' + str(backDays) + 'day-'
  workbook = xlsxwriter.Workbook(prefix + today.strftime('%Y-%m-%d') + '.xlsx')
  worksheet = workbook.add_worksheet()
  count = 0
  for inmate in rows:
    if count == 0:
      header = list(inmate.keys())
      worksheet.write_row(count, 0, header)
    worksheet.write_row(count + 1, 0, inmate.values())
    count += 1
  workbook.close()

def createArgParser():
  parser = argparse.ArgumentParser()
  parser.add_argument('fileName')
  parser.add_argument('-i', '--importDate', help='IMPORTDATE of the form YYYY-MM-DD')
  parser.add_argument('-b', '--backDays', type=int, help='Default is 3 days on Monday, 1 day otherwise')
  parser.add_argument('-d', '--database', type=int, help='1 to load to the database, 0 to skip')
  return parser

# Main program

load_dotenv()

importFileName = None
importDate = datetime.datetime.now().strftime('%Y-%m-%d')
backDays = 1

parser = createArgParser()
args = parser.parse_args()
inputFileName = args.fileName
useDB = False if args.database == 0 else True
backDays = computeBackDays(args.backDays)
if args.importDate:
  importDate = args.importDate

print('Input file: ', inputFileName, ' input date: ', importDate, ', backDays = ', backDays, 'useDB = ', useDB)

file = open(inputFileName)
pageText = file.read()
file.close()
soup = BeautifulSoup(pageText, 'html.parser')

nms = soup.find_all("div", "p2c-card-title")
cards = soup.find_all("md-card", "p2c-card")
print('Total inmates: ', len(cards))
inmates = []
for card in cards:
  itm = {}
  for c1 in card.children:
    if c1.name == 'md-card-title':
      for c2 in c1.children:
        if c2.name == 'md-card-title-text':
          count = 0
          children = list(filter(lambda r: r.name == 'div', c2.contents))
          if 'p2c-card-title' not in children[0]['class']:
            raise Exception('First div of title text is not the card title')
          itm['name'] = children[0].contents[0]
          processColumns(itm, children[2].contents)
          processColumns(itm, children[3].contents)
          processColumns(itm, children[4].contents)
          processOneColumn(itm, children[5])
          processColumns(itm, children[6].contents)
          processOneColumn(itm, children[7])
          processOneColumn(itm, children[8])
    if c1.name == 'md-card-content':
      table = c1.tbody
      rows = list(filter(lambda r: r.name == 'tr', table.contents))
      rows.pop(0)
      itm['charges'] = processCharges(rows)
  inmates.append(processInmateRecord(itm, importDate))

createRecentArrestsFile(inmates, backDays)
if useDB:
  loadToDatabase(inmates)



