"""Schemas for the Masker package.

Pydantic models defining the masking/hydration contract. The
:class:`MaskingContract` is the immutable agreement between the
two phases — every placeholder created during masking must be
resolvable during hydration, or the operation fails fast.
"""

from __future__ import annotations

import re

from pydantic import BaseModel, Field


class MaskingContract(BaseModel):
    """Immutable contract linking masking and hydration phases.

    Guarantees that every placeholder created while masking can be
    resolved during hydration. A hydration attempt encountering a
    placeholder NOT present in this contract fails immediately.

    Attributes
    ----------
    placeholder_map : dict
        Mapping of ``[CATEGORY#N]`` placeholders to original values.
    count : int
        Total number of unique placeholders in the contract.
    """

    placeholder_map: dict[str, str] = Field(
        default_factory=dict,
        description="Placeholder-to-original-value mapping.",
        examples=[{"[RESIDENT_REGISTRATION_NUMBER#1]": "901212-1234567"}],
    )
    count: int = Field(
        default=0,
        ge=0,
        description="Total number of placeholders created.",
        examples=[3],
    )

    def validate_response(self, text: str) -> list[str]:
        """Validate that every placeholder in *text* is resolvable.

        Parameters
        ----------
        text : str
            The LLM response to validate.

        Returns
        -------
        list of str
            Placeholders found in *text* that are **not** in
            :attr:`placeholder_map`. An empty list means the
            response is safe to hydrate.
        """
        found = set(re.findall(r"\[[A-Z][A-Z0-9_]*#\d+\]", text))
        return [p for p in found if p not in self.placeholder_map]


class MaskingResult(BaseModel):
    """Result of a masking operation.

    Attributes
    ----------
    masked_text : str
        Text with sensitive spans replaced by placeholders.
    contract : MaskingContract
        Immutable contract for the subsequent hydration phase.
    """

    masked_text: str = Field(
        ...,
        description="Text with sensitive spans replaced by placeholders.",
        examples=["주민등록번호 [RESIDENT_REGISTRATION_NUMBER#1] 기재"],
    )
    contract: MaskingContract = Field(
        ..., description="The immutable hydration contract."
    )


class HydrationResult(BaseModel):
    """Result of a hydration operation.

    Attributes
    ----------
    hydrated_text : str
        Text with placeholders restored to original values.
    placeholders_restored : int
        How many placeholder replacements were performed.
    unresolved : list of str
        Always empty for a successful hydration (fail-fast otherwise).
    """

    hydrated_text: str = Field(
        ...,
        description="Text with all placeholders restored to original values.",
        examples=["주민등록번호 901212-1234567 기재"],
    )
    placeholders_restored: int = Field(
        ...,
        ge=0,
        description="Number of placeholder → original value replacements.",
        examples=[2],
    )
    unresolved: list[str] = Field(
        default_factory=list,
        description="Unresolvable placeholders (always empty on success).",
    )
