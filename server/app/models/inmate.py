"""
Inmate data models.

Defines Pydantic models for inmate records, including create and update DTOs.
"""
from datetime import date, datetime

from pydantic import BaseModel


class Inmate(BaseModel):
    """Full inmate record."""

    id: str
    inmate_number: str
    first_name: str
    last_name: str
    date_of_birth: date
    cell_block: str
    cell_number: str
    photo_uri: str | None = None
    is_enrolled: bool = False
    enrolled_at: datetime | None = None
    is_active: bool = True
    created_at: datetime
    updated_at: datetime


class InmateCreate(BaseModel):
    """DTO for creating a new inmate."""

    inmate_number: str
    first_name: str
    last_name: str
    date_of_birth: date
    cell_block: str
    cell_number: str


class InmateUpdate(BaseModel):
    """DTO for updating an inmate (all fields optional)."""

    first_name: str | None = None
    last_name: str | None = None
    cell_block: str | None = None
    cell_number: str | None = None
    is_active: bool | None = None
