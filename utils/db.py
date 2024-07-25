from flask import current_app as app, g
import pyodbc
import pandas as pd

import os

class MSSQLConnection:
    def __init__(self):
        self.connection = None
        

    def init_app(self, app):
        app.teardown_appcontext(self.close_connection)

    def connect(self):
        if self.connection is None:
            conn_str = (
                f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                f"SERVER=tcp:{app.config['MSSQL_SERVER']},1433;"
                f"DATABASE={app.config['MSSQL_DATABASE']};"
                f"UID={os.environ.get('CLIENTID')};"
                f"PWD={os.environ.get('CLIENT_SECRET')};"
                f"Authentication=ActiveDirectoryServicePrincipal"
            )
            self.connection = pyodbc.connect(conn_str)
            
        return self.connection

    def close_connection(self, exception):
        conn = getattr(g, '_database', None)
        if conn is not None:
            conn.close()

    def get_db(self):
        if 'db_conn' not in g:
            g.db_conn = self.connect()
        return g.db_conn

    def exec(self, query, *args):
        try:
            result = True
            conn = self.get_db()
            cursor = conn.cursor()
            cursor.execute(query, args)
            conn.commit()
        except Exception as e:
            print(f"Failed while sql_exec: {str(e)}")
            result = False
        finally:
            return result

    def select(self, query):
        """to run a select query """
        try:
            result = []
            conn = self.get_db()
            cursor = conn.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()
            columns = [column[0] for column in cursor.description]
            for row in rows:
                result.append(dict(zip(columns, row)))
        except Exception as e:
            print(f"Failed while sql_exec: {str(e)}")
            result = False
        finally:
            return result

    def select_df(self, query):
        """to run a select query """
        try:
            
            conn = self.get_db()
            cursor = conn.cursor()
            result = pd.read_sql(query, conn)
            # print(result)
            
        except Exception as e:
            print(f"Failed while sql_exec: {str(e)}")
            result = pd.DataFrame({'A' : []})
        finally:
            return result