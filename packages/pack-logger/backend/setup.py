"""
Setup configuration for pack-logger Python package.

Uwaga: Warning o setuptools w IDE jest normalny - setuptools będzie dostępne
podczas instalacji paczki przez uv/pip. Ten plik jest opcjonalny (mamy pyproject.toml),
ale może być przydatny dla niektórych narzędzi.
"""
from setuptools import setup, find_packages  # type: ignore[import-untyped]

setup(
    name="pack-logger",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "rich>=14.0.0",
    ],
    extras_require={
        "django": ["django>=5.0.0"],
    },
    python_requires=">=3.12",
)