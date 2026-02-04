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

    # Association
    # Many to many relationship
    events: Mapped[list["Event"]] = relationship(
        secondary=user_event_association,
        back_populates="users",
    )

    group_membership: Mapped[list["GroupMembers"]] = relationship(
        back_populates="user",
        cascade="save-update,delete-orphan",
    )


    column_values: Mapped[list["ColumnValues"]] = relationship(
        back_populates="user",
        cascade="save-update, delete-orphan",
    )

    qualifiers: Mapped[list["Qualifier"]] = relationship(
        back_populates="user",
        cascade="save-update, delete-orphan"
    )

    userrole : Mapped[list["UserRole"]] = relationship(
        back_populates="user",
        cascade="save-update, delete-orphan"
    )

    tiesheetplayer : Mapped[list["TiesheetPlayer"]] = relationship(
        back_populates="user",
        cascade="save-update, delete-orphan"
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

    # Many to many relationship
    users: Mapped[list["User"]] = relationship(
        secondary=user_event_association,
        back_populates="events",
    )

    stages: Mapped[list["Stage"]] = relationship(
        back_populates="event",
        cascade="save-update, delete-orphan",
    )

    groups: Mapped[list["Group"]] = relationship(
        "Group",
        back_populates="event",
        cascade="save-update, delete-orphan",
    )

    qualifiers: Mapped[list["Qualifier"]] = relationship(
        back_populates="event",
        cascade="save-update, delete-orphan",
    )
    userrole : Mapped[list["UserRole"]] = relationship(
        back_populates="event",
        cascade="save-update,delete-orphan"
    )
    def __repr__(self):
        return f"<Event id={self.id} title={self.title}>"

class Role(Mixins, Base):
    __tablename__ = "roles"

    rolename: Mapped[str] = mapped_column(String(30), nullable=False)

    can_edit: Mapped[bool] = mapped_column(Boolean, default=False)
    can_create: Mapped[bool] = mapped_column(Boolean, default=False)
    can_delete: Mapped[bool] = mapped_column(Boolean, default=False)

    can_edit_users: Mapped[bool] = mapped_column(Boolean, default=False)
    can_create_users: Mapped[bool] = mapped_column(Boolean, default=False)
    can_delete_users: Mapped[bool] = mapped_column(Boolean, default=False)

    can_edit_roles: Mapped[bool] = mapped_column(Boolean, default=False)
    can_create_roles: Mapped[bool] = mapped_column(Boolean, default=False)
    can_delete_roles: Mapped[bool] = mapped_column(Boolean, default=False)

    can_edit_events: Mapped[bool] = mapped_column(Boolean, default=False)
    can_create_events: Mapped[bool] = mapped_column(Boolean, default=False)
    can_delete_events: Mapped[bool] = mapped_column(Boolean, default=False)

    can_manage_events: Mapped[bool] = mapped_column(Boolean, default=False)
    
    userrole: Mapped[list["UserRole"]] = relationship(
        back_populates="role",
        cascade="save-update, delete-orphan"
    )

    # One-to-one relationship
    roleaccesspage: Mapped["RoleAccessPage"] = relationship(
        "RoleAccessPage",
        back_populates="role",
        cascade="save-update, delete-orphan",
        uselist=False
    )

    def __repr__(self):
        return f"<Role id={self.id} rolename={self.rolename}>"
    
class UserRole(Mixins, Base):
    __tablename__ = "userrole"

    user_id : Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    event_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("events.id", ondelete="CASCADE"),
        nullable=False,
    )
    role_id : Mapped[uuid.UUID] = mapped_column(
        ForeignKey("roles.id", ondelete="CASCADE"),
        nullable=False
    )

    event: Mapped["Event"] = relationship(
        back_populates="userrole",
    )
    user : Mapped["User"] = relationship(
        back_populates="userrole"
    )
    role : Mapped["Role"] = relationship(
        back_populates="userrole"
    )

    def __repr__(self):
        return f"<UserRole id={self.id}>"

class RoleAccessPage(Mixins, Base):
    __tablename__ = "role_access_page"

    role_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("roles.id", ondelete="CASCADE"),
        nullable=False,
        unique=True 
    )
    home_page: Mapped[bool] = mapped_column(Boolean, default=False)
    event_page: Mapped[bool] = mapped_column(Boolean, default=False)
    user_page: Mapped[bool] = mapped_column(Boolean, default=False)
    profile_page: Mapped[bool] = mapped_column(Boolean, default=False)
    tiesheet_page: Mapped[bool] = mapped_column(Boolean, default=False)
    group_page: Mapped[bool] = mapped_column(Boolean, default=False)
    round_config_page: Mapped[bool] = mapped_column(Boolean, default=False)
    qualifier_page: Mapped[bool] = mapped_column(Boolean, default=False)
    participants_page: Mapped[bool] = mapped_column(Boolean, default=False)
    column_config_page: Mapped[bool] = mapped_column(Boolean, default=False)
    group_stage_standing_page: Mapped[bool] = mapped_column(Boolean, default=False)
    todays_game_page: Mapped[bool] = mapped_column(Boolean, default=False)

    # One-to-one relationship
    role: Mapped["Role"] = relationship(
        "Role",
        back_populates="roleaccesspage"
    )

class Stage(Mixins, Base):
    __tablename__ = "stages"

    event_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("events.id", ondelete="CASCADE"),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(String(30), nullable=False)
    round_order: Mapped[int] = mapped_column(Integer, nullable=False)

    event: Mapped["Event"] = relationship(
        back_populates="stages",
    )

    groups: Mapped[list["Group"]] = relationship(
        back_populates="stage",
        cascade="save-update, delete-orphan",
    )

    tiesheets: Mapped[list["Tiesheet"]] = relationship(
        back_populates="stage",
        cascade="save-update, delete-orphan",
    )

    columns: Mapped[list["StandingColumn"]] = relationship(
        back_populates="stage",
        cascade="save-update, delete-orphan",
    )

    qualifiers: Mapped[list["Qualifier"]] = relationship(
        back_populates="stage",
        cascade="save-update, delete-orphan",
    )
    def __repr__(self):
        return f"<Stage id={self.id} name={self.name}>"


class Group(Mixins, Base):
    __tablename__ = "groups"

    stage_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("stages.id", ondelete="CASCADE"),
        nullable=False,
    )

    event_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("events.id", ondelete="CASCADE"),
        nullable=False,
    )

    event: Mapped["Event"] = relationship(
        back_populates="groups",
    )
    name: Mapped[str] = mapped_column(String(50), nullable=False)

    stage: Mapped["Stage"] = relationship(back_populates="groups")

    members: Mapped[list["GroupMembers"]] = relationship(
        back_populates="group",
        cascade="save-update, delete-orphan"
    )

    tiesheets: Mapped[list["Tiesheet"]] = relationship(
        back_populates="group",
        cascade="save-update, delete-orphan"
    )

    def __repr__(self):
        return f"<Group id={self.id} name={self.name}>"


class GroupMembers(Mixins, Base):
    __tablename__ = "groupmembers"

    __table_args__ = (
        UniqueConstraint("user_id", "group_id", name="uq_groupmembers_user_id_group_id"),
    )

    group_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("groups.id", ondelete="CASCADE"),
        nullable=False,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    group: Mapped["Group"] = relationship(back_populates="members")
    user: Mapped["User"] = relationship(back_populates="group_membership")

    def __repr__(self):
        return f"<GroupMembers user_id={self.user_id} group_id={self.group_id}>"


class StandingColumn(Mixins, Base):
    __tablename__ = "standingcolumns"

    stage_id : Mapped[uuid.UUID] = mapped_column(
        ForeignKey("stages.id", ondelete="CASCADE"),
        nullable=False
    )
    column_field : Mapped[str] = mapped_column(String(255), nullable=False)
    default_value : Mapped[str] = mapped_column(String(60), nullable=True)
    to_show : Mapped[bool] = mapped_column(Boolean,default=False)

    stage: Mapped["Stage"] = relationship(back_populates="columns")
    values: Mapped[list["ColumnValues"]] = relationship(
        back_populates="column",
        cascade="save-update, delete-orphan",
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
    user: Mapped["User"] = relationship(back_populates="column_values")
    column: Mapped["StandingColumn"] = relationship(back_populates="values")

    def __repr__(self):
        return f"<Column Value value={self.value}>"


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

    status : Mapped[str] = mapped_column(String(20),nullable=True)

    players: Mapped[list["TiesheetPlayer"]] = relationship(
        back_populates="tiesheet",
        cascade="save-update, delete-orphan",
    )

    group: Mapped["Group"] = relationship(back_populates="tiesheets")
    stage: Mapped["Stage"] = relationship(back_populates="tiesheets")
    match : Mapped[list["Match"]] = relationship(back_populates="tiesheet", cascade="save-update, delete-orphan")

    def __repr__(self):
        return f"<Tiesheet id={self.id} scheduled_at={self.scheduled_date}>"


class TiesheetPlayer(Mixins,Base):
    __tablename__ = "tiesheet_players"

    tiesheet_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tiesheets.id", ondelete="CASCADE"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
    )

    is_winner: Mapped[bool] = mapped_column(Boolean, default=False)

    tiesheet: Mapped["Tiesheet"] = relationship(back_populates="players")
    user: Mapped["User"] = relationship(back_populates="tiesheetplayer")
    matchscore : Mapped[list["Tiesheetplayermatchscore"]] = relationship(back_populates="tiesheetplayer", cascade="save-update, delete-orphan")

    def __repr__(self):
        return f"<TiesheetPlayer tiesheet_id={self.tiesheet_id} user_id={self.user_id} winner={self.is_winner}>"

class Match(Mixins, Base):
    __tablename__ = "roundmatch"

    tiesheet_id : Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tiesheets.id", ondelete="CASCADE")
    )

    match_name : Mapped[str] = mapped_column(String(50),nullable=False)

    tiesheet: Mapped["Tiesheet"] = relationship(back_populates="match")
    matchscore : Mapped["Tiesheetplayermatchscore"] = relationship(back_populates="match", cascade="save-update, delete-orphan")
    
    def __repr__(self):
        return f"<Match match_id={self.id} match_name={self.match_name}>"
    
class Tiesheetplayermatchscore(Mixins, Base):
    __tablename__ = "tiesheet_player_match_score"

    match_id : Mapped[uuid.UUID] = mapped_column(
        ForeignKey("roundmatch.id", ondelete="CASCADE"),
    )

    tiesheetplayer_id : Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tiesheet_players.id", ondelete="CASCADE")
    )

    points : Mapped[str] = mapped_column(String(50), nullable=True)
    winner : Mapped[bool] = mapped_column(Boolean, default=False)
    match : Mapped["Match"] = relationship(back_populates="matchscore")
    tiesheetplayer : Mapped["TiesheetPlayer"] = relationship(back_populates="matchscore")

    __table_args__ = (
        UniqueConstraint('match_id', 'tiesheetplayer_id', name='uq_match_tiesheetplayer'),
    )

    def __repr__(self):
        return f"<Tiesheet Player Match Score id={self.id}>"

class Qualifier(Mixins, Base):
    __tablename__ = "qualifier"

    event_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("events.id", ondelete="CASCADE"), nullable=False
    )
    stage_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("stages.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    __table_args__ = (
        UniqueConstraint(
            "event_id",
            "stage_id",
            "user_id",
            name="uq_qualifier_event_stage_user",
        ),
    )

    event: Mapped["Event"] = relationship(back_populates="qualifiers")
    stage: Mapped["Stage"] = relationship(back_populates="qualifiers")
    user: Mapped["User"] = relationship(back_populates="qualifiers")

    def __repr__(self):
        return f"<Qualifier id={self.id}>"  