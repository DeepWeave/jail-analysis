from bs4 import BeautifulSoup
import time
import sys

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

# Main program

# The -s is to suppress annoying error messages from xlrd
argc = len(sys.argv)
print(argc)
if (argc < 2 or argc > 2):
  print('Usage: get-inmates inputfilename')
  sys.exit()

inputFileName = sys.argv[1]
print('Input file: ', inputFileName)

file = open(inputFileName)
pageText = file.read()
file.close()
pageText.replace('\n', '')
soup = BeautifulSoup(pageText, 'html.parser')

nms = soup.find_all("div", "p2c-card-title")
cards = soup.find_all("md-card", "p2c-card")
print('Total cards: ', len(cards))

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
  print(itm)
  # break


