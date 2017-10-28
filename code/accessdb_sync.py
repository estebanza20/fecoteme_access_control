#!/usr/bin/python3
# -*- coding: utf-8 -*-

from access_control import Database


def main():
    # Setup Databases
    credentials = []
    with open("/home/pi/fecoteme_access_control/dbcredentials.txt") as f:
        for line in f:
            credentials.append(line.split())

    localDB = Database(*credentials[0])
    localDB.connect()
    serverDB = Database(*credentials[1])
    serverDB.connect()

    # Check affiliates max_valid_date and quick-pass fields
    sql = "SELECT a.id,b.valido_hasta,c.entra_gratis FROM afiliado a \
    LEFT JOIN pagos b ON a.id = b.carne  \
    AND b.valido_hasta = (SELECT MAX(valido_hasta) \
    from pagos WHERE carne=a.id AND anulado=0) \
    LEFT JOIN tipo_afiliado c ON a.tipo = c.tipo"
    cursor = serverDB.query(sql)

    # Update local database
    for row in cursor:
        sql = "REPLACE INTO access values ('%d', '%s', '%d')" % row
        localDB.query(sql)

if __name__ == '__main__':
    main()
