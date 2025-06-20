from celery import shared_task

import logging, time

# @shared_task(bind=True, queue="high-priority")
@shared_task(bind=True)
def add_task(self, a, b):

    self.update_state(state="ADD_PROGRESS", meta={'step' : 'add_task'})

    time.sleep(15)

    logging.info(f"{a=}, {b=}")
    logging.info(f"Task Done : {a} + {b} = {a + b}")

    return a + b


# @shared_task(bind=True, queue="high-priority")
@shared_task(bind=True)
def multi_task(self,a, b):

    self.update_state(state="MULTI_PROGRESS", meta={'step' : 'multi_task'})

    time.sleep(8)

    logging.info(f"{a=}, {b=}")
    logging.info(f"Task Done : {a} * {b} = {a * b}")

    return a * b

@shared_task(bind=True)
def sum_multiply_task(self, sum, a, b):

    self.update_state(state="SUM_MULTIPLY_PROGRESS", meta={'step' : 'sum_multiply_task'})

    time.sleep(8)

    logging.info(f"{a=}, {b=}, {sum=}")
    logging.info(f"Task Done : {a} * {sum} = {a * sum}")
    logging.info(f"Task Done : {b} * {sum} = {b * sum}")

    return a * sum, b * sum
