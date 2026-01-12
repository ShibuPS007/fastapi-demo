
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine


db_url = "mysql+mysqlconnector://root:Idly2004@mysql:3306/fast_api"


engine=create_engine(db_url)
SessionLocal=sessionmaker(autocommit=False,autoflush=False,bind=engine)