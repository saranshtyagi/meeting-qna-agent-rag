from sqlalchemy.orm import Session

from app.db.models import Meeting


class MeetingRepository:

    def __init__(self, db: Session):
        self.db = db

    def create(self, meeting: Meeting) -> Meeting:
        self.db.add(meeting)
        self.db.commit()
        self.db.refresh(meeting)
        return meeting

    def get(self, meeting_id: str):
        return (
            self.db.query(Meeting)
            .filter(Meeting.id == meeting_id)
            .first()
        )

    def get_all(self):
        return (
            self.db.query(Meeting)
            .order_by(Meeting.created_at.desc())
            .all()
        )

    def delete(self, meeting_id: str):
        meeting = self.get(meeting_id)

        if meeting:
            self.db.delete(meeting)
            self.db.commit()

        return meeting