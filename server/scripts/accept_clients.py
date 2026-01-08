import asyncio
import json
import random
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, text

from app.core.database import async_session_maker
from app.models.users import User


PLAN_CHOICES = ["simple", "medium", "premium"]
PERIOD_CHOICES = ["month", "year"]


def make_contract_number(client_id: str, idx: int) -> str:
    short = client_id.replace("-", "")[:6].upper()
    return f"DA-{short}-{idx:04d}"


async def main() -> None:
    random.seed(42)
    now = datetime.now(timezone.utc)

    async with async_session_maker() as session:
        managers = (await session.execute(text("SELECT id FROM manager_users WHERE is_active = true"))).scalars().all()
        tariffs = await session.execute(
            text("SELECT id, name, base_fee, extra_per_device FROM manager_tariffs")
        )
        tariff_rows = list(tariffs.mappings())

        clients = await session.execute(text("SELECT id, user_id FROM manager_clients ORDER BY created_at ASC"))
        client_rows = list(clients.mappings())
        if not client_rows:
            print("No manager_clients found. Aborting.")
            return

        created = 0
        for idx, row in enumerate(client_rows, start=1):
            client_id = str(row["id"])
            user_id = str(row["user_id"])
            manager_id = str(managers[idx % len(managers)]) if managers else None
            tariff = random.choice(tariff_rows) if tariff_rows else None
            if tariff:
                tariff_snapshot = {
                    "id": str(tariff["id"]),
                    "name": tariff["name"],
                    "base_fee": str(tariff["base_fee"]),
                    "extra_per_device": str(tariff["extra_per_device"]),
                }
            else:
                ut = await session.execute(
                    text(
                        """
                        SELECT tariff_id, device_count, total_extra_fee
                        FROM user_tariffs
                        WHERE client_id = :client_id
                        """
                    ),
                    {"client_id": client_id},
                )
                ut_row = ut.mappings().first()
                tariff_snapshot = {
                    "tariff_id": str(ut_row["tariff_id"]) if ut_row and ut_row["tariff_id"] else None,
                    "device_count": int(ut_row["device_count"]) if ut_row else 0,
                    "total_extra_fee": str(ut_row["total_extra_fee"]) if ut_row else "0",
                    "placeholder": True,
                }
            passport_snapshot = {"placeholder": True}
            device_snapshot = {"placeholder": True}

            contract_number = make_contract_number(client_id, idx)
            contract_url = f"https://app.privetsuper.ru/contracts/{contract_number}.pdf"

            plan = random.choice(PLAN_CHOICES)
            period = random.choice(PERIOD_CHOICES)
            paid_until = now + (timedelta(days=365) if period == "year" else timedelta(days=30))

            await session.execute(
                text(
                    """
                    UPDATE manager_clients
                    SET assigned_manager_id = :manager_id,
                        status = 'processed',
                        updated_at = now()
                    WHERE id = :client_id
                    """
                ),
                {"manager_id": manager_id, "client_id": client_id},
            )

            if tariff:
                await session.execute(
                    text(
                        """
                        INSERT INTO user_tariffs
                            (id, client_id, tariff_id, device_count, total_extra_fee, calculated_at, created_at, updated_at)
                        VALUES
                            (:id, :client_id, :tariff_id, 0, 0, now(), now(), now())
                        ON CONFLICT (client_id) DO UPDATE SET
                            tariff_id = EXCLUDED.tariff_id,
                            calculated_at = now(),
                            updated_at = now()
                        """
                    ),
                    {
                        "id": str(uuid.uuid4()),
                        "client_id": client_id,
                        "tariff_id": str(tariff["id"]),
                    },
                )

            await session.execute(
                text(
                    """
                    INSERT INTO user_contracts
                        (id, client_id, tariff_snapshot, passport_snapshot, device_snapshot,
                         signed_at, payment_confirmed_at, contract_url, contract_number,
                         signed_ip, signed_user_agent, created_at, updated_at)
                    VALUES
                        (:id, :client_id, :tariff_snapshot::json, :passport_snapshot::json, :device_snapshot::json,
                         :signed_at, :payment_confirmed_at, :contract_url, :contract_number,
                         :signed_ip, :signed_user_agent, now(), now())
                    ON CONFLICT (client_id) DO UPDATE SET
                        tariff_snapshot = EXCLUDED.tariff_snapshot,
                        passport_snapshot = EXCLUDED.passport_snapshot,
                        device_snapshot = EXCLUDED.device_snapshot,
                        signed_at = EXCLUDED.signed_at,
                        payment_confirmed_at = EXCLUDED.payment_confirmed_at,
                        contract_url = EXCLUDED.contract_url,
                        contract_number = EXCLUDED.contract_number,
                        signed_ip = EXCLUDED.signed_ip,
                        signed_user_agent = EXCLUDED.signed_user_agent,
                        updated_at = now()
                    """
                ),
                {
                    "id": str(uuid.uuid4()),
                    "client_id": client_id,
                    "tariff_snapshot": json.dumps(tariff_snapshot),
                    "passport_snapshot": json.dumps(passport_snapshot),
                    "device_snapshot": json.dumps(device_snapshot),
                    "signed_at": now,
                    "payment_confirmed_at": now,
                    "contract_url": contract_url,
                    "contract_number": contract_number,
                    "signed_ip": "127.0.0.1",
                    "signed_user_agent": "seed-script",
                },
            )

            await session.execute(
                text("UPDATE subscriptions SET active = false WHERE user_id = :user_id"),
                {"user_id": user_id},
            )
            await session.execute(
                text(
                    """
                    INSERT INTO subscriptions
                        (id, user_id, plan, period, active, started_at, paid_until, created_at, updated_at)
                    VALUES
                        (:id, :user_id, :plan, :period, true, :started_at, :paid_until, now(), now())
                    """
                ),
                {
                    "id": str(uuid.uuid4()),
                    "user_id": user_id,
                    "plan": plan,
                    "period": period,
                    "started_at": now,
                    "paid_until": paid_until,
                },
            )
            await session.execute(
                text("UPDATE users SET has_subscription = true WHERE id = :user_id"),
                {"user_id": user_id},
            )

            created += 1
            if created % 50 == 0:
                print(f"progress: {created}/{len(client_rows)}")

        await session.commit()
        print(f"done: {created}/{len(client_rows)}")


if __name__ == "__main__":
    asyncio.run(main())
