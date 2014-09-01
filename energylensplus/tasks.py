"""
Tasks are used for emboding the events i.e. Tasks === Events.
They are:
1. DataReceived
2. EdgeDetected
3. OFFDetected
4. WastageDetected
"""

from __future__ import absolute_import

from msgrelayserver.celery import app


@app.task
def add(x, y):
    return x + y


@app.task
def mul(x, y):
    return x * y


@app.task
def xsum(numbers):
    return sum(numbers)
