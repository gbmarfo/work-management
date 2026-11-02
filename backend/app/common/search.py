"""Shared search helpers for list endpoints."""

from sqlalchemy import or_
from sqlalchemy.orm import Query


def apply_search(query: Query, term: str | None, *columns) -> Query:
    if not term or not str(term).strip():
        return query
    pattern = f"%{term.strip()}%"
    return query.filter(or_(*[col.ilike(pattern) for col in columns]))
