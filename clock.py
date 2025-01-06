## DEPRECATED ##

from apscheduler.schedulers.blocking import BlockingScheduler

from getxml import updaterss

sched = BlockingScheduler()

@sched.scheduled_job('cron', hour = 4)
def scheduled_job():
    updaterss()

sched.start()

# from apscheduler.schedulers.background import BackgroundScheduler

# from updater import getxml

# jobid = 'Wiley-update'

# def canceljob(jobid):
#     sched.remove_job(jobid)

# sched = BackgroundScheduler()
# sched.start()

# job = sched.add_job(getxml, 'interval', minutes = 86400, id = jobid)