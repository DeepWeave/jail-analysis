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
  inmate['released'] = None
  val = None
  if 'released' in itm:
    val = itm['released']
  if 'expected_release' in itm:
    val = itm['expected_release']
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
previousInmateMap = {}
checkPrevious = True

def checkDate(itm):
  global cutoffDate
  global previousInmateMap

  val = False
  if itm['arrested']:
    iDate = datetime.datetime.strptime(itm['arrested'], '%Y-%m-%d').date()
    val =  iDate >= cutoffDate
  if checkPrevious and not val:
    key = itm['name'] + itm['gender'] + itm['race']
    val = key not in previousInmateMap
    if val:
      print(key)

  return val

def chargeLine(c):
  charge = c['charge']
  if charge is None:
    charge = ''
  line = charge + '; ' + c ['description'] + '; ' 
  line += (c['status'] if c['status'] else 'None') + '; '
  line += (c['docket_number'] if c['docket_number'] else 'None') + '; '
  line += (c['bond_type'] if c['bond_type'] else '?') + '; '
  line += ("${:,.2f}".format(c['bond_amount']/100) if c['bond_amount'] else '-') + '\n'
  return line

def computeBackDays(defaultValue):
  if defaultValue is not None:
    return defaultValue
  today = datetime.date.today()
  backDays = 3 if today.weekday() == 0 else 1
  return backDays

def createColumnFormats(sample, workbook, worksheet):
  colCount = len(sample.keys())
#  columnFormats = [{ 'width': 40, 'format': workbook.add_format()}] * colCount
#  print(columnFormats)
  baseFormat = workbook.add_format({'font_color': 'black', 'text_wrap':True, 'valign': 'top'})
  baseFormat.set_border(1)
  i_format = workbook.add_format({'font_color': 'black', 'text_wrap':True, 'valign': 'top', 'num_format': 'mm/dd'})
  i_format.set_border(1)

  worksheet.freeze_panes(1, 0)
  i = 0
  worksheet.set_column(i, i, 5, baseFormat) #pull
  i = i + 1
  worksheet.set_column(i, i, 5, baseFormat) #cal
  i = i + 1
  worksheet.set_column(i, i, 22, baseFormat) #name
  i = i + 1
  worksheet.set_column(i, i, 6, baseFormat) #ADMN
  i = i + 1
  worksheet.set_column(i, i, 7, baseFormat) #atty-this
  i = i + 1
  worksheet.set_column(i, i, 7, baseFormat) #atty-other
  i = i + 1
  worksheet.set_column(i, i, 20, baseFormat) #notes
  i = i + 1
  worksheet.set_column(i, i, 8, baseFormat) #PDO
  i = i + 1
  worksheet.set_column(i, i, 7, i_format) #Ct-date
  i = i + 1
  worksheet.set_column(i, i, 10, baseFormat) #Conflict
  i = i + 1
  worksheet.set_column(i, i, 10, baseFormat) #Total bond
  i = i + 1
  worksheet.set_column(i, i, 7, baseFormat) #Bond chg
  i = i + 1
  worksheet.set_column(i, i, 7, baseFormat) #add to bond cal
  i = i + 1
  worksheet.set_column(i, i, 100, baseFormat) #charges
  i = i + 1
  worksheet.set_column(i, i, 3, baseFormat) #gender
  i = i + 1
  worksheet.set_column(i, i, 3, baseFormat) #age
  i = i + 1
  worksheet.set_column(i, i, 3, baseFormat) #race
  i = i + 1
  worksheet.set_column(i, i, 9, baseFormat) #arrested
  i = i + 1
  worksheet.set_column(i, i, 9, baseFormat) #court data
  i = i + 1
  worksheet.set_column(i, i, 9, baseFormat)# released
  i = i + 1
  worksheet.set_column(i, i, 9, baseFormat) #holding facility

  a_no = workbook.add_format({'bg_color': '#DCDCDC'})
  a_yes = workbook.add_format({'bg_color': '#ffeb9c'})
  b_misd = workbook.add_format({'font_color': 'lightslategray', 'bold': True})
  b_ad1a = workbook.add_format({'font_color': '#244061', 'bold': True})
  b_ad2b = workbook.add_format({'font_color': '#02b050', 'bold': True})
  b_ad3b = workbook.add_format({'font_color': '#974805', 'bold': True})
  b_9999 = workbook.add_format({'font_color': '#974805', 'bold': True})
  all_x = workbook.add_format({'bg_color': '#DCDCDC'})
  d_yes = workbook.add_format({'font_color': '#02b050'})
  d_na = workbook.add_format({'bg_color': '#DCDCDC'})
  e_none = workbook.add_format({'bg_color': '#c6efce'})
  h_yes = workbook.add_format({'bg_color': '#ffeb9c'})
  h_noneed = workbook.add_format({'bg_color': '#d8d8d8'})
  h_waive = workbook.add_format({'bg_color': '#d8d8d8'})
  n_sentenced = workbook.add_format({'bg_color': '#c6efce'})
  n_nobond = workbook.add_format({'bg_color': '#ffc7ce'})
  n_support = workbook.add_format({'bg_color': '#cef0cc'})

  j_na = workbook.add_format({'bg_color': '#DCDCDC'})
  j_xa = workbook.add_format({'bg_color': '#ffeb9c'})
  m_no = workbook.add_format({'bg_color': '#DCDCDC'})
  m_yes = workbook.add_format({'bg_color': '#ffeb9c'})
  d_no = workbook.add_format({'bg_color': '#DCDCDC'})

  worksheet.conditional_format('A2:A1000', {'type': 'text', 'criteria': 'containing', 'value': 'no', 'format': a_no})
  worksheet.conditional_format('A2:A1000', {'type': 'text', 'criteria': 'containing', 'value': 'yes', 'format': a_yes})
  worksheet.conditional_format('B2:B1000', {'type': 'cell', 'criteria': '==', 'value': '"MISD"', 'format': b_misd})
  worksheet.conditional_format('B2:B1000', {'type': 'cell', 'criteria': '==', 'value': '"AD1A"', 'format': b_ad1a})
  worksheet.conditional_format('B2:B1000', {'type': 'cell', 'criteria': '==', 'value': '"AD2B"', 'format': b_ad2b})
  worksheet.conditional_format('B2:B1000', {'type': 'cell', 'criteria': '==', 'value': '"AD3B"', 'format': b_ad3b})
  worksheet.conditional_format('B2:B1000', {'type': 'cell', 'criteria': '==', 'value': '"9999"', 'format': b_9999})
  worksheet.conditional_format('A2:Z1000', {'type': 'cell', 'criteria': '==', 'value': '"x"', 'format': all_x})
  worksheet.conditional_format('D2:D1000', {'type': 'text', 'criteria': 'containing', 'value': 'yes', 'format': d_yes})
  worksheet.conditional_format('D2:D1000', {'type': 'text', 'criteria': 'containing', 'value': 'n/a', 'format': d_na})
  worksheet.conditional_format('E2:E1000', {'type': 'text', 'criteria': 'containing', 'value': 'none', 'format': e_none})
  worksheet.conditional_format('H2:H1000', {'type': 'text', 'criteria': 'containing', 'value': 'yes', 'format': h_yes})
  worksheet.conditional_format('H2:H1000', {'type': 'text', 'criteria': 'containing', 'value': 'no need', 'format': h_noneed})
  worksheet.conditional_format('H2:H1000', {'type': 'text', 'criteria': 'containing', 'value': 'waive', 'format': h_waive})

  worksheet.conditional_format('N2:N1000', {'type': 'text', 'criteria': 'containing', 'value': 'sentenced', 'format': n_sentenced})
  worksheet.conditional_format('N2:N1000', {'type': 'text', 'criteria': 'containing', 'value': 'no bond', 'format': n_nobond})
  worksheet.conditional_format('N2:N1000', {'type': 'text', 'criteria': 'containing', 'value': 'support', 'format': n_support})
  worksheet.conditional_format('J2:J1000', {'type': 'text', 'criteria': 'containing', 'value': 'n/a', 'format': j_na})
  worksheet.conditional_format('J2:J1000', {'type': 'text', 'criteria': 'containing', 'value': 'xa', 'format': j_xa})
  worksheet.conditional_format('M2:M1000', {'type': 'text', 'criteria': 'containing', 'value': 'no', 'format': m_no})
  worksheet.conditional_format('M2:M1000', {'type': 'text', 'criteria': 'containing', 'value': 'yes', 'format': m_yes})
  worksheet.conditional_format('D2:D1000', {'type': 'text', 'criteria': 'containing', 'value': 'no', 'format': d_no})
  
def createRecentArrestsFile(inmates, backdays, importDate):
  global cutoffDate
  today = datetime.date.today()
  today = datetime.datetime.strptime(importDate, '%Y-%m-%d').date()
  days = datetime.timedelta(backdays)
  cutoffDate = today - days
  print('Cut off date = ', cutoffDate)
  latest = list(filter(checkDate, inmates))
  print('Total arrests over past ', backdays, ' days: ', len(latest))
  pdo = ['', 'yes', 'no need', 'who knows', 'yes', 'no need']
  rows = []
  for itm in latest:
    inmate = {}
    inmate['pull?'] = None
    inmate['cal'] = None
    inmate['name'] = itm['name']
    inmate['ADMN'] = None
    inmate['atty on this'] = None
    inmate['atty on other'] = None
    inmate['notes'] = None
    inmate['PDO appt\'d'] = None
    inmate['Ct Date'] = None
    inmate['Conflict Info'] = None
    inmate['total bond'] = "${:,.2f}".format(itm['total_bond']/100)
    inmate['bond chg'] = None
    inmate['add to bond cal'] = None
    inmate['charges'] = ''
    inmate['gender'] = itm['gender']
    inmate['age'] = itm['age']
    inmate['race'] = itm['race']
    inmate['arrested'] = itm['arrested']
    inmate['court date'] = itm['court_date']
    inmate['released'] = itm['released']
    inmate['holding facility'] = itm['holding_facility']
    inmate['date generated'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    for c in itm['charges']:
      inmate['charges'] += chargeLine(c)
    rows.append(inmate)
  prefix = '-latest_arrests-ej-' + str(backDays) + 'day'
  workbook = xlsxwriter.Workbook(today.strftime('%Y-%m-%d') + prefix + '.xlsx')
  worksheet = workbook.add_worksheet()
  header = '&LPage &P of &N' + '&CFIRST APP - ' + today.strftime('%Y-%m-%d')

  worksheet.set_landscape()
  worksheet.set_header(header)
  worksheet.print_area('A1:M10000')

  columnFormats = createColumnFormats(rows[0], workbook, worksheet)
  count = 0
  for inmate in rows:
    if count == 0:
      header = list(inmate.keys())
      worksheet.write_row(count, 0, header, workbook.add_format({'font_color': 'black', 'bold': True}))
    worksheet.write_row(count + 1, 0, inmate.values())
    count += 1
  workbook.close()

def createArgParser():
  parser = argparse.ArgumentParser()
  parser.add_argument('fileName')
  parser.add_argument('-i', '--importDate', help='IMPORTDATE of the form YYYY-MM-DD')
  parser.add_argument('-b', '--backDays', type=int, help='Default is 3 days on Monday, 1 day otherwise')
  parser.add_argument('-d', '--database', type=int, help='1 to load to the database, 0 to skip')
  parser.add_argument('-a', '--arrests', type=int, help='1 to create the arrests file, 0 to skip')
  return parser

def computeYesterday(today):
  global cutoffDate
  day = datetime.datetime.strptime(today, '%Y-%m-%d')
  days = datetime.timedelta(1)
  cutoffDate = day - days
  return cutoffDate.strftime('%Y-%m-%d')

def getPreviousInmates(backdays, importDate):
  global previousInmateMap
  today = datetime.date.today()
  today = datetime.datetime.strptime(importDate, '%Y-%m-%d').date()

  days = datetime.timedelta(backdays)
  prevDate = today - days

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

  print('Get inmates from yesterday: ', prevDate)
  sql = 'select name, gender, race from jaildata.daily_inmates where (import_date = %s)'

  cur.execute(sql, (prevDate,)) # Note the comma! Keeps it a tuple, apparently
  staySet = cur.fetchall()

  conn.commit()
  cur.close()
  conn.close()
  previousInmateMap = {}
  for inmate in staySet:
    name, gender, race = inmate
    key = name + gender + race
    previousInmateMap[key] = inmate
  
  print('Previous inmate count: ', len(previousInmateMap))
  return previousInmateMap


def getInmateList(inputFileName):
  file = open(inputFileName)
  pageText = file.read()
  file.close()
  soup = BeautifulSoup(pageText, 'html.parser')

  cards = soup.find_all("mat-card", "mat-mdc-card")
  print('Total inmates: ', len(cards))
  inmates = []
  for card in cards:
    itm = {}
    for c1 in card.descendants:
      if (c1.name == 'div' and c1.has_attr('id')):
        if (c1['id'] == 'inmate-name'):
          itm['name'] = getContent(c1)
      elif (c1.name == 'span' and c1.has_attr('id')):
        if (c1['id'] == 'age-span'):
          itm['age'] = getContent(c1)
        if (c1['id'] == 'gender-span'):
          itm['gender'] = getContent(c1)
        if (c1['id'] == 'race-span'):
          itm['race'] = getContent(c1)
        if (c1['id'] == 'arrest-date-span'):
          itm['arrested'] = getContent(c1)
        if (c1['id'] == 'release-date'):
          itm['released'] = None
          if (len(c1.contents) > 0):
            itm['released'] = getContent(c1)
        if (c1['id'] == 'primary-charge-span'):
          itm['primary_charge'] = getContent(c1)
        if (c1['id'] == 'holding-facility-span'):
          itm['holding_facility'] = getContent(c1)
        if (c1['id'] == 'total-bond-amount'):
          itm['total_bond_amount:'] = getContent(c1)
        if (c1['id'] == 'court-date-label'):
          c2 = c1.next_sibling
          itm['court_date'] = getContent(c2)
      # 3/6/2024: The following no longer applies (they fixed the inconsistency
      # see the lines just preceding this), but leaving for now
      elif (c1.name == 'label' and c1.has_attr('id')):
        if (c1['id'] == 'court-date-label'):
          c2 = c1.next_sibling
          itm['court_date'] = getContent(c2)
      elif (c1.name == 'table' and c1.has_attr('class') and 'charge' in c1['class']):
        table = c1
        rows = list(filter(lambda r: r.name == 'tr', table.contents))
        rows.pop(0)
        itm['charges'] = processCharges(rows)

    inmates.append(processInmateRecord(itm, importDate))
  return inmates

def checkIntegrity(inmates):
  ok = True
  testInmates = {}
  for m in inmates:
    if m['name'] not in testInmates:
      testInmates[m['name']] = m
    else:
      print('!!!!!!!!!!! INTEGRITY ERROR !!!!!!!!!!!')
      print(m['name'], ' appears twice!')
      print('!!!!!!!!!!! INTEGRITY ERROR !!!!!!!!!!!')
      ok = False
  return ok

############################
####    Main program    ####
############################

load_dotenv()

importFileName = None
importDate = datetime.datetime.now().strftime('%Y-%m-%d')
backDays = 1

parser = createArgParser()
args = parser.parse_args()
inputFileName = args.fileName
useDB = False if args.database == 0 else True
doArrests = False if args.arrests == 0 else True
backDays = computeBackDays(args.backDays)
if args.importDate:
  importDate = args.importDate

print('Input file: ', inputFileName, ' input date: ', importDate, ', backDays = ', backDays, 'useDB = ', useDB)

inmates = getInmateList(inputFileName)
ok = checkIntegrity(inmates)
if ok:
  if doArrests:
    previousInmateMap = getPreviousInmates(backDays, importDate)
    createRecentArrestsFile(inmates, backDays, importDate)
  if useDB:
    loadToDatabase(inmates)
