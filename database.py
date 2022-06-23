from sqlalchemy import create_engine, Column, Text, BLOB, Integer
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from helpers import getdatatbaseinfo

dbinfo = getdatatbaseinfo()

engine = create_engine(
    f"mysql+pymysql://{dbinfo['user']}:{dbinfo['passwd']}@{dbinfo['host']}:{dbinfo['port']}/{dbinfo['dbname']}",
    pool_pre_ping=True
)
db_session = scoped_session(
    sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine
    )
)

Base = declarative_base()
Base.query = db_session.query_property()
