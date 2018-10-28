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

    def close_connection(self):
        self.conn.close()


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
        # print("Enter isValidAccess")
        # print("affiliate_id:", affiliate_id)
        is_valid = False

        userInside = self.isUserInside(affiliate_id)
        # print("userInside:", userInside)

        # Check if user is at valid position
        if ((not userInside and direc == "in") or (userInside and direc == "out")):
            # print("User at valid position")
            # If user is about to get in, check database for valid access
            if direc == "in":
                # print("In Direction")
                try:
                    affiliate_int = int(affiliate_id)
                except ValueError:
                    return False

                sql = "SELECT quickpass,max_valid_time FROM access \
                where id='%d'" % (affiliate_int)

                cursor = self.accessDB.query(sql)
                data = cursor.fetchone()
                # print("data:", data)

                if data is not None:
                    # print("Data not None")
                    quickpass = data[0]

                    if quickpass == 1:
                        # print("Has QuickPass access")
                        is_valid = True
                    else:
                        # print("No QuickPass access")
                        max_valid_time = data[1]
                        # print("Max valid Time:", max_valid_time)
                        if max_valid_time is not None:
                            now_time = datetime.now()
                            # print("Now Time:", now_time)
                            is_valid = now_time <= max_valid_time
                            # print("is valid:", is_valid)

            #If user is about to get out, allow access 
            elif direc == "out":
                is_valid = True

        return is_valid
