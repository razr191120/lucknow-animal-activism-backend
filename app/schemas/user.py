from __future__ import annotations

import datetime
import re
import uuid

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=255)
    password: str = Field(..., min_length=6, max_length=128)


class UserCreateLaap(BaseModel):
    """LAAP signup: same user pool as LWBP, with Aadhaar and PAN on file."""

    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=255)
    password: str = Field(..., min_length=6, max_length=128)
    aadhaar_number: str = Field(..., min_length=12, max_length=12)
    pan_number: str = Field(..., min_length=10, max_length=10)

    @field_validator("aadhaar_number")
    @classmethod
    def digits_aadhaar(cls, v: str) -> str:
        d = re.sub(r"\s+", "", v)
        if not re.fullmatch(r"\d{12}", d):
            raise ValueError("Aadhaar must be exactly 12 digits")
        return d

    @field_validator("pan_number")
    @classmethod
    def normalize_pan(cls, v: str) -> str:
        p = re.sub(r"\s+", "", v).upper()
        if not re.fullmatch(r"[A-Z]{5}\d{4}[A-Z]", p):
            raise ValueError("PAN must be in format ABCDE1234F")
        return p


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    role: str
    is_active: bool
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    full_name: str | None = None
    email: EmailStr | None = None
    role: str | None = Field(None, pattern="^(member|admin)$")
    is_active: bool | None = None


class UserUpdatePassword(BaseModel):
    new_password: str = Field(..., min_length=6, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class OAuthGoogleBody(BaseModel):
    id_token: str = Field(..., min_length=10)


class OAuthFacebookBody(BaseModel):
    access_token: str = Field(..., min_length=10)


class OAuthInstagramBody(BaseModel):
    """Instagram Basic Display: exchange `code` from redirect, or pass `access_token`."""

    code: str | None = Field(None, min_length=2)
    access_token: str | None = Field(None, min_length=10)

    @model_validator(mode="after")
    def one_of(self) -> OAuthInstagramBody:
        if not self.code and not self.access_token:
            raise ValueError("Provide either code or access_token")
        return self
