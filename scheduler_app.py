from apscheduler.schedulers.background import BlockingScheduler, BackgroundScheduler
from apscheduler.triggers.combining import OrTrigger 
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session

from sql import getEngine, portfolioSnapshot
from utils import customLogger

import argparse
parser = argparse.ArgumentParser()
parser.add_argument('--prod', action='store_true')
args = parser.parse_args()

logger = customLogger(__file__)

job_defaults = {
    'coalesce': True,
    'max_instances': 3
}
scheduler = BlockingScheduler(timezone='Asia/Singapore')
# scheduler = BackgroundScheduler(timezone='Asia/Singapore')

# GMT+8 > 930am - 5pm (9-5pm)
# GMT+1 > 3pm - 1230am (8-430pm)
# GMT-5 > 1030pm - 5am (930-4pm)
# trigger = OrTrigger([
#     CronTrigger(minute='2', day_of_week='mon-fri', hour='9-18', timezone='Asia/Singapore'),
#     CronTrigger(minute='32', day_of_week='mon-fri', hour='21', timezone='Asia/Singapore'),
#     CronTrigger(minute='2', day_of_week='mon-fri', hour='22-23', timezone='Asia/Singapore'),
#     CronTrigger(minute='2', day_of_week='tue-sat', hour='0-5', timezone='Asia/Singapore')
# ])
if args.prod:
    trigger = OrTrigger([
        CronTrigger(day_of_week='mon-fri', hour='9-23'),
        CronTrigger(day_of_week='tue-sat', hour='0-5')
    ])
    engine = getEngine('prod')
else:
    trigger = CronTrigger(minute='*/1')
    engine = getEngine('test')

def portfolioSnapshotJob(session):
    logger.info(f'Job started: {portfolioSnapshot.__name__}')
    try:
        portfolioSnapshot(session)
        logger.info(f'Job completed: {portfolioSnapshot.__name__}')
    except Exception as e:
        logger.info(f'Job failed, rolling back: {e}')
        session.rollback()

with Session(engine) as session:
    scheduler.add_job(portfolioSnapshotJob, trigger=trigger, name='portfolioSnapshot', args=[session])

    logger.info('=== Starting Scheduler ===')
    scheduler.start()

# python scheduler_app.py >> scheduler_app.log 2>&1
# nohup python scheduler_app.py >> scheduler_app.log 2>&1 &