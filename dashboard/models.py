from sqlalchemy.orm import  DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String,Date,func, DateTime, Table, ForeignKey, Column
from datetime import date,datetime
from sqlalchemy.dialects.postgresql import UUID
import uuid


class Base(DeclarativeBase):
    pass

user_event_association = Table(
    "participants",
    Base.metadata,
    Column(
        "user_id",
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True
    ),
    Column(
        "event_id",
        UUID(as_uuid=True),
        ForeignKey("events.id", ondelete="CASCADE"),
        primary_key=True
    ),
)
class Mixins:
    __abstract__ = True

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

class User(Mixins,Base):
    __tablename__ = "users"

    username : Mapped[str] = mapped_column(String(30),unique=True,nullable=False)
    fullname : Mapped[str] = mapped_column(String(30),nullable=False)
    email : Mapped[str] = mapped_column(String(255),unique=True,nullable=False)
    password : Mapped[str] = mapped_column(String(255),nullable=False)
    role : Mapped[str] = mapped_column(String(20),nullable=False)

    events: Mapped[list["Event"]] = relationship(secondary=user_event_association,back_populates="users",lazy="selectin")

    def __repr__(self):
        return f"<User id={self.id} username={self.username} email={self.email}>"
    
class Event(Base,Mixins):
    __tablename__ = "events"

    title : Mapped[str] = mapped_column(String(255),nullable=False)
    description : Mapped[str] = mapped_column(String(255))
    startdate : Mapped[date] = mapped_column(Date,nullable=False)
    enddate : Mapped[date] = mapped_column(Date,nullable=False)
    status : Mapped[str] = mapped_column(String(20),nullable=False)
    progress_note : Mapped[str] = mapped_column(String(255))

    users : Mapped[list["User"]] = relationship(secondary=user_event_association,back_populates="events",lazy="selectin")
    def __repr__(self):
        return f"<Event id={self.id} title={self.title}>"
