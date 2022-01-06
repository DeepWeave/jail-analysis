from bs4 import BeautifulSoup
import time
import datetime
import sys
import os
import psycopg2
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
  inmate['height'] = itm['height'].replace("'","''") if itm['height'] else None
  inmate['weight'] = itm['weight']
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
  inmate['total_bond_amount'] = int(float(val) * 100)
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
  for m in inmates:
    sql = 'insert into jaildata.daily_inmates ' + \
    '(import_date, name, age, gender, race, height, weight, arrested, court_date, released, primary_charge, holding_facility, total_bond) ' +\
    "VALUES ("
    sql +=  "'" + m['import_date'] + "', "
    sql +=  "'" + m['name'] + "', "
    sql += str(m['age']) + ','
    sql += "'" + m['gender'] + "', '" + m['race'] + "', "
    sql += ("'" + m['height'] + "', " ) if m['height'] else 'null, '
    sql += ("'" + m['weight'] + "', ") if m['weight'] else 'null, '
    sql += ("'" + m['arrested'] + "'") if m['arrested'] else 'null'
    sql += ','
    sql += ("'" + m['court_date'] + "'") if m['court_date'] else 'null'
    sql += ','
    sql += ("'" + m['released'] + "'") if m['released'] else 'null'
    sql += ','
    sql += " '" + m['primary_charge'] + "', " 
    sql += ("'" + m['holding_facility'] + "',") if m['holding_facility'] else 'null, '
    sql +=  str(m['total_bond_amount']) + ') returning id'
    cur.execute(sql)
    id = cur.fetchone()[0]

  conn.commit()
  cur.close()
  conn.close()


# Main program

load_dotenv()
import os
token = os.environ.get("api-token")

importDate = datetime.datetime.now().strftime('%Y-%m-%d')
argc = len(sys.argv)

if (argc < 2 or argc > 3):
  print('Usage: get-inmates inputfilename [YYYY-MM-DD]')
  sys.exit()

inputFileName = sys.argv[1]
if argc == 3:
  importDate = sys.argv[2]

print('Input file: ', inputFileName, ' input date: ', importDate)

file = open(inputFileName)
pageText = file.read()
file.close()
#pageText.replace('\n', '')
soup = BeautifulSoup(pageText, 'html.parser')

nms = soup.find_all("div", "p2c-card-title")
cards = soup.find_all("md-card", "p2c-card")
print('Total cards: ', len(cards))
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

print('Total cards: ', len(cards))
loadToDatabase(inmates)



