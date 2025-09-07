"""Normalize support enums; add USER to changed_by; ensure tickets default 'new'"""

from __future__ import annotations
from alembic import op
import sqlalchemy as sa

# Идентификаторы ревизии
revision = "865cbc827c40"
down_revision = "35b0_merge_heads"  # <- укажи последнюю "merge" ревизию в твоём дереве
branch_labels = None
depends_on = None


def upgrade() -> None:
    #
    # 1) support_tickets.status → supportcasestatus ('open','pending','resolved','closed')
    #
    # тип создаём идемпотентно
    op.execute(
        """
        DO $$
        BEGIN
          IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'supportcasestatus') THEN
            CREATE TYPE supportcasestatus AS ENUM ('open','pending','resolved','closed');
          END IF;
        END$$;
        """
    )

    # снять дефолт перед сменой типа, затем enum<-text и новый дефолт
    op.execute(
        """
        DO $$
        BEGIN
          IF EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_name='support_tickets' AND column_name='status'
          ) THEN
            EXECUTE 'ALTER TABLE support_tickets ALTER COLUMN status DROP DEFAULT';
            BEGIN
              EXECUTE 'ALTER TABLE support_tickets
                         ALTER COLUMN status TYPE supportcasestatus
                         USING status::text::supportcasestatus';
            EXCEPTION
              WHEN others THEN
                NULL;
            END;
            EXECUTE $$ALTER TABLE support_tickets
                       ALTER COLUMN status SET DEFAULT 'open'::supportcasestatus$$;
          END IF;
        END$$;
        """
    )

    #
    # 2) changed_by_t — добавить значение 'USER' (если отсутствует)
    #
    with op.get_context().autocommit_block():
        op.execute(
            """
            DO $$
            BEGIN
              IF NOT EXISTS (
                SELECT 1
                FROM pg_type t
                JOIN pg_enum e ON e.enumtypid = t.oid
                WHERE t.typname = 'changed_by_t' AND e.enumlabel = 'USER'
              ) THEN
                ALTER TYPE changed_by_t ADD VALUE 'USER';
              END IF;
            END$$;
            """
        )

    #
    # 3) ticket_status_t — убедиться, что есть 'new', и дефолт для tickets.status = 'new'
    #
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE ticket_status_t ADD VALUE IF NOT EXISTS 'new';")

    op.execute(
        """
        DO $$
        BEGIN
          IF EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_name='tickets' AND column_name='status'
          ) THEN
            EXECUTE $$ALTER TABLE tickets ALTER COLUMN status SET DEFAULT 'new'$$;
          END IF;
        END$$;
        """
    )


def downgrade() -> None:
    # Откатить значения из ENUM программно нельзя просто так.
    # Делаем мягкий откат только того, что безопасно.

    # вернуть дефолт tickets.status на 'accepted'
    op.execute(
        """
        DO $$
        BEGIN
          IF EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_name='tickets' AND column_name='status'
          ) THEN
            EXECUTE $$ALTER TABLE tickets ALTER COLUMN status SET DEFAULT 'accepted'$$;
          END IF;
        END$$;
        """
    )

    # support_tickets.status перевести обратно в TEXT (тип supportcasestatus оставим, если он используется)
    op.execute(
        """
        DO $$
        BEGIN
          IF EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_name='support_tickets' AND column_name='status'
          ) THEN
            EXECUTE 'ALTER TABLE support_tickets ALTER COLUMN status DROP DEFAULT';
            BEGIN
              EXECUTE 'ALTER TABLE support_tickets
                         ALTER COLUMN status TYPE TEXT
                         USING status::text';
            EXCEPTION
              WHEN others THEN
                NULL;
            END;
          END IF;
        END$$;
        """
    )

    # Значение 'USER' в changed_by_t убирать не пытаемся (опасно).
    # Тип supportcasestatus можно удалить вручную позже, если точно не используется.