from dataclasses import dataclass


@dataclass
class TokenUserRecordsDTO:
    id: int
    user: str
    token: bytes

    def __repr__(self):
        return "<TokenUserRecordDTO %r>" % self.__dict__
