import argparse
from pathlib import Path


def export_installation_site_data(
    output_dir: Path, year: int = 2026, zip_file: Path | None = None, keep_zip: bool = False
) -> None:
    from pyeutl import download_data
    from pyeutl.ziploader import (
        get_account_holders,
        get_accounts,
        get_compliance,
        get_installations,
        get_transactions,
    )

    output_dir.mkdir(parents=True, exist_ok=True)

    downloaded_zip = False
    if zip_file is None:
        zip_file = output_dir / f"eutl_{year}.zip"
        download_data(year=year, fn_out=str(zip_file))
        downloaded_zip = True

    df_installations = get_installations(str(zip_file))
    df_account_holders = get_account_holders(str(zip_file))
    df_accounts = get_accounts(
        str(zip_file),
        df_installation=df_installations,
        df_accountHolder=df_account_holders,
    )
    df_compliance = get_compliance(str(zip_file), df_installation=df_installations)
    df_transactions = get_transactions(str(zip_file), df_account=df_accounts)

    df_installations.to_csv(output_dir / "installations.csv", index=False)
    df_compliance.to_csv(output_dir / "installation_compliance.csv", index=False)
    df_accounts.to_csv(output_dir / "installation_accounts.csv", index=False)
    df_account_holders.to_csv(output_dir / "account_holders.csv", index=False)
    df_transactions.to_csv(output_dir / "installation_transactions.csv", index=False)

    if downloaded_zip and not keep_zip:
        zip_file.unlink(missing_ok=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download and export installation-site relevant EUTL data."
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("installation_data"),
        help="Directory where exported CSV files are written.",
    )
    parser.add_argument(
        "--year",
        type=int,
        default=2026,
        help="EUTL source year key to download (defaults to latest configured key).",
    )
    parser.add_argument(
        "--zip-file",
        type=Path,
        default=None,
        help="Optional path to an existing EUTL zip file to avoid downloading.",
    )
    parser.add_argument(
        "--keep-zip",
        action="store_true",
        help="Keep downloaded zip file in output directory.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    export_installation_site_data(
        output_dir=args.output_dir,
        year=args.year,
        zip_file=args.zip_file,
        keep_zip=args.keep_zip,
    )
    print(f"Export complete: {args.output_dir.resolve()}")


if __name__ == "__main__":
    main()
