from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import (
    String,
    Date,
    DateTime,
    Table,
    ForeignKey,
    Column,
    Boolean,
    Integer,
    UniqueConstraint,
    func,
    PrimaryKeyConstraint,
    Time
)
from sqlalchemy.dialects.postgresql import UUID
from datetime import date, datetime, time
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
        primary_key=True,
    ),
    Column(
        "event_id",
        UUID(as_uuid=True),
        ForeignKey("events.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column("is_winner", Boolean, default=False),
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


class User(Mixins, Base):
    __tablename__ = "users"

    username: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    fullname: Mapped[str] = mapped_column(String(30), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)

    events: Mapped[list["Event"]] = relationship(
        secondary=user_event_association,
        back_populates="users",
        lazy="selectin",
    )

    group_membership: Mapped["GroupMembers"] = relationship(
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )

    column_values: Mapped[list["ColumnValues"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self):
        return f"<User id={self.id} username={self.username}>"


class Event(Mixins, Base):
    __tablename__ = "events"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(String(255))
    startdate: Mapped[date] = mapped_column(Date, nullable=False)
    enddate: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    progress_note: Mapped[str] = mapped_column(String(255))

    users: Mapped[list["User"]] = relationship(
        secondary=user_event_association,
        back_populates="events",
        lazy="selectin",
    )
    stages: Mapped[list["Stage"]] = relationship(
        "Stage",
        back_populates="event",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


    def __repr__(self):
        return f"<Event id={self.id} title={self.title}>"


class Stage(Mixins, Base):
    __tablename__ = "stages"

    event_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("events.id", ondelete="CASCADE"),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(String(30), nullable=False)
    round_order: Mapped[int] = mapped_column(Integer, nullable=False)

    event: Mapped["Event"] = relationship(
        "Event",
        back_populates="stages",
        lazy="selectin",
    )


    groups: Mapped[list["Group"]] = relationship(
        back_populates="stage",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    tiesheets: Mapped[list["Tiesheet"]] = relationship(
        back_populates="stage",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    columns: Mapped[list["StandingColumn"]] = relationship(
        back_populates="stage",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self):
        return f"<Stage id={self.id} name={self.name}>"


class Group(Mixins, Base):
    __tablename__ = "groups"

    stage_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("stages.id", ondelete="CASCADE"),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(String(50), nullable=False)

    stage: Mapped["Stage"] = relationship(back_populates="groups", lazy="selectin")

    members: Mapped[list["GroupMembers"]] = relationship(
        back_populates="group",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    tiesheets: Mapped[list["Tiesheet"]] = relationship(
        back_populates="group",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self):
        return f"<Group id={self.id} name={self.name}>"


class GroupMembers(Mixins, Base):
    __tablename__ = "groupmembers"

    __table_args__ = (
        UniqueConstraint("user_id", name="uq_groupmembers_user_id"),
    )

    group_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("groups.id", ondelete="CASCADE"),
        nullable=False,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    group: Mapped["Group"] = relationship(back_populates="members", lazy="selectin")
    user: Mapped["User"] = relationship(back_populates="group_membership", lazy="selectin")

    def __repr__(self):
        return f"<GroupMembers user_id={self.user_id} group_id={self.group_id}>"


class StandingColumn(Mixins, Base):
    __tablename__ = "standingcolumns"

    stage_id : Mapped[uuid.UUID] = mapped_column(
        ForeignKey("stages.id", ondelete="CASCADE"),
        nullable=False
    )
    column_field : Mapped[str] = mapped_column(String(255), nullable=False)

    stage: Mapped["Stage"] = relationship(back_populates="columns", lazy="selectin")

    values: Mapped[list["ColumnValues"]] = relationship(
        back_populates="column",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self):
        return f"<Standing Column id={self.id} filed={self.column_field}>"
    
class ColumnValues(Mixins,Base):
    __tablename__ = "columnvalues"


    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    column_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("standingcolumns.id", ondelete="CASCADE"),
        nullable=False,
    )

    value : Mapped[str] = mapped_column(String(60),nullable=False)
    
    __table_args__ = (
        PrimaryKeyConstraint(
            "user_id",
            "column_id",
            name="pk_columnvalues",
        ),
    )
    user: Mapped["User"] = relationship(back_populates="column_values", lazy="selectin")
    column: Mapped["StandingColumn"] = relationship(back_populates="values", lazy="selectin")

    def __repr__(self):
        return f"<Column Value value={self.value}>"


# Need to add state ie: completed, upcoming... 
class Tiesheet(Mixins, Base):
    __tablename__ = "tiesheets"

    group_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("groups.id", ondelete="CASCADE"),
        nullable=True,
    )

    stage_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("stages.id", ondelete="CASCADE"),
        nullable=False,
    )

    scheduled_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    scheduled_time: Mapped[time] = mapped_column(
        Time,
        nullable=False,
    )

    players: Mapped[list["TiesheetPlayer"]] = relationship(
        back_populates="tiesheet",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    group: Mapped["Group"] = relationship(back_populates="tiesheets", lazy="selectin")
    stage: Mapped["Stage"] = relationship(back_populates="tiesheets", lazy="selectin")

    def __repr__(self):
        return f"<Tiesheet id={self.id} scheduled_at={self.scheduled_at}>"


class TiesheetPlayer(Base):
    __tablename__ = "tiesheet_players"

    tiesheet_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tiesheets.id", ondelete="CASCADE"),
        primary_key=True,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )

    is_winner: Mapped[bool] = mapped_column(Boolean, default=False)

    tiesheet: Mapped["Tiesheet"] = relationship(back_populates="players", lazy="selectin")
    user: Mapped["User"] = relationship(lazy="selectin")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    def __repr__(self):
        return f"<TiesheetPlayer tiesheet_id={self.tiesheet_id} user_id={self.user_id} winner={self.is_winner}>"
