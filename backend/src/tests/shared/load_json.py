from __future__ import annotations

import json
from typing import Any, Callable

import pytest

from core.paths import TESTS_DIR


def _load_cases_from_json(relative_path: str, key: str) -> list[Any]:
    """
    Wczytuje dane testowe z pliku JSON.
    Args:
        relative_path: Ścieżka do pliku JSON względem katalogu tests/data.
        key: Klucz w pliku JSON, pod którym znajdują się dane testowe.
        Returns:
        Lista danych testowych.
        Raises:
        KeyError: Jeśli klucz nie istnieje w pliku JSON.
    """
    file_path = TESTS_DIR / "data" / relative_path
    data = json.loads(file_path.read_text(encoding="utf-8"))

    if key not in data:
        raise KeyError(f"Key '{key}' not found in JSON file: {file_path}")

    return data[key]


def parametrize_data_from_json(
    argnames: str,
    relative_path: str,
    key: str,
) -> Callable:
    """
    Dekorator do parametryzacji testów na podstawie danych z pliku JSON.
    Args:
        argnames: Nazwy argumentów testu, oddzielone przecinkami.
        relative_path: Ścieżka do pliku JSON względem katalogu tests/data.
        key: Klucz w pliku JSON, pod którym znajdują się dane testowe.
    Returns:
        Dekorator pytest.mark.parametrize z danymi testowymi.

    Przykład użycia:
        {
            "accounts": [
                {
                    "id": "test_case_1",
                    "input": {"email": "test1@example.com"},
                    "expected": {"email": "test1@example.com"},
                },
        }
        @parametrize_data_from_json("input, expected", "accounts.json", "accounts")
        def test_account_creation(input, expected):
            # test logic here
    """
    cases = _load_cases_from_json(relative_path, key)

    params = [
        pytest.param(
            *[case[name.strip()] for name in argnames.split(",")],
            id=case.get("id", f"{key}_{index}"),
        )
        for index, case in enumerate(cases)
    ]

    return pytest.mark.parametrize(argnames, params)
