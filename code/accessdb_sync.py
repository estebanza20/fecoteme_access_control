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
    sql = "SELECT a.id, \
	IFNULL((SELECT	\
		IF (\
			y.entra_gratis=1 or c.entra_gratis=1,\
			'2050-01-01 00:00:00',			\
			MAX(x.valido_hasta)\
			) valido_hasta\
		FROM afiliado z\
		left join pagos x on z.id = x.carne and anulado = 0\
		left join tipo_afiliado y on z.tipo = y.tipo\
		where z.id = d.jugador\
		),\
		IF (c.entra_gratis=1,'2050-01-01 00:00:00',IFNULL(MAX(b.valido_hasta),'2000-01-01 00:00:00'))) validez,\
        0 entra_gratis\
	FROM afiliado a   \
    left join pagos b on a.id = b.carne and anulado = 0\
    left join tipo_afiliado c on a.tipo = c.tipo\
    left join relacion_familiar d on encargado = a.id and d.relacion_activa = 1\
	where b.valido_hasta is not null OR c.entra_gratis = 1 OR d.jugador is not null\
group by a.id"

    cursor = serverDB.query(sql)

    sql = "INSERT INTO access (id, max_valid_time, quickpass)\
    VALUES ('%d', '%s', '%d')\
    ON DUPLICATE KEY UPDATE \
    id=VALUES(id),\
    max_valid_time=VALUES(max_valid_time),\
    quickpass=VALUES(quickpass)"

    # Update local database
    for row in cursor:
        localDB.query(sql % row)

    # Close database connections
    localDB.close_connection()
    serverDB.close_connection()

if __name__ == '__main__':
    main()
