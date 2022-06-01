"""empty message

Revision ID: f3530249ad5f
Revises: 73765744a1f6
Create Date: 2022-04-12 14:15:34.964524+00:00

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from Backend.database import Roles, RolesActivity, RolesActivityTimePeriod, RolesCollectibles

# revision identifiers, used by Alembic.
revision = "f3530249ad5f"
down_revision = "73765744a1f6"
branch_labels = None
depends_on = None


def get_role(session: Session, r_id: int) -> Roles:
    query = select(Roles).filter_by(role_id=r_id)
    return session.execute(query).scalars().first()


def add_role(session: Session, entry: dict, old_entries: dict):
    req_role = get_role(session, entry[0])
    if req_role:
        return

    role_data = entry[2]

    role = Roles(
        role_id=entry[0],
        guild_id=entry[1],
        category=role_data["category"],
        deprecated=role_data["deprecated"],
        acquirable=role_data["acquirable"],
        requirement_require_activity_completions=[
            RolesActivity(
                allowed_activity_hashes=data["allowed_activity_hashes"],
                count=data["count"],
                allow_checkpoints=data["allow_checkpoints"],
                require_team_flawless=data["require_team_flawless"],
                require_individual_flawless=data["require_individual_flawless"],
                require_score=data["require_score"],
                require_kills=data["require_kills"],
                require_kills_per_minute=data["require_kills_per_minute"],
                require_kda=data["require_kda"],
                require_kd=data["require_kd"],
                maximum_allowed_players=data["maximum_allowed_players"],
                allow_time_periods=[
                    RolesActivityTimePeriod(
                        start_time=time_period["start_time"],
                        end_time=time_period["end_time"],
                    )
                    for time_period in data["allow_time_periods"]
                ],
                disallow_time_periods=[
                    RolesActivityTimePeriod(
                        start_time=time_period["start_time"],
                        end_time=time_period["end_time"],
                    )
                    for time_period in data["disallow_time_periods"]
                ],
                inverse=data["inverse"],
            )
            for data in role_data["require_activity_completions"]
        ],
        requirement_require_collectibles=[
            RolesCollectibles(
                bungie_id=data["id"],
                inverse=data["inverse"],
            )
            for data in role_data["require_collectibles"]
        ],
        requirement_require_records=[
            RolesCollectibles(
                bungie_id=data["id"],
                inverse=data["inverse"],
            )
            for data in role_data["require_records"]
        ],
    )

    if role_data["require_role_ids"]:
        for r in role_data["require_role_ids"]:
            role_id = r["id"]
            req_role = get_role(session, role_id)

            if not req_role:
                for entry in old_entries:
                    if entry[0] == role_id:
                        add_role(session, entry, old_entries)

                req_role = get_role(session, role_id)
                if not req_role:
                    # data is missing, do not add this role
                    print(f"Missing data (req_role `{role_id}`) for role `{entry[0]}`, not adding it...")
                    return

            role.requirement_require_roles.append(req_role)

    session.add(role)
    session.flush()


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint("activitiesUsers_activity_instance_id_fkey", "activitiesUsers", type_="foreignkey")
    op.create_foreign_key(
        None, "activitiesUsers", "activities", ["activity_instance_id"], ["instance_id"], ondelete="CASCADE"
    )
    op.drop_constraint("activitiesUsersWeapons_user_id_fkey", "activitiesUsersWeapons", type_="foreignkey")
    op.create_foreign_key(None, "activitiesUsersWeapons", "activitiesUsers", ["user_id"], ["id"], ondelete="CASCADE")

    # move table to temp
    op.rename_table("roles", "roles_temp")

    # create the new tables
    op.create_table(
        "roles",
        sa.Column("_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("role_id", sa.BigInteger(), nullable=False),
        sa.Column("guild_id", sa.BigInteger(), nullable=False),
        sa.Column("category", sa.Text(), nullable=False),
        sa.Column("deprecated", sa.Boolean(), nullable=False),
        sa.Column("acquirable", sa.Boolean(), nullable=False),
        sa.Column("_replaced_by_role_id", sa.BigInteger(), nullable=True),
        sa.ForeignKeyConstraint(["_replaced_by_role_id"], ["roles.role_id"], ondelete="SET NULL"),  # noqa
        sa.PrimaryKeyConstraint("_id"),
        sa.UniqueConstraint("role_id"),
    )
    op.create_table(
        "requiredRolesAssociation",
        sa.Column("parent_role_id", sa.BigInteger(), nullable=False),
        sa.Column("require_role_id", sa.BigInteger(), nullable=False),
        sa.ForeignKeyConstraint(["parent_role_id"], ["roles.role_id"], ondelete="CASCADE"),  # noqa
        sa.ForeignKeyConstraint(["require_role_id"], ["roles.role_id"], ondelete="CASCADE"),  # noqa
        sa.PrimaryKeyConstraint("parent_role_id", "require_role_id"),
    )
    op.create_table(
        "rolesActivity",
        sa.Column("_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("role_id", sa.BigInteger(), nullable=True),
        sa.Column("allowed_activity_hashes", sa.ARRAY(sa.BigInteger()), nullable=False),
        sa.Column("count", sa.Integer(), nullable=False),
        sa.Column("allow_checkpoints", sa.Boolean(), nullable=False),
        sa.Column("require_team_flawless", sa.Boolean(), nullable=False),
        sa.Column("require_individual_flawless", sa.Boolean(), nullable=False),
        sa.Column("require_score", sa.Integer(), nullable=True),
        sa.Column("require_kills", sa.Integer(), nullable=True),
        sa.Column("require_kills_per_minute", sa.Float(), nullable=True),
        sa.Column("require_kda", sa.Float(), nullable=True),
        sa.Column("require_kd", sa.Float(), nullable=True),
        sa.Column("maximum_allowed_players", sa.Integer(), nullable=False),
        sa.Column("inverse", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["role_id"], ["roles.role_id"], onupdate="CASCADE", ondelete="CASCADE"),  # noqa
        sa.PrimaryKeyConstraint("_id"),
    )
    op.create_table(
        "rolesInteger",
        sa.Column("_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("role_id", sa.BigInteger(), nullable=True),
        sa.Column("bungie_id", sa.BigInteger(), nullable=False),
        sa.Column("inverse", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["role_id"], ["roles.role_id"], onupdate="CASCADE", ondelete="CASCADE"),  # noqa
        sa.PrimaryKeyConstraint("_id"),
    )
    op.create_table(
        "rolesActivityTimePeriod",
        sa.Column("_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("role_activity_id", sa.Integer(), nullable=True),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["role_activity_id"], ["rolesActivity._id"], onupdate="CASCADE", ondelete="CASCADE"
        ),  # noqa
        sa.PrimaryKeyConstraint("_id"),
    )

    # move the old data to the new table
    bind = op.get_bind()
    session = Session(bind=bind)

    old_entries = bind.execute("select role_id, guild_id, role_data from roles_temp").fetchall()  # noqa

    # add roles
    for entry in old_entries:
        add_role(session, entry, old_entries)  # noqa

    # add the replaced_by field
    for entry in old_entries:
        role_data = entry[2]

        if role_data["replaced_by_role_id"]:
            role = get_role(session, entry[0])
            if not role:
                print(f"Could not get role from db for role {entry[0]}, skipping")
                continue

            rep_role = get_role(session, role_data["replaced_by_role_id"])
            if not rep_role:
                # data is missing, do not add this role
                print(
                    f"Missing data (rep_role `{rep_role.role_id}`) for role `{entry[0]}`, leaving that empty instead..."
                )
                continue

            role.requirement_replaced_by_role = rep_role
            flag_modified(role, "requirement_replaced_by_role")

            session.flush()

    # delete old roles data table
    op.drop_table("roles_temp")
    # ### end Alembic commands ###


def downgrade():
    raise NotImplementedError
