"""Initial Otto health schema

Revision ID: 001
Revises:
Create Date: 2026-03-25

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── users (admins) ────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column(
            "role",
            sa.Enum("super_admin", "admin", name="userrole"),
            nullable=False,
            server_default="admin",
        ),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── clients (health users) ────────────────────────────────────────────────
    op.create_table(
        "clients",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), nullable=True, unique=True),
        sa.Column("hashed_password", sa.String(255), nullable=True),
        sa.Column("telegram_chat_id", sa.BigInteger, nullable=True, unique=True),
        sa.Column("telegram_username", sa.String(255), nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        # Health profile
        sa.Column("date_of_birth", sa.Date, nullable=True),
        sa.Column(
            "sex",
            sa.Enum("male", "female", "other", name="biologicalsex"),
            nullable=True,
        ),
        sa.Column("height_cm", sa.Float, nullable=True),
        sa.Column("weight_kg", sa.Float, nullable=True),
        sa.Column(
            "subscription_tier",
            sa.Enum("free", "standard", "premium", name="subscriptiontier"),
            nullable=False,
            server_default="standard",
        ),
        # Nutrition targets
        sa.Column("daily_protein_target_g", sa.Integer, nullable=True),
        sa.Column("daily_fibre_target_g", sa.Integer, nullable=True),
        sa.Column("daily_calories_target", sa.Integer, nullable=True),
        # AI memory
        sa.Column("memory_summary", sa.Text, nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column(
            "created_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── conversations ─────────────────────────────────────────────────────────
    op.create_table(
        "conversations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "client_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("clients.id"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "channel",
            sa.Enum("telegram", "web", name="channel"),
            nullable=False,
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("summary", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── messages ──────────────────────────────────────────────────────────────
    op.create_table(
        "messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "conversation_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("conversations.id"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "role",
            sa.Enum("client", "otto", "system", name="messagerole"),
            nullable=False,
        ),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("token_count", sa.Integer, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── lab_results ───────────────────────────────────────────────────────────
    op.create_table(
        "lab_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "client_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("clients.id"),
            nullable=False,
            index=True,
        ),
        sa.Column("marker_name", sa.String(255), nullable=False),
        sa.Column("value", sa.Float, nullable=True),
        sa.Column("value_text", sa.String(100), nullable=True),
        sa.Column("unit", sa.String(50), nullable=True),
        sa.Column("ref_range_low", sa.Float, nullable=True),
        sa.Column("ref_range_high", sa.Float, nullable=True),
        sa.Column("optimal_low", sa.Float, nullable=True),
        sa.Column("optimal_high", sa.Float, nullable=True),
        sa.Column(
            "flag",
            sa.Enum(
                "optimal", "normal", "borderline", "high", "low",
                "critical_high", "critical_low",
                name="biomarkerflag",
            ),
            nullable=True,
        ),
        sa.Column("test_date", sa.Date, nullable=False, index=True),
        sa.Column("lab_name", sa.String(255), nullable=True),
        sa.Column("source_pdf_url", sa.String(500), nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── nutrition_log ─────────────────────────────────────────────────────────
    op.create_table(
        "nutrition_log",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "client_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("clients.id"),
            nullable=False,
            index=True,
        ),
        sa.Column("log_date", sa.Date, nullable=False, index=True),
        sa.Column(
            "meal_type",
            sa.Enum("breakfast", "lunch", "dinner", "snack", "other", name="mealtype"),
            nullable=False,
            server_default="other",
        ),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("calories", sa.Integer, nullable=True),
        sa.Column("protein_g", sa.Float, nullable=True),
        sa.Column("fat_g", sa.Float, nullable=True),
        sa.Column("carbs_net_g", sa.Float, nullable=True),
        sa.Column("fibre_g", sa.Float, nullable=True),
        sa.Column("omega3_g", sa.Float, nullable=True),
        sa.Column("alcohol_units", sa.Float, nullable=True),
        sa.Column("photo_url", sa.String(500), nullable=True),
        sa.Column("ai_analysed", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── goals ─────────────────────────────────────────────────────────────────
    op.create_table(
        "goals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "client_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("clients.id"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "domain",
            sa.Enum(
                "cardiovascular", "metabolic", "neurological", "cancer_prevention",
                "nutrition", "training", "body_composition", "sleep",
                "supplements", "general",
                name="goaldomain",
            ),
            nullable=False,
        ),
        sa.Column("goal_text", sa.Text, nullable=False),
        sa.Column("target_metric", sa.String(255), nullable=True),
        sa.Column("current_value", sa.String(100), nullable=True),
        sa.Column("target_value", sa.String(100), nullable=True),
        sa.Column("deadline", sa.Date, nullable=True),
        sa.Column(
            "status",
            sa.Enum("active", "completed", "paused", "abandoned", name="goalstatus"),
            nullable=False,
            server_default="active",
        ),
        sa.Column("interventions", sa.Text, nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── training_notes (admin guidance injected into system prompts) ──────────
    op.create_table(
        "training_notes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column(
            "conversation_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("conversations.id"),
            nullable=True,
        ),
        sa.Column(
            "message_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("messages.id"),
            nullable=True,
        ),
        sa.Column("guidance", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── documents (RAG knowledge base) ───────────────────────────────────────
    op.create_table(
        "documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column(
            "doc_type",
            sa.Enum("soul", "methodology", "coursework", "other", name="doctype"),
            nullable=False,
        ),
        sa.Column("file_path", sa.String(500), nullable=False),
        sa.Column(
            "uploaded_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=True,
        ),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── coursework ────────────────────────────────────────────────────────────
    op.create_table(
        "coursework",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column(
            "document_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("documents.id"),
            nullable=True,
        ),
        sa.Column(
            "created_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── client_coursework ─────────────────────────────────────────────────────
    op.create_table(
        "client_coursework",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "client_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("clients.id"),
            nullable=False,
        ),
        sa.Column(
            "coursework_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("coursework.id"),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum("assigned", "in_progress", "completed", name="assignmentstatus"),
            nullable=False,
            server_default="assigned",
        ),
        sa.Column("assigned_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("client_coursework")
    op.drop_table("coursework")
    op.drop_table("documents")
    op.drop_table("training_notes")
    op.drop_table("goals")
    op.drop_table("nutrition_log")
    op.drop_table("lab_results")
    op.drop_table("messages")
    op.drop_table("conversations")
    op.drop_table("clients")
    op.drop_table("users")

    # Drop enums
    for enum_name in [
        "userrole", "biologicalsex", "subscriptiontier", "channel", "messagerole",
        "biomarkerflag", "mealtype", "goaldomain", "goalstatus",
        "doctype", "assignmentstatus",
    ]:
        op.execute(f"DROP TYPE IF EXISTS {enum_name}")
