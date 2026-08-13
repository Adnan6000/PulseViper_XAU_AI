from __future__ import annotations

import argparse
import importlib
import math
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


fetcher = importlib.import_module(
    "02_AI.Dataset.data_fetcher"
).fetcher

market_structure = importlib.import_module(
    "02_AI.Core.market_structure"
).market_structure


def section(title: str) -> None:
    print()
    print("=" * 112)
    print(title)
    print("=" * 112)


def parse_moduli(text: str) -> list[float]:

    values = [
        float(x.strip())
        for x in text.split(",")
        if x.strip()
    ]

    if (
        not values
        or any(
            value <= 0
            for value in values
        )
    ):
        raise ValueError(
            "--moduli must contain positive values"
        )

    return values


def bin_count(
    modulus: float,
    bin_size: float,
) -> int:

    if bin_size <= 0:
        raise ValueError(
            "--bin-size must be > 0"
        )

    ratio = (
        modulus
        /
        bin_size
    )

    count = int(
        round(
            ratio
        )
    )

    if (
        count < 2
        or not math.isclose(
            ratio,
            count,
            abs_tol=1e-9,
        )
    ):
        raise ValueError(
            (
                f"--bin-size {bin_size} "
                f"must divide modulus {modulus}"
            )
        )

    return count


def bucket_ids(
    values: np.ndarray,
    modulus: float,
    bin_size: float,
) -> np.ndarray:
    """
    Circular nearest-number residue buckets.

    Examples with modulus=100, bin=1:

        4313.42 -> 13
        4313.76 -> 14
        4399.80 -> 00
    """

    count = bin_count(
        modulus,
        bin_size,
    )

    residue = np.mod(
        np.asarray(
            values,
            dtype=float,
        ),
        modulus,
    )

    ids = np.floor(
        (
            residue
            /
            bin_size
        )
        +
        0.5
    ).astype(
        np.int64
    )

    return np.mod(
        ids,
        count,
    )


def hist(
    values: np.ndarray,
    modulus: float,
    bin_size: float,
) -> np.ndarray:

    count = bin_count(
        modulus,
        bin_size,
    )

    array = np.asarray(
        values,
        dtype=float,
    )

    array = array[
        np.isfinite(
            array
        )
    ]

    if array.size == 0:
        return np.zeros(
            count,
            dtype=np.int64,
        )

    return np.bincount(
        bucket_ids(
            array,
            modulus,
            bin_size,
        ),
        minlength=count,
    )


def label(
    bucket: int,
    modulus: float,
    bin_size: float,
) -> str:

    center = (
        bucket
        *
        bin_size
    )

    if (
        math.isclose(
            modulus,
            100.0,
        )
        and
        math.isclose(
            bin_size,
            1.0,
        )
    ):
        return (
            f"{int(round(center)) % 100:02d}"
        )

    return f"{center:g}"


def normal_p(
    z: float,
) -> float:

    if not np.isfinite(
        z
    ):
        return np.nan

    return math.erfc(
        abs(
            float(
                z
            )
        )
        /
        math.sqrt(
            2.0
        )
    )


def bh(
    pvalues: np.ndarray,
) -> np.ndarray:

    p = np.asarray(
        pvalues,
        dtype=float,
    )

    output = np.full_like(
        p,
        np.nan,
    )

    valid_indices = np.flatnonzero(
        np.isfinite(
            p
        )
    )

    if valid_indices.size == 0:
        return output

    valid = p[
        valid_indices
    ]

    order = np.argsort(
        valid
    )

    ordered = valid[
        order
    ]

    count = len(
        ordered
    )

    adjusted = np.empty(
        count,
        dtype=float,
    )

    running = 1.0

    for index in range(
        count - 1,
        -1,
        -1,
    ):

        running = min(
            running,
            (
                ordered[
                    index
                ]
                *
                count
                /
                (
                    index
                    +
                    1
                )
            ),
        )

        adjusted[
            index
        ] = min(
            1.0,
            running,
        )

    restore = np.empty_like(
        order
    )

    restore[
        order
    ] = np.arange(
        count
    )

    output[
        valid_indices
    ] = adjusted[
        restore
    ]

    return output


def global_mc_p(
    observed: np.ndarray,
    probabilities: np.ndarray,
    simulations: int,
    seed: int,
) -> tuple[
    float,
    float,
]:

    observed = np.asarray(
        observed,
        dtype=float,
    )

    probabilities = np.asarray(
        probabilities,
        dtype=float,
    )

    total = int(
        observed.sum()
    )

    if total <= 0:
        return (
            np.nan,
            np.nan,
        )

    probabilities = np.clip(
        probabilities,
        0,
        None,
    )

    probabilities = (
        probabilities
        /
        probabilities.sum()
    )

    expected = (
        total
        *
        probabilities
    )

    valid = (
        expected
        >
        1e-12
    )

    chi = float(
        np.sum(
            (
                observed[
                    valid
                ]
                -
                expected[
                    valid
                ]
            )
            ** 2
            /
            expected[
                valid
            ]
        )
    )

    rng = np.random.default_rng(
        seed
    )

    simulations_array = (
        rng.multinomial(
            total,
            probabilities,
            size=simulations,
        )
        .astype(
            float
        )
    )

    simulation_chi = np.sum(
        (
            simulations_array[
                :,
                valid
            ]
            -
            expected[
                valid
            ]
        )
        ** 2
        /
        expected[
            valid
        ],
        axis=1,
    )

    mc_p = (
        1
        +
        np.sum(
            simulation_chi
            >=
            chi
        )
    ) / (
        simulations
        +
        1
    )

    return (
        chi,
        float(
            mc_p
        ),
    )


def extract_swings(
    frame: pd.DataFrame,
) -> pd.DataFrame:

    required = {
        "swing_id",
        "swing_type",
        "swing_price",
        "swing_scale",
        "swing_origin_time",
    }

    missing = (
        required
        -
        set(
            frame.columns
        )
    )

    if missing:
        raise RuntimeError(
            (
                "Missing swing columns: "
                +
                ", ".join(
                    sorted(
                        missing
                    )
                )
            )
        )

    swing_id = pd.to_numeric(
        frame[
            "swing_id"
        ],
        errors="coerce",
    ).fillna(
        0
    )

    swing_price = pd.to_numeric(
        frame[
            "swing_price"
        ],
        errors="coerce",
    )

    mask = (
        (
            swing_id
            >
            0
        )
        &
        swing_price.notna()
    )

    output = frame.loc[
        mask,
        [
            "swing_id",
            "swing_type",
            "swing_price",
            "swing_scale",
            "swing_origin_time",
        ],
    ].copy()

    output[
        "swing_id"
    ] = pd.to_numeric(
        output[
            "swing_id"
        ],
        errors="coerce",
    ).astype(
        "int64"
    )

    output[
        "swing_price"
    ] = pd.to_numeric(
        output[
            "swing_price"
        ],
        errors="coerce",
    )

    output[
        "swing_type"
    ] = (
        output[
            "swing_type"
        ]
        .astype(
            str
        )
        .str
        .upper()
    )

    output[
        "swing_scale"
    ] = (
        output[
            "swing_scale"
        ]
        .astype(
            str
        )
        .str
        .upper()
    )

    output[
        "swing_origin_time"
    ] = pd.to_datetime(
        output[
            "swing_origin_time"
        ],
        errors="coerce",
    )

    return (
        output
        .sort_values(
            "swing_id"
        )
        .reset_index(
            drop=True
        )
    )


def expected_probs(
    raw: pd.DataFrame,
    swings: pd.DataFrame,
    modulus: float,
    bin_size: float,
) -> np.ndarray:
    """
    Baseline is ordinary market HIGH/LOW residues.

    HIGH swings are compared against normal candle highs.
    LOW swings are compared against normal candle lows.

    For mixed ALL swings, the baseline is weighted by the
    actual HIGH/LOW swing mix.
    """

    high_hist = hist(
        pd.to_numeric(
            raw[
                "high"
            ],
            errors="coerce",
        ).to_numpy(
            float
        ),
        modulus,
        bin_size,
    ).astype(
        float
    )

    low_hist = hist(
        pd.to_numeric(
            raw[
                "low"
            ],
            errors="coerce",
        ).to_numpy(
            float
        ),
        modulus,
        bin_size,
    ).astype(
        float
    )

    high_probability = (
        high_hist
        /
        high_hist.sum()
    )

    low_probability = (
        low_hist
        /
        low_hist.sum()
    )

    types = swings[
        "swing_type"
    ]

    high_count = int(
        (
            types
            ==
            "HIGH"
        ).sum()
    )

    low_count = int(
        (
            types
            ==
            "LOW"
        ).sum()
    )

    total = (
        high_count
        +
        low_count
    )

    if total <= 0:
        return (
            high_probability
            +
            low_probability
        ) / 2

    return (
        high_probability
        *
        (
            high_count
            /
            total
        )
        +
        low_probability
        *
        (
            low_count
            /
            total
        )
    )


def residue_table(
    raw: pd.DataFrame,
    swings: pd.DataFrame,
    modulus: float,
    bin_size: float,
    simulations: int,
    seed: int,
) -> tuple[
    pd.DataFrame,
    float,
    float,
]:

    observed = hist(
        swings[
            "swing_price"
        ].to_numpy(
            float
        ),
        modulus,
        bin_size,
    ).astype(
        float
    )

    probabilities = expected_probs(
        raw,
        swings,
        modulus,
        bin_size,
    )

    total = int(
        observed.sum()
    )

    rows: list[
        dict[
            str,
            Any,
        ]
    ] = []

    pvalues: list[
        float
    ] = []

    for index in range(
        len(
            observed
        )
    ):

        count = int(
            observed[
                index
            ]
        )

        probability = float(
            probabilities[
                index
            ]
        )

        expected = (
            total
            *
            probability
        )

        variance = (
            total
            *
            probability
            *
            (
                1
                -
                probability
            )
        )

        z = (
            (
                count
                -
                expected
            )
            /
            math.sqrt(
                variance
            )
            if variance > 0
            else np.nan
        )

        p = normal_p(
            z
        )

        pvalues.append(
            p
        )

        rows.append(
            {
                "residue": label(
                    index,
                    modulus,
                    bin_size,
                ),

                "bucket_id": (
                    index
                ),

                "swings": (
                    count
                ),

                "swing_pct": (
                    count
                    /
                    total
                    *
                    100
                    if total
                    else np.nan
                ),

                "baseline_pct": (
                    probability
                    *
                    100
                ),

                "expected": (
                    expected
                ),

                "enrichment": (
                    count
                    /
                    expected
                    if expected > 0
                    else np.nan
                ),

                "z": (
                    z
                ),

                "p": (
                    p
                ),
            }
        )

    table = pd.DataFrame(
        rows
    )

    table[
        "q_bh"
    ] = bh(
        np.asarray(
            pvalues
        )
    )

    chi, mc_p = global_mc_p(
        observed,
        probabilities,
        simulations,
        seed,
    )

    return (
        table,
        chi,
        mc_p,
    )


def top_table(
    table: pd.DataFrame,
    top: int,
    minimum_count: int,
) -> pd.DataFrame:

    output = table.loc[
        table[
            "swings"
        ]
        >=
        minimum_count
    ].copy()

    if output.empty:
        return output

    output = (
        output
        .sort_values(
            [
                "q_bh",
                "enrichment",
                "swings",
            ],
            ascending=[
                True,
                False,
                False,
            ],
        )
        .head(
            top
        )
    )

    output = output[
        [
            "residue",
            "swings",
            "swing_pct",
            "baseline_pct",
            "expected",
            "enrichment",
            "z",
            "q_bh",
        ]
    ].copy()

    for column in (
        "swing_pct",
        "baseline_pct",
        "expected",
        "enrichment",
        "z",
        "q_bh",
    ):

        output[
            column
        ] = pd.to_numeric(
            output[
                column
            ],
            errors="coerce",
        ).round(
            3
        )

    return output


def build_eras(
    raw: pd.DataFrame,
    days: int,
    eras: int,
) -> list[
    tuple[
        str,
        set[
            str
        ],
    ]
]:

    dates = (
        pd.to_datetime(
            raw[
                "time"
            ],
            errors="coerce",
        )
        .dt
        .strftime(
            "%Y-%m-%d"
        )
        .dropna()
        .drop_duplicates()
        .tolist()
    )

    possible = min(
        eras,
        len(
            dates
        )
        //
        days,
    )

    if possible <= 0:
        return []

    selected = dates[
        -possible * days:
    ]

    result: list[
        tuple[
            str,
            set[
                str
            ],
        ]
    ] = []

    for index in range(
        possible
    ):

        chunk = selected[
            index * days:
            (
                index
                +
                1
            )
            *
            days
        ]

        result.append(
            (
                (
                    f"{chunk[0]} "
                    f"-> {chunk[-1]}"
                ),
                set(
                    chunk
                ),
            )
        )

    return result


def era_stability(
    raw: pd.DataFrame,
    swings: pd.DataFrame,
    candidate_ids: list[int],
    days: int,
    eras: int,
    bin_size: float,
) -> pd.DataFrame:

    periods = build_eras(
        raw,
        days,
        eras,
    )

    if not periods:
        return pd.DataFrame()

    raw_dates = (
        pd.to_datetime(
            raw[
                "time"
            ],
            errors="coerce",
        )
        .dt
        .strftime(
            "%Y-%m-%d"
        )
    )

    swing_dates = (
        swings[
            "swing_origin_time"
        ]
        .dt
        .strftime(
            "%Y-%m-%d"
        )
    )

    rows: list[
        dict[
            str,
            Any,
        ]
    ] = []

    for candidate in candidate_ids:

        for (
            era_name,
            era_dates,
        ) in periods:

            era_raw = raw.loc[
                raw_dates.isin(
                    era_dates
                )
            ]

            era_swings = swings.loc[
                swing_dates.isin(
                    era_dates
                )
            ]

            if era_swings.empty:
                continue

            observed = hist(
                era_swings[
                    "swing_price"
                ].to_numpy(
                    float
                ),
                100.0,
                bin_size,
            )

            probabilities = expected_probs(
                era_raw,
                era_swings,
                100.0,
                bin_size,
            )

            count = int(
                observed[
                    candidate
                ]
            )

            expected = (
                len(
                    era_swings
                )
                *
                float(
                    probabilities[
                        candidate
                    ]
                )
            )

            rows.append(
                {
                    "residue": label(
                        candidate,
                        100.0,
                        bin_size,
                    ),

                    "era": (
                        era_name
                    ),

                    "swings": (
                        count
                    ),

                    "expected": round(
                        expected,
                        2,
                    ),

                    "enrichment": (
                        round(
                            count
                            /
                            expected,
                            3,
                        )
                        if expected > 0
                        else np.nan
                    ),
                }
            )

    return pd.DataFrame(
        rows
    )


def transition_table(
    swings: pd.DataFrame,
    bin_size: float,
    minimum_from: int,
    top: int,
) -> pd.DataFrame:

    if len(
        swings
    ) < 2:
        return pd.DataFrame()

    ids = bucket_ids(
        swings[
            "swing_price"
        ].to_numpy(
            float
        ),
        100.0,
        bin_size,
    )

    from_ids = ids[
        :-1
    ]

    to_ids = ids[
        1:
    ]

    count_bins = bin_count(
        100.0,
        bin_size,
    )

    destination_base = np.bincount(
        to_ids,
        minlength=count_bins,
    ).astype(
        float
    )

    destination_base = (
        destination_base
        /
        destination_base.sum()
    )

    rows: list[
        dict[
            str,
            Any,
        ]
    ] = []

    for from_id in np.unique(
        from_ids
    ):

        mask = (
            from_ids
            ==
            from_id
        )

        from_count = int(
            mask.sum()
        )

        if from_count < minimum_from:
            continue

        destination_counts = np.bincount(
            to_ids[
                mask
            ],
            minlength=count_bins,
        )

        for to_id in np.flatnonzero(
            destination_counts
        ):

            transition_count = int(
                destination_counts[
                    to_id
                ]
            )

            conditional_probability = (
                transition_count
                /
                from_count
            )

            base_probability = float(
                destination_base[
                    to_id
                ]
            )

            lift = (
                conditional_probability
                /
                base_probability
                if base_probability > 0
                else np.nan
            )

            rows.append(
                {
                    "from": label(
                        int(
                            from_id
                        ),
                        100.0,
                        bin_size,
                    ),

                    "to": label(
                        int(
                            to_id
                        ),
                        100.0,
                        bin_size,
                    ),

                    "from_n": (
                        from_count
                    ),

                    "transition_n": (
                        transition_count
                    ),

                    "p_to_given_from": round(
                        conditional_probability,
                        3,
                    ),

                    "destination_base": round(
                        base_probability,
                        3,
                    ),

                    "lift": round(
                        float(
                            lift
                        ),
                        3,
                    ),
                }
            )

    if not rows:
        return pd.DataFrame()

    return (
        pd.DataFrame(
            rows
        )
        .sort_values(
            [
                "lift",
                "transition_n",
            ],
            ascending=[
                False,
                False,
            ],
        )
        .head(
            top
        )
        .reset_index(
            drop=True
        )
    )


def main() -> None:

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--symbol",
        default="XAUUSDm",
    )

    parser.add_argument(
        "--bars",
        type=int,
        default=150000,
    )

    parser.add_argument(
        "--moduli",
        default="100,50,25,20,10,5",
    )

    parser.add_argument(
        "--bin-size",
        type=float,
        default=1.0,
    )

    parser.add_argument(
        "--top",
        type=int,
        default=20,
    )

    parser.add_argument(
        "--minimum-count",
        type=int,
        default=3,
    )

    parser.add_argument(
        "--simulations",
        type=int,
        default=3000,
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=42,
    )

    parser.add_argument(
        "--era-days",
        type=int,
        default=40,
    )

    parser.add_argument(
        "--eras",
        type=int,
        default=3,
    )

    parser.add_argument(
        "--candidate-count",
        type=int,
        default=12,
    )

    parser.add_argument(
        "--min-transition-from",
        type=int,
        default=8,
    )

    args = parser.parse_args()

    if args.bars <= 0:
        raise ValueError(
            "--bars must be > 0"
        )

    if (
        args.top <= 0
        or
        args.minimum_count <= 0
        or
        args.simulations <= 0
    ):
        raise ValueError(
            (
                "top/minimum-count/"
                "simulations must be > 0"
            )
        )

    moduli = parse_moduli(
        args.moduli
    )

    for modulus in moduli:
        bin_count(
            modulus,
            args.bin_size,
        )

    section(
        "PulseViper Swing Price Lattice Forensic Diagnostic"
    )

    print(
        f"Requested symbol : {args.symbol}"
    )

    print(
        f"Requested bars   : {args.bars}"
    )

    print(
        (
            "Moduli           : "
            +
            ", ".join(
                f"{modulus:g}"
                for modulus
                in moduli
            )
        )
    )

    print(
        (
            "Residue bin      : "
            f"nearest {args.bin_size:g} price unit"
        )
    )

    print(
        "Production impact : NONE"
    )

    print()

    print(
        "Fetching broker history..."
    )

    raw = fetcher.fetch(
        symbol=args.symbol,
        bars=args.bars,
    )

    if raw.empty:
        raise RuntimeError(
            "No usable MT5 history returned"
        )

    print(
        f"Fetched bars     : {len(raw)}"
    )

    resolved = str(
        getattr(
            fetcher,
            "last_resolved_symbol",
            "",
        )
    )

    if resolved:
        print(
            f"Resolved symbol  : {resolved}"
        )

    print()

    print(
        "Running frozen causal MarketStructure..."
    )

    structured = (
        market_structure.generate(
            raw
        )
    )

    swings = extract_swings(
        structured
    )

    if swings.empty:
        raise RuntimeError(
            "No confirmed swings generated"
        )

    section(
        "SWING SAMPLE"
    )

    print(
        f"Confirmed swings : {len(swings)}"
    )

    print(
        (
            "HIGH             : "
            f"{int((swings['swing_type'] == 'HIGH').sum())}"
        )
    )

    print(
        (
            "LOW              : "
            f"{int((swings['swing_type'] == 'LOW').sum())}"
        )
    )

    print()

    print(
        swings[
            "swing_scale"
        ]
        .value_counts()
        .rename_axis(
            "scale"
        )
        .reset_index(
            name="swings"
        )
        .to_string(
            index=False
        )
    )

    print()

    print(
        (
            "First origin     : "
            f"{swings['swing_origin_time'].min()}"
        )
    )

    print(
        (
            "Last origin      : "
            f"{swings['swing_origin_time'].max()}"
        )
    )

    full_100: (
        pd.DataFrame
        |
        None
    ) = None

    for modulus in moduli:

        section(
            (
                f"MODULO {modulus:g} "
                "— GLOBAL DISTRIBUTION"
            )
        )

        summary_rows: list[
            dict[
                str,
                Any,
            ]
        ] = []

        categories = [
            (
                "ALL",
                pd.Series(
                    True,
                    index=swings.index,
                ),
            ),

            (
                "HIGH",
                swings[
                    "swing_type"
                ]
                ==
                "HIGH",
            ),

            (
                "LOW",
                swings[
                    "swing_type"
                ]
                ==
                "LOW",
            ),
        ]

        for (
            name,
            mask,
        ) in categories:

            subset = swings.loc[
                mask
            ].copy()

            (
                table,
                chi,
                mc_p,
            ) = residue_table(
                raw,
                subset,
                modulus,
                args.bin_size,
                args.simulations,
                (
                    args.seed
                    +
                    int(
                        modulus
                        *
                        100
                    )
                    +
                    len(
                        name
                    )
                ),
            )

            significant = table.loc[
                (
                    table[
                        "q_bh"
                    ]
                    <=
                    0.05
                )
                &
                (
                    table[
                        "enrichment"
                    ]
                    >
                    1
                )
            ]

            summary_rows.append(
                {
                    "category": (
                        name
                    ),

                    "n": (
                        len(
                            subset
                        )
                    ),

                    "chi_square": round(
                        chi,
                        3,
                    ),

                    "global_mc_p": round(
                        mc_p,
                        5,
                    ),

                    "q05_enriched_bins": (
                        len(
                            significant
                        )
                    ),
                }
            )

            if (
                name == "ALL"
                and
                math.isclose(
                    modulus,
                    100.0,
                )
            ):
                full_100 = (
                    table.copy()
                )

        print(
            pd.DataFrame(
                summary_rows
            ).to_string(
                index=False
            )
        )

        (
            all_table,
            _,
            all_p,
        ) = residue_table(
            raw,
            swings,
            modulus,
            args.bin_size,
            args.simulations,
            (
                args.seed
                +
                int(
                    modulus
                    *
                    1000
                )
            ),
        )

        print()

        print(
            (
                "Top ALL-swing residues | "
                f"global Monte Carlo p="
                f"{all_p:.5f}"
            )
        )

        display = top_table(
            all_table,
            args.top,
            args.minimum_count,
        )

        print(
            (
                display.to_string(
                    index=False
                )
                if not display.empty
                else
                "No supported buckets."
            )
        )

    if 100.0 in moduli:

        for side in (
            "HIGH",
            "LOW",
        ):

            section(
                f"MODULO 100 — {side} DETAIL"
            )

            subset = swings.loc[
                swings[
                    "swing_type"
                ]
                ==
                side
            ].copy()

            (
                table,
                chi,
                mc_p,
            ) = residue_table(
                raw,
                subset,
                100.0,
                args.bin_size,
                args.simulations,
                (
                    args.seed
                    +
                    (
                        1001
                        if side == "HIGH"
                        else 1002
                    )
                ),
            )

            print(
                (
                    f"n={len(subset)} | "
                    f"chi-square={chi:.3f} | "
                    f"global Monte Carlo p="
                    f"{mc_p:.5f}"
                )
            )

            print()

            display = top_table(
                table,
                args.top,
                args.minimum_count,
            )

            print(
                (
                    display.to_string(
                        index=False
                    )
                    if not display.empty
                    else
                    "No supported buckets."
                )
            )

    if full_100 is not None:

        candidates = (
            full_100.loc[
                full_100[
                    "swings"
                ]
                >=
                args.minimum_count
            ]
            .sort_values(
                [
                    "q_bh",
                    "enrichment",
                    "swings",
                ],
                ascending=[
                    True,
                    False,
                    False,
                ],
            )
            .head(
                args.candidate_count
            )
        )

        candidate_ids = [
            int(
                value
            )
            for value
            in candidates[
                "bucket_id"
            ].tolist()
        ]

        section(
            "MODULO 100 — ERA CONSISTENCY"
        )

        stability = era_stability(
            raw,
            swings,
            candidate_ids,
            args.era_days,
            args.eras,
            args.bin_size,
        )

        if stability.empty:

            print(
                (
                    "Insufficient data "
                    "for era consistency."
                )
            )

        else:

            print(
                stability.to_string(
                    index=False
                )
            )

            rows = []

            for (
                residue,
                group,
            ) in stability.groupby(
                "residue"
            ):

                enrichment = pd.to_numeric(
                    group[
                        "enrichment"
                    ],
                    errors="coerce",
                ).dropna()

                rows.append(
                    {
                        "residue": (
                            residue
                        ),

                        "eras": (
                            len(
                                enrichment
                            )
                        ),

                        "eras_enriched_gt1": int(
                            (
                                enrichment
                                >
                                1
                            ).sum()
                        ),

                        "median_enrichment": (
                            round(
                                float(
                                    enrichment.median()
                                ),
                                3,
                            )
                            if len(
                                enrichment
                            )
                            else np.nan
                        ),

                        "min_enrichment": (
                            round(
                                float(
                                    enrichment.min()
                                ),
                                3,
                            )
                            if len(
                                enrichment
                            )
                            else np.nan
                        ),
                    }
                )

            print()

            print(
                "Era summary:"
            )

            print(
                pd.DataFrame(
                    rows
                )
                .sort_values(
                    [
                        "eras_enriched_gt1",
                        "median_enrichment",
                    ],
                    ascending=[
                        False,
                        False,
                    ],
                )
                .to_string(
                    index=False
                )
            )

        section(
            (
                "MODULO 100 — "
                "CONSECUTIVE SWING TRANSITIONS"
            )
        )

        transitions = transition_table(
            swings,
            args.bin_size,
            args.min_transition_from,
            args.top,
        )

        print(
            (
                transitions.to_string(
                    index=False
                )
                if not transitions.empty
                else
                "No supported transitions."
            )
        )

    section(
        "INTERPRETATION"
    )

    print(
        "Interesting only if:"
    )

    print(
        (
            "1. global Monte Carlo p "
            "is small;"
        )
    )

    print(
        (
            "2. specific residues survive "
            "BH correction (q_bh <= 0.05);"
        )
    )

    print(
        (
            "3. the same residues stay "
            "enriched across eras;"
        )
    )

    print(
        (
            "4. HIGH/LOW behavior has "
            "enough support;"
        )
    )

    print(
        (
            "5. transition lifts later survive "
            "an independent sample."
        )
    )

    print()

    print(
        (
            "A positive result proves a repeatable "
            "numerical swing lattice relative to "
            "ordinary candle highs/lows. It does NOT "
            "by itself prove a hidden broker/server "
            "algorithm."
        )
    )


if __name__ == "__main__":
    main()