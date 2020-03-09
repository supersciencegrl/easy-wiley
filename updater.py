from datetime import date

from getxml import updatejournals, ghpush

cdate = date.today()
commitmsg = cdate.strftime('%Y-%b-%d')

def getxml():
    updatejournals()
    cdate = date.today()
    commitmsg = cdate.strftime('%Y-%b-%d')
    ghpush(commitmsg)
