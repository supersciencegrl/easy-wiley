from datetime import date

from getxml import updaterss, ghpush

cdate = date.today()
commitmsg = cdate.strftime('%Y-%b-%d')

def getxml():
    updaterss()
    cdate = date.today()
    commitmsg = cdate.strftime('%Y-%b-%d')
    ghpush(commitmsg)
