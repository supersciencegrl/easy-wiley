from apscheduler.schedulers.blocking import BlockingScheduler

from getxml import updaterss

sched = BlockingScheduler()

@sched.scheduled_job('cron', hour = 4)
def scheduled_job():
    updaterss()

sched.start()
