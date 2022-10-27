from database import Base, Column, Text, BLOB, Integer


class TokenUserRecordsDAO(Base):
    __tablename__ = "ms_graph_token"
    id = Column(Integer, primary_key=True, autoincrement=True, unique=True, nullable=False)
    user = Column(Text, unique=True, nullable=False)
    token = Column(BLOB, unique=True, nullable=False)

    def __init__(self, user=None, token=None):
        self.user = user
        self.token = token

    def __repr__(self):
        return "<TokenUserRecordDAO %r>" % self.__dict__
