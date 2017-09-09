#!/usr/bin/python3

import MySQLdb

db = MySQLdb.connect("localhost","root","","fecoteme")

cursor = db.cursor()

id = int(input("Afiliado id: "))

sql = "select firstName,lastname,rank \
from afiliado where (id='%d')" % (id)

try:
    cursor.execute(sql)
    db.commit()
except:
    db.rollback()
    

data = cursor.fetchone()

if data is None:
    print("No entry found")
else:
    print(data)
