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
  worksheet.freeze_panes(1, 0)
  i = 0
  worksheet.set_column(i, i, 5, baseFormat) #cal
  i = i + 1
  worksheet.set_column(i, i, 22, baseFormat) #name
  i = i + 1
  worksheet.set_column(i, i, 6, baseFormat) #ADMN
  i = i + 1
  worksheet.set_column(i, i, 6, baseFormat) #atty-this
  i = i + 1
  worksheet.set_column(i, i, 6, baseFormat) #atty-other
  i = i + 1
  worksheet.set_column(i, i, 20, baseFormat) #notes
  i = i + 1
  worksheet.set_column(i, i, 7, baseFormat) #PDO
  i = i + 1
  worksheet.set_column(i, i, 7, baseFormat) #Ct-date
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

  a_misd = workbook.add_format({'font_color': 'lightslategray', 'bold': True})
  a_ad1a = workbook.add_format({'font_color': '#244061', 'bold': True})
  a_ad2b = workbook.add_format({'font_color': '#02b050', 'bold': True})
  a_ad3b = workbook.add_format({'font_color': '#974805', 'bold': True})
  a_9999 = workbook.add_format({'font_color': '#974805', 'bold': True})
  a_x = workbook.add_format({'bg_color': '#DCDCDC'})
  c_yes = workbook.add_format({'font_color': '#02b050'})
  c_na = workbook.add_format({'bg_color': '#DCDCDC'})
  d_none = workbook.add_format({'bg_color': '#c6efce'})
  g_yes = workbook.add_format({'bg_color': '#ffeb9c'})
  g_noneed = workbook.add_format({'bg_color': '#d8d8d8'})
  g_waive = workbook.add_format({'bg_color': '#d8d8d8'})
  m_sentenced = workbook.add_format({'bg_color': '#c6efce'})
  m_nobond = workbook.add_format({'bg_color': '#ffc7ce'})
  m_support = workbook.add_format({'bg_color': '#cef0cc'})

  i_na = workbook.add_format({'bg_color': '#DCDCDC'})
  i_xa = workbook.add_format({'bg_color': '#ffeb9c'})
  l_no = workbook.add_format({'bg_color': '#DCDCDC'})
  l_yes = workbook.add_format({'bg_color': '#ffeb9c'})
  c_no = workbook.add_format({'bg_color': '#DCDCDC'})

  worksheet.conditional_format('A2:A1000', {'type': 'cell', 'criteria': '==', 'value': '"MISD"', 'format': a_misd})
  worksheet.conditional_format('A2:A1000', {'type': 'cell', 'criteria': '==', 'value': '"AD1A"', 'format': a_ad1a})
  worksheet.conditional_format('A2:A1000', {'type': 'cell', 'criteria': '==', 'value': '"AD2B"', 'format': a_ad2b})
  worksheet.conditional_format('A2:A1000', {'type': 'cell', 'criteria': '==', 'value': '"AD3B"', 'format': a_ad3b})
  worksheet.conditional_format('A2:A1000', {'type': 'cell', 'criteria': '==', 'value': '"9999"', 'format': a_9999})
  worksheet.conditional_format('A2:A1000', {'type': 'cell', 'criteria': '==', 'value': '"x"', 'format': a_x})
  worksheet.conditional_format('C2:C1000', {'type': 'text', 'criteria': 'containing', 'value': 'yes', 'format': c_yes})
  worksheet.conditional_format('C2:C1000', {'type': 'text', 'criteria': 'containing', 'value': 'n/a', 'format': c_na})
  worksheet.conditional_format('D2:D1000', {'type': 'text', 'criteria': 'containing', 'value': 'none', 'format': d_none})
  worksheet.conditional_format('G2:G1000', {'type': 'text', 'criteria': 'containing', 'value': 'yes', 'format': g_yes})
  worksheet.conditional_format('G2:G1000', {'type': 'text', 'criteria': 'containing', 'value': 'no need', 'format': g_noneed})
  worksheet.conditional_format('G2:G1000', {'type': 'text', 'criteria': 'containing', 'value': 'waive', 'format': g_waive})
  worksheet.conditional_format('M2:M1000', {'type': 'text', 'criteria': 'containing', 'value': 'sentenced', 'format': m_sentenced})
  worksheet.conditional_format('M2:M1000', {'type': 'text', 'criteria': 'containing', 'value': 'no bond', 'format': m_nobond})
  worksheet.conditional_format('M2:M1000', {'type': 'text', 'criteria': 'containing', 'value': 'support', 'format': m_support})
  worksheet.conditional_format('I2:I1000', {'type': 'text', 'criteria': 'containing', 'value': 'n/a', 'format': i_na})
  worksheet.conditional_format('I2:I1000', {'type': 'text', 'criteria': 'containing', 'value': 'xa', 'format': i_xa})
  worksheet.conditional_format('L2:L1000', {'type': 'text', 'criteria': 'containing', 'value': 'no', 'format': l_no})
  worksheet.conditional_format('L2:L1000', {'type': 'text', 'criteria': 'containing', 'value': 'yes', 'format': l_yes})
  worksheet.conditional_format('C2:C1000', {'type': 'text', 'criteria': 'containing', 'value': 'no', 'format': c_no})
  
def createRecentArrestsFile(inmates, backdays, importDate):
  global cutoffDate
  today = datetime.date.today()
  days = datetime.timedelta(backdays)
  cutoffDate = today - days
  latest = list(filter(checkDate, inmates))
  print('Total arrests over past ', backdays, ' days: ', len(latest))
  pdo = ['', 'yes', 'no need', 'who knows', 'yes', 'no need']
  i = 0
  rows = []
  for itm in latest:
    inmate = {}
    if (i > 4):
      i = 0
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

    i = i+1

    for c in itm['charges']:
      inmate['charges'] += chargeLine(c)
    rows.append(inmate)
  prefix = 'latest_arrests-' + str(backDays) + 'day-'
  workbook = xlsxwriter.Workbook(prefix + today.strftime('%Y-%m-%d') + '.xlsx')
  worksheet = workbook.add_worksheet()
  header = '&LPage &P of &N' + '&CFIRST APP - ' + today.strftime('%Y-%m-%d')

  worksheet.set_landscape()
  worksheet.set_header(header)
  worksheet.print_area('A1:L10000')


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
  return parser

def getInmateList(inputFileName):
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
inputFileName = args.fileName
useDB = False if args.database == 0 else True
backDays = computeBackDays(args.backDays)
if args.importDate:
  importDate = args.importDate
useDB = False
print('Input file: ', inputFileName, ' input date: ', importDate, ', backDays = ', backDays, 'useDB = ', useDB)

inmates = getInmateList(inputFileName)
createRecentArrestsFile(inmates, backDays, importDate)
if useDB:
  loadToDatabase(inmates)



