from sqlalchemy import Column, String, Text, DateTime
from datetime import datetime

from app.db.database import Base


class Meeting(Base):

    __tablename__ = "meetings"

    id = Column(String, primary_key=True)

    title = Column(Text)

    transcript = Column(Text)

    summary = Column(Text)

    action_items = Column(Text)

    key_decisions = Column(Text)

    open_questions = Column(Text)

    youtube_url = Column(Text, nullable=True)

    filename = Column(Text, nullable=True)

    duration = Column(String, nullable=True)

    status = Column(String, default="completed")

    created_at = Column(DateTime, default=datetime.utcnow)

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )