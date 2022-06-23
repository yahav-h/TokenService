from database import Base, Column, Text, BLOB, Integer


class TokenUserRecords(Base):
    __tablename__ = "token_user_records"
    id = Column(Integer, primary_key=True, autoincrement=True, unique=True, nullable=False)
    user = Column(Text, unique=True, nullable=False)
    token = Column(BLOB, unique=True, nullable=False)

    def __init__(self, user=None, token=None):
        self.user = user
        self.token = token

    def __repr__(self):
        return "<TokenUserRecord %r>" % self.__dict__
