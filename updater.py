from getxml import updatejournals, ghpush

def updatexml(cdate):
    #commitmsg = cdate.strftime('%Y-%b-%d')
    updatejournals(cdate)
    #ghpush(cdate)
