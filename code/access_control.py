import MySQLdb
from datetime import datetime


class Database:
    def __init__(self, server, user, passwd, db, port=None):
        self.server = server
        self.user = user
        self.passwd = passwd
        self.db = db
        self.port = port
        self.conn = None

    def connect(self):
        if self.port is None:
            self.conn = MySQLdb.connect(host=self.server,
                                        user=self.user,
                                        passwd=self.passwd,
                                        db=self.db)
        else:
            self.conn = MySQLdb.connect(host=self.server,
                                        user=self.user,
                                        passwd=self.passwd,
                                        db=self.db,
                                        port=self.port)

    def query(self, sql):
        try:
            # self.conn.ping(True)
            cursor = self.conn.cursor()
            cursor.execute(sql)
            self.conn.commit()
        except (AttributeError, MySQLdb.OperationalError):
            # self.conn.rollback()
            self.connect()
            cursor = self.conn.cursor()
            cursor.execute(sql)
            self.conn.commit()
        return cursor


class AccessControl:
    def __init__(self, accessDB, movWriteQueue):
        self.accessDB = accessDB
        self.movWriteQueue = movWriteQueue
        self.usersInside = set()

    def isUserInside(self, affiliate_id):
        return affiliate_id in self.usersInside

    def userEnters(self, affiliate_id):
        self.usersInside.add(affiliate_id)
        movData = (affiliate_id, 0, datetime.now())
        self.movWriteQueue.put(movData)

    def userExits(self, affiliate_id):
        self.usersInside.discard(affiliate_id)
        movData = (affiliate_id, 1, datetime.now())
        self.movWriteQueue.put(movData)

    def isValidAccess(self, affiliate_id, direc):
        is_valid = False

        userInside = self.isUserInside(affiliate_id)

        if ((not userInside and direc == "in") or (userInside and direc == "out")):
            sql = "SELECT quickpass,max_valid_time FROM access \
            where id='%d'" % (int(affiliate_id))

            cursor = self.accessDB.query(sql)
            data = cursor.fetchone()

            print(60 * "-")
            print("Affiliate ID:", affiliate_id)

            if data is not None:
                quickpass = data[0]

                if quickpass == 1:
                    is_valid = True
                    print("Affiliate has quick-pass access")
                else:
                    max_valid_time = data[1]
                    if max_valid_time is not None:
                        now_time = datetime.now()

                        print("valid time:", max_valid_time)
                        print("now time:", now_time)

                        is_valid = now_time <= max_valid_time 
                        if not is_valid:
                            print("Invalid access: Affiliate subscription has caducated.")
                            print("Less or equal than 30 days from last subscription update")
                            print("is required for access")

                if is_valid:
                    print("Valid access")
            else:
                print("")
                print("Invalid access: Affiliate has no registered max valid ")
                print("datetime and has no quick-pass access")

            print(60 * "-")
        else:
            print("User at invalid position")

        return is_valid
