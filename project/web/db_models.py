from peewee import *
from config import DATABASENAME, USER, PASSWORD, PORT, HOST

psql_db = PostgresqlDatabase(DATABASENAME, user=USER, password=PASSWORD, port=PORT, host=HOST)

class Query_results(Model):
    class Meta:
        database = psql_db

    text1 = TextField()
    text2 = TextField()
    cos_dist = CharField(30)

    def init_db():
        psql_db.create_tables(Query_results, safe=True)

    def drop_db():
        psql_db.drop_tables(Query_results, safe=True)

if __name__ == "__main__":
    Query_results.drop_db()
    Query_results.init_db()
