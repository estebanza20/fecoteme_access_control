import MySQLdb
from datetime import datetime, date
from dateutil.relativedelta import relativedelta


class Database:
    def __init__(self, server, user, passwd, db, port=None):
        self.server = server
        self.user = user
        self.passwd = passwd
        self.db = db
        self.port = port
        self.conn = None

    def connect(self):
        if self.port == None:
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
            cursor = self.conn.cursor()
            cursor.execute(sql)
            self.conn.commit()
        except (AttributeError, MySQLdb.OperationalError):
            self.conn.rollback()
            self.connect()
            cursor = self.conn.cursor()
            cursor.execute(sql)
            self.conn.commit()
        return cursor

    
#FIXME: Implement movQueue pipe with multiprocessing
class AccessControl:
    def __init__(self, accessDB, movementsDB):
        self.accessDB = accessDB
        self.movementsDB = movementsDB
        self.usersInside = set()

    def isUserInside(self, affiliate_id):
        return affiliate_id in self.usersInside

    #FIXME: Register user entry in movementsDB
    def userEnters(self, affiliate_id):
        self.usersInside.add(affiliate_id)

    #FIXME: Register user exit in movementsDB
    def userExits(self, affiliate_id):
        self.usersInside.discard(affiliate_id)

    def is_valid_access(self, affiliate_id, direc):
        is_valid = False

        sql = "select firstName,lastName,subscriptionDate \
        from afiliado where (id='%d')" % (int(affiliate_id))
        cursor = self.accessDB.query(sql)
        
        data = cursor.fetchone()
        
        userInside = self.isUserInside(affiliate_id);
        
        if ((not userInside and direc == "in") or (userInside and direc == "out")):
            print(60 * "-")
            print("Affiliate ID:", affiliate_id)

            if data is not None:
                name = " ".join(data[0:2])
                subscription_date = data[2]

                print("Name:", name)
        
                if subscription_date is not None:
                    last_valid_access_date = subscription_date + relativedelta(days=+30)
                    today = date.today()
                    is_valid = (today <= last_valid_access_date)

                    print("Subscription Date:",subscription_date)
                    print("Last Valid Access Date:",last_valid_access_date)
                    print("Days from Last Subscription Update:",(today-subscription_date).days)

                    if is_valid == False:
                        print("")
                        print("Invalid access: Affiliate subscription has caducated.")
                        print("Less or equal than 30 days from last subscription update")
                        print("is required for access")
                else:
                    print("")
                    print("Invalid access: Affiliate has never been subscribed")
            else:
                print("")
                print("Invalid access: Affiliate does not exist")

            print(60 * "-")
        else:
            print("User in invalid position")
            
        return is_valid
