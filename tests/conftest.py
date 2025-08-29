import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))  # Add project root to Python path

from models.cafe_managment_models import Base
from models.dbhandler import DBHandler


@pytest.fixture(scope='function')
def in_memory_db():
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)

    db_handler = DBHandler(engine=engine, session_factory=Session)
    yield db_handler

    Base.metadata.drop_all(engine)