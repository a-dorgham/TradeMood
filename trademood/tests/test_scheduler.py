import time
from apscheduler.schedulers.background import BackgroundScheduler
scheduler = BackgroundScheduler()

def test_job(): print("Test job ran")
scheduler.add_job(test_job, 'interval', seconds=10)
scheduler.start()
try:
    while True: time.sleep(60)
except KeyboardInterrupt:
    scheduler.shutdown()