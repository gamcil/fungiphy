import os

from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, configure_mappers, scoped_session


DB_PATH = os.getenv("FUNGPHY_DB") or "fungphy.db"
engine = create_engine(f"sqlite:///{DB_PATH}")
session = scoped_session(sessionmaker(bind=engine, autocommit=False, autoflush=False))

naming_convention={
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(column_0_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}
meta = MetaData(naming_convention=naming_convention)
Base = declarative_base(metadata=meta)
Base.query = session.query_property()


def init_db():
    import fungphy.models
    configure_mappers()
    Base.metadata.create_all(engine)
