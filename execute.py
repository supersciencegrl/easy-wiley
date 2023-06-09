from datetime import date

from getxml import update_journals, github_push

def update_xml(cdate):
    update_journals(cdate)
    #github_push(cdate)

cdate = date.today().strftime('%Y-%m-%d')
update_xml(cdate)