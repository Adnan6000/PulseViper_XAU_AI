"""Pandas dataframe guard for strict PulseViper instrument isolation."""

from __future__ import annotations

import importlib

from typing import Any, Iterable

import pandas as pd


context_module: Any = importlib.import_module(
    "02_AI.Common.instrument_context"
)

InstrumentContext: Any = (
    context_module.InstrumentContext
)

InstrumentIsolationError: Any = (
    context_module.InstrumentIsolationError
)


class InstrumentFrameGuard:
    """Stamp and validate dataframes against one exact InstrumentContext."""

    IDENTITY_COLUMNS = (
        "pv_canonical_symbol",
        "pv_asset_class",
        "pv_broker_id",
        "pv_broker_symbol",
        "pv_account_scope_id",
        "pv_execution_environment",
        "pv_contract_spec_id",
        "pv_data_schema_version",
        "pv_feature_contract_version",
        "pv_instrument_definition_fingerprint",
        "pv_instrument_identity_fingerprint",
    )

    def __init__(
        self,
        context: Any,
    ) -> None:

        if not isinstance(
            context,
            InstrumentContext,
        ):

            raise InstrumentIsolationError(
                "INVALID_INSTRUMENT_FRAME_CONTEXT"
            )

        self.context = context

    def identity_values(
        self,
    ) -> dict[
        str,
        str,
    ]:

        return {
            "pv_canonical_symbol": (
                self.context
                .canonical_symbol
            ),
            "pv_asset_class": (
                self.context
                .asset_class
            ),
            "pv_broker_id": (
                self.context
                .broker_id
            ),
            "pv_broker_symbol": (
                self.context
                .broker_symbol
            ),
            "pv_account_scope_id": (
                self.context
                .account_scope_id
            ),
            "pv_execution_environment": (
                self.context
                .execution_environment
            ),
            "pv_contract_spec_id": (
                self.context
                .contract_spec_id
            ),
            "pv_data_schema_version": (
                self.context
                .data_schema_version
            ),
            "pv_feature_contract_version": (
                self.context
                .feature_contract_version
            ),
            "pv_instrument_definition_fingerprint": (
                self.context
                .definition
                .fingerprint
            ),
            "pv_instrument_identity_fingerprint": (
                self.context
                .identity_fingerprint
            ),
        }

    @staticmethod
    def _validate_frame_shape(
        frame: Any,
    ) -> None:

        if not isinstance(
            frame,
            pd.DataFrame,
        ):

            raise InstrumentIsolationError(
                "INSTRUMENT_FRAME_MUST_BE_DATAFRAME"
            )

        if not frame.columns.is_unique:

            raise InstrumentIsolationError(
                "INSTRUMENT_FRAME_DUPLICATE_COLUMNS"
            )

    def stamp(
        self,
        frame: pd.DataFrame,
    ) -> pd.DataFrame:

        self._validate_frame_shape(
            frame
        )

        result = frame.copy(
            deep=True
        )

        present = [
            column
            for column
            in self.IDENTITY_COLUMNS
            if column
            in result.columns
        ]

        if (
            present
            and
            len(
                present
            )
            !=
            len(
                self.IDENTITY_COLUMNS
            )
        ):

            raise InstrumentIsolationError(
                "PARTIAL_INSTRUMENT_IDENTITY_COLUMNS"
            )

        if (
            len(
                present
            )
            ==
            len(
                self.IDENTITY_COLUMNS
            )
        ):

            self.validate(
                result
            )

            return result

        for (
            column,
            value,
        ) in self.identity_values().items():

            result[
                column
            ] = value

        return result

    def validate(
        self,
        frame: pd.DataFrame,
        *,
        require_nonempty: bool = False,
    ) -> None:

        self._validate_frame_shape(
            frame
        )

        missing = [
            column
            for column
            in self.IDENTITY_COLUMNS
            if column
            not in frame.columns
        ]

        if missing:

            raise InstrumentIsolationError(
                "INSTRUMENT_IDENTITY_COLUMNS_MISSING"
            )

        if (
            require_nonempty
            and
            frame.empty
        ):

            raise InstrumentIsolationError(
                "INSTRUMENT_FRAME_EMPTY"
            )

        expected = (
            self.identity_values()
        )

        for (
            column,
            value,
        ) in expected.items():

            series = frame[
                column
            ]

            if not bool(
                series
                .eq(
                    value
                )
                .fillna(
                    False
                )
                .all()
            ):

                raise InstrumentIsolationError(
                    (
                        "INSTRUMENT_FRAME_IDENTITY_MISMATCH:"
                        f"{column}"
                    )
                )

    def concat(
        self,
        frames: Iterable[
            pd.DataFrame
        ],
        *,
        ignore_index: bool = True,
    ) -> pd.DataFrame:

        materialized = list(
            frames
        )

        if not materialized:

            return self.stamp(
                pd.DataFrame()
            )

        for frame in materialized:

            self.validate(
                frame
            )

        combined = pd.concat(
            materialized,
            ignore_index=ignore_index,
        )

        self.validate(
            combined
        )

        return combined