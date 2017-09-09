#!/usr/bin/python3
# -*- coding: utf-8 -*-

from datetime import datetime, date
from dateutil.relativedelta import relativedelta

DATE = date(2017, 1, 31)
print(DATE)

ONE_MONTH_AFTER = DATE + relativedelta(days=+30)
print(ONE_MONTH_AFTER)

TODAY = date.today()
print(TODAY)

print(TODAY <= ONE_MONTH_AFTER)
