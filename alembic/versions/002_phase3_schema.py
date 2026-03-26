"""Phase 3: Risk Engine, Wearables, Nudges, Coach Notes

Revision ID: 002
Revises: 001
Create Date: 2026-03-26

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Add 'coach' to userrole enum ──────────────────────────────────────────
    op.execute("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'coach'")

    # ── risk_scores ───────────────────────────────────────────────────────────
    op.create_table(
        "risk_scores",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("client_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("clients.id", ondelete="CASCADE"), nullable=False),
        sa.Column(
            "domain",
            sa.Enum("cardiovascular", "metabolic", "neurological", "cancer", name="riskdomain"),
            nullable=False,
        ),
        sa.Column("score", sa.Float, nullable=True),
        sa.Column(
            "rag_status",
            sa.Enum("green", "amber", "red", "insufficient_data", name="ragstatus"),
            nullable=False,
            server_default="insufficient_data",
        ),
        sa.Column("interpretation", sa.Text, nullable=True),
        sa.Column("contributing_factors", postgresql.JSONB, nullable=True),
        sa.Column("data_gaps", postgresql.JSONB, nullable=True),
        sa.Column(
            "last_calculated",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )
    op.create_index("ix_risk_scores_client_id", "risk_scores", ["client_id"])
    op.create_unique_constraint("uq_risk_scores_client_domain", "risk_scores", ["client_id", "domain"])

    # ── wearable_data ─────────────────────────────────────────────────────────
    op.create_table(
        "wearable_data",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("client_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("clients.id", ondelete="CASCADE"), nullable=False),
        sa.Column("data_date", sa.Date, nullable=False),
        sa.Column(
            "source",
            sa.Enum("whoop", "oura", "garmin", "apple_health", "manual", name="wearablesource"),
            nullable=False,
            server_default="manual",
        ),
        # Sleep
        sa.Column("sleep_hours", sa.Float, nullable=True),
        sa.Column("sleep_efficiency", sa.Float, nullable=True),
        sa.Column("deep_sleep_hours", sa.Float, nullable=True),
        sa.Column("rem_sleep_hours", sa.Float, nullable=True),
        # Recovery
        sa.Column("hrv_ms", sa.Float, nullable=True),
        sa.Column("resting_hr", sa.Integer, nullable=True),
        sa.Column("recovery_score", sa.Float, nullable=True),
        sa.Column("readiness_score", sa.Float, nullable=True),
        sa.Column("skin_temp_deviation", sa.Float, nullable=True),
        # Activity
        sa.Column("strain_score", sa.Float, nullable=True),
        sa.Column("steps", sa.Integer, nullable=True),
        sa.Column("active_calories", sa.Integer, nullable=True),
        sa.Column("zone2_minutes", sa.Integer, nullable=True),
        sa.Column("vo2_max", sa.Float, nullable=True),
        # Body
        sa.Column("weight_kg", sa.Float, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )
    op.create_index("ix_wearable_data_client_id", "wearable_data", ["client_id"])
    op.create_unique_constraint("uq_wearable_data_client_date_source", "wearable_data", ["client_id", "data_date", "source"])

    # ── nudges ────────────────────────────────────────────────────────────────
    op.create_table(
        "nudges",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("client_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("clients.id", ondelete="CASCADE"), nullable=False),
        sa.Column(
            "nudge_type",
            sa.Enum(
                "daily_checkin", "meal_reminder", "training_prompt",
                "biomarker_due", "goal_milestone", "weekly_summary", "risk_flag",
                name="nudgetype",
            ),
            nullable=False,
        ),
        sa.Column("message", sa.Text, nullable=False),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_nudges_client_id", "nudges", ["client_id"])

    # ── coach_notes ───────────────────────────────────────────────────────────
    op.create_table(
        "coach_notes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("client_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("clients.id", ondelete="CASCADE"), nullable=False),
        sa.Column("coach_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("note_text", sa.Text, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )
    op.create_index("ix_coach_notes_client_id", "coach_notes", ["client_id"])


def downgrade() -> None:
    op.drop_table("coach_notes")
    op.drop_table("nudges")
    op.drop_table("wearable_data")
    op.drop_table("risk_scores")

    op.execute("DROP TYPE IF EXISTS nudgetype")
    op.execute("DROP TYPE IF EXISTS wearablesource")
    op.execute("DROP TYPE IF EXISTS ragstatus")
    op.execute("DROP TYPE IF EXISTS riskdomain")
