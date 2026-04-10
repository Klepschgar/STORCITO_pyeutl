from __future__ import annotations

import logging
from pathlib import Path

import polars as pl

_logger = logging.getLogger(__name__)

_ETS_DIR = Path(__file__).resolve().parent / "installation_data"
_TARGET_COUNTRIES = ("DE", "NL", "NO")
_TARGET_YEAR = 2023


def build_ets_master(ets_dir: Path) -> pl.DataFrame:
    installation = pl.scan_parquet(ets_dir / "installation.parquet")
    compliance = pl.scan_parquet(ets_dir / "compliance.parquet")
    activity_type = pl.scan_parquet(ets_dir / "activity_type.parquet")
    nace_code = pl.scan_parquet(ets_dir / "nace_code.parquet")
    country_code = pl.scan_parquet(ets_dir / "country_code.parquet")
    account = pl.scan_parquet(ets_dir / "account.parquet")
    account_holder = pl.scan_parquet(ets_dir / "account_holder.parquet")
    compliance_code = pl.scan_parquet(ets_dir / "compliance_code.parquet")

    nace_division = nace_code.filter(pl.col("level") == 2).select(
        pl.col("id").alias("nace_div_id"),
        pl.col("description").alias("nace_description"),
    )

    operator_account = (
        account.filter(pl.col("accountType_id") == "100-7")
        .select("installation_id", "companyRegistrationNumber", "accountHolder_id")
        .unique(subset=["installation_id"], keep="first")
    )

    inst_base = (
        installation.filter(pl.col("country_id").is_in(_TARGET_COUNTRIES))
        .filter(pl.col("latitudeEutl").is_not_null() | pl.col("latitudeGoogle").is_not_null())
        .with_columns(
            pl.coalesce(["latitudeEutl", "latitudeGoogle"]).alias("latitude"),
            pl.coalesce(["longitudeEutl", "longitudeGoogle"]).alias("longitude"),
            pl.col("nace_id")
            .cast(pl.Float64, strict=False)
            .floor()
            .cast(pl.Int64, strict=False)
            .cast(pl.String)
            .alias("nace_div_id"),
            pl.col("postalCode").str.strip_chars().replace("-", None).alias("postal_code"),
        )
        .join(
            activity_type.rename({"id": "activity_id", "description": "activity_description"}),
            on="activity_id",
            how="left",
        )
        .join(nace_division, on="nace_div_id", how="left")
        .join(
            country_code.rename({"id": "country_id", "description": "country_name"}),
            on="country_id",
            how="left",
        )
        .join(operator_account, left_on="id", right_on="installation_id", how="left")
        .join(
            account_holder.select(
                pl.col("id").cast(pl.Float64).alias("accountHolder_id"),
                pl.col("name").alias("account_holder_name"),
                "legalEntityIdentifier",
            ),
            on="accountHolder_id",
            how="left",
        )
        .select(
            pl.col("id").alias("installation_id"),
            pl.col("name").alias("installation_name"),
            "country_id",
            "country_name",
            "latitude",
            "longitude",
            pl.col("nace_id").cast(pl.Float64, strict=False),
            "nace_description",
            "activity_description",
            "account_holder_name",
            "companyRegistrationNumber",
            "legalEntityIdentifier",
            "postal_code",
            "city",
        )
    )

    comp_with_status = (
        compliance.filter((pl.col("year") == _TARGET_YEAR) & pl.col("verified").is_not_null())
        .join(
            compliance_code.rename({"id": "compliance_id", "description": "compliance_status"}),
            on="compliance_id",
            how="left",
        )
        .select(
            "installation_id",
            "year",
            pl.col("allocatedTotal").cast(pl.Float64, strict=False),
            pl.col("allocatedFree").cast(pl.Float64, strict=False),
            pl.col("verified").cast(pl.Float64, strict=False),
            pl.col("surrendered").cast(pl.Float64, strict=False),
            "compliance_status",
        )
    )

    return (
        comp_with_status.join(inst_base, on="installation_id", how="inner")
        .select(
            [
                "installation_id",
                "installation_name",
                pl.col("country_id").cast(pl.Categorical),
                pl.col("country_name").cast(pl.Categorical),
                "latitude",
                "longitude",
                "activity_description",
                "nace_id",
                "nace_description",
                "account_holder_name",
                "companyRegistrationNumber",
                "postal_code",
                "city",
                "year",
                "allocatedTotal",
                "allocatedFree",
                "verified",
                "surrendered",
            ]
        )
        .collect()
    )


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    output_path = _ETS_DIR / "ets_master_data.parquet"
    _logger.info("Building ETS master data from %s", _ETS_DIR)
    df = build_ets_master(_ETS_DIR)
    _logger.info(
        "%d rows, %d unique installations, %d countries",
        len(df),
        df["installation_id"].n_unique(),
        df["country_id"].n_unique(),
    )
    df.write_parquet(output_path, compression="zstd")
    _logger.info("Written to %s", output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
