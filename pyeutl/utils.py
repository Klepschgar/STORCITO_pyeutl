import os
import logging
import requests

MOST_RECENT_YEAR = 2026
FALLBACK_YEAR = 2024
# Backward compatibility for historical typo-style year input.
YEAR_ALIASES = {20245: 202405}
logger = logging.getLogger(__name__)

URLS = {
    MOST_RECENT_YEAR: None,
    FALLBACK_YEAR: "https://euets-info-public.s3.eu-central-1.amazonaws.com/eutl_2024_202410.zip",
    202405: "https://euets-info-public.s3.eu-central-1.amazonaws.com/eutl_2024_202405.zip",
    2023: "https://euets-info-public.s3.eu-central-1.amazonaws.com/eutl_2023.zip",
    2022: "https://euets-info-public.s3.eu-central-1.amazonaws.com/eutl_2022.zip",
    2021: "https://euets-info-public.s3.eu-central-1.amazonaws.com/eutl_2021.zip",
}


def download_data(
    year: int = MOST_RECENT_YEAR,
    fn_out: str | None = None,
) -> str:
    """Download data from the EUTL website for the given year.

    Args:
        year (int, optional): Year to download data for. Defaults to MOST_RECENT_YEAR.
        fn_out (str, optional): Filename to save the data to. If None, file will be saved
            to the current working directory as eutl_{year}.zip.
            Defaults to None.

    Returns:
        str: Path to the downloaded file.
    """
    resolved_year = YEAR_ALIASES.get(year, year)
    if resolved_year not in URLS:
        raise ValueError(
            f"Unsupported year '{year}'. Available keys are: {sorted(URLS.keys())}"
        )
    source_year = resolved_year
    url = URLS[source_year]
    if url is None:
        source_year = FALLBACK_YEAR
        url = URLS[source_year]
        logger.info(
            f"No configured EUTL source for {year}. "
            f"Downloading fallback data for {source_year}."
        )
    if fn_out is None:
        fn_out = os.path.join(os.getcwd(), f"eutl_{source_year}.zip")
    r = requests.get(url, allow_redirects=True)
    with open(fn_out, "wb") as fobj:
        fobj.write(r.content)
    return fn_out
