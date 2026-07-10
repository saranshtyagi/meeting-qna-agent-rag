from typing import Optional

from sqlalchemy.orm import Session

from app.db.models import Meeting


class MeetingRepository:

    def __init__(self, db: Session):
        self.db = db

    # ======================================================
    # CREATE
    # ======================================================

    def create(self, meeting: Meeting):

        self.db.add(meeting)

        self.db.commit()

        self.db.refresh(meeting)

        return meeting

    # ======================================================
    # READ
    # ======================================================

    def get_all(self):

        return (
            self.db.query(Meeting)
            .order_by(Meeting.created_at.desc())
            .all()
        )

    def get_by_id(
        self,
        meeting_id: str,
    ) -> Optional[Meeting]:

        return (
            self.db.query(Meeting)
            .filter(Meeting.id == meeting_id)
            .first()
        )

    # ======================================================
    # DELETE
    # ======================================================

    def delete(
        self,
        meeting: Meeting,
    ):

        self.db.delete(meeting)

        self.db.commit()