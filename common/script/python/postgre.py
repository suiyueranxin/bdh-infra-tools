#!/usr/bin/env python
import psycopg2

class PGCTL(object):
    def __init__(self, **kwargs):
        try:
            self.conn = psycopg2.connect(**kwargs)
            self.cur = self.conn.cursor()
        except Exception as e:
            print "Create db connection failed with error: %s" %str(e)
            raise e

    def execSQL(self, strSQL, *args):
        try:
            self.cur.execute(strSQL, *args)
            self.conn.commit()
        except Exception as e:
            if self.conn:
                self.conn.rollback()
            print "Execution SQL :'%s' failed with error: %s" %(strSQL, str(e))
            raise e

    def execSQLNoCommit(self, strSQL, *args):
        try:
            self.cur.execute(strSQL, *args)
        except Exception as e:
            print "Execution SQL :'%s' failed with error: %s" %(strSQL, str(e))
            raise e
    
    def commit(self):
        try:
            self.conn.commit()
        except Exception as e:
            if self.conn:
                self.conn.rollback()
            print "Execution SQL :'%s' failed with error: %s" %( str(e))
            raise e

    def querySQL(self, strSQL, *args):
        try:
            self.cur.execute(strSQL, *args)
            rows = self.cur.fetchall()
            return rows
        except Exception as e:
            print "Execution SQL :'%s' failed with error: %s" %(strSQL, str(e))
            raise e

    def queryOne(self, strSQL, *args):
        try:
            self.cur.execute(strSQL, *args)
            row = self.cur.fetchone()
            return row
        except Exception as e:
            print "Execution SQL :'%s' failed with error: %s" %(strSQL, str(e))
            raise e


    def __del__(self):
        if self.cur:
            self.cur.close()
        if self.conn:
            self.conn.close()

if __name__ == "__main__":
    db = "postgres"
    host = "mo-6967799b2.mo.sap.corp"
    user = "postgres"
    password = ""
    port = 5432
    objDB = PGCTL(database=db,host=host,user=user,password=password,port=port)
    strSQL = "select * from public.cfg_backend_info"
    #strSQL = "select * from res_monsoon_volumes"
    print objDB.querySQL(strSQL)
