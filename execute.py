#import os
from datetime import date

from updater import updatexml

cdate = date.today().strftime('%Y-%m-%d')

#try:
#    os.chdir('C:\\Users\\Nessa\\Documents\\GitHub\\easy-wiley')
#except FileNotFoundError:
#    os.chdir('C:\\Users\\CARSOL02\\Documents\\GitHub\\easy-wiley\\easy-wiley')

updatexml(cdate)
