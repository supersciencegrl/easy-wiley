from datetime import date

from getxml import update_journals

cdate = date.today().strftime('%Y-%m-%d')
update_journals(cdate)