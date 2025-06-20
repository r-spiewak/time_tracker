"""This file holds base classes to hold party information."""

# import re
from typing import Any

import phonenumbers
from pydantic import BaseModel, EmailStr, field_validator

NEWLINE = "\n"


class Party(BaseModel):
    """Base class for parties of contracts (e.g., clients, me)."""

    name: str
    address: str
    email: EmailStr
    phone: str

    @field_validator("address")
    @classmethod
    def multiline_address(cls, v: Any):
        """Validate that the address contains multiple lines."""
        if NEWLINE not in v:
            raise ValueError("Address must have multiple lines.")
        return v

    # @field_validator("email")
    # @classmethod
    # def validate_company_email(cls, v: Any):
    #     """Validate that the email is in the company domain."""
    #     allowed_domains = {"example.com", "sample.com"}
    #     domain = v.split("@")[-1].lower()
    #     if domain not in allowed_domains:
    #         raise ValueError(f"Email domain '{domain}' is not allowed.")
    #     return v

    @field_validator("phone")
    @classmethod
    def validate_phone_format(cls, v: Any):
        """Validate that a phone number is in a correct format."""
        # if not re.fullmatch(r"\d{3}-\d{3}-\d{4}", v):
        #     raise ValueError("Phone number must be in the format XXX-XXX-XXXX")
        # return v
        try:  # pylint: disable=too-many-try-statements
            parsed = phonenumbers.parse(
                v, "US"
            )  # You can use "None" for unknown regions
            if not phonenumbers.is_valid_number(parsed):
                raise ValueError(f"Invalid phone number: {v}")
        except phonenumbers.NumberParseException as e:
            raise ValueError(f"Invalid phone number format: {e}") from e
        return phonenumbers.format_number(
            parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL
        )
