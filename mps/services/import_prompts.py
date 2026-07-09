from __future__ import annotations


def prompt_project() -> str:
    return input("Project: ").strip()


def prompt_day() -> str:
    return input("Day/session: ").strip()


def prompt_year(default: int) -> int:
    value = input(f"Year [{default}]: ").strip()

    if not value:
        return default

    return int(value)
