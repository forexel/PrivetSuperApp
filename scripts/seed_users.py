import asyncio
import random

from app.core.database import async_session_maker
from app.services.users import UserService


FIRST = [
    "Алексей", "Иван", "Павел", "Дмитрий", "Сергей", "Андрей", "Никита", "Олег", "Роман", "Илья",
    "Мария", "Анна", "Елена", "Ольга", "Наталья", "Ксения", "Виктория", "Дарья", "Юлия", "Алина",
]
LAST = [
    "Иванов", "Петров", "Сидоров", "Смирнов", "Кузнецов", "Попов", "Соколов", "Лебедев", "Новиков", "Морозов",
    "Волкова", "Козлова", "Орлова", "Егорова", "Павлова", "Семенова", "Федорова", "Крылова", "Зайцева", "Беляева",
]
STREETS = [
    "Тверская", "Арбат", "Ленинградский проспект", "Профсоюзная", "Мира", "Садовая", "Большая Ордынка",
    "Никольская", "Новослободская", "Краснопресненская", "Кутузовский проспект", "Серебряническая",
]
DOMAINS = ["gmail.ru", "mail.ru", "yandex.ru"]
PREFIXES = ["985", "977", "903"]


COUNT = 473
PASSWORD = "12345678"


def make_phone(i: int) -> str:
    prefix = PREFIXES[i % len(PREFIXES)]
    suffix = f"{i:07d}"
    return prefix + suffix


def make_name(i: int) -> str:
    return f"{FIRST[i % len(FIRST)]} {LAST[i % len(LAST)]}"


def make_email(i: int, name: str) -> str:
    local = name.lower().replace(" ", ".")
    domain = DOMAINS[i % len(DOMAINS)]
    return f"{local}.im{i}@{domain}"


def make_address(i: int) -> str:
    street = STREETS[i % len(STREETS)]
    house = (i % 120) + 1
    apt = (i % 200) + 1
    return f"г. Москва, ул. {street}, д. {house}, кв. {apt}"


async def main() -> None:
    async with async_session_maker() as session:
        service = UserService(session)
        created = 0
        for i in range(COUNT):
            name = make_name(i)
            phone = make_phone(i)
            email = make_email(i, name)
            address = make_address(i)
            try:
                await service.create(
                    phone=phone,
                    password=PASSWORD,
                    name=name,
                    email=email,
                    address=address,
                )
                created += 1
            except Exception as exc:
                print(f"skip {phone} {email}: {exc}")
            if (i + 1) % 50 == 0:
                print(f"progress: {i + 1}/{COUNT}")
        print(f"done: {created}/{COUNT}")


if __name__ == "__main__":
    asyncio.run(main())
