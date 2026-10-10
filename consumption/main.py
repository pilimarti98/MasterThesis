"""Pull Elering Estfeed metering data into a pandas DataFrame and write it to CSV.

The customer portal exposes two constraints that shape everything here:
  * a single request may cover at most 31 days, and
  * requests are rate limited to one every 5 seconds.

So a long range is split into windows, fetched one at a time with a throttle
between calls, and concatenated. Access tokens live for 5 minutes; rather than
track expiry we just mint a fresh one per window, which is what the API manual
recommends.
"""

from __future__ import annotations

import argparse
import sys
import time
from collections.abc import Callable, Iterator
from contextlib import ExitStack
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Final

import httpx
import pandas as pd
import structlog
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel
from pydantic_settings import BaseSettings, SettingsConfigDict

log = structlog.get_logger()

MAX_WINDOW_DAYS: Final = 31
RATE_LIMIT_SECONDS: Final = 5.0
MAX_EICS_PER_REQUEST: Final = 10
REQUEST_TIMEOUT: Final = 30.0
RETRY_AFTER_SECONDS: Final = 10.0

# Column name -> dtype. Also fixes column order, and lets an empty result still
# come back as a correctly typed frame instead of a shapeless blank one.
COLUMNS: Final[dict[str, str]] = {
    "metering_point_eic": "string",
    "period_start": "datetime64[ns, UTC]",
    "consumption_kwh": "float64",
    "production_kwh": "float64",
    "consumption_m3": "float64",
    "production_m3": "float64",
}


class EleringError(RuntimeError):
    """Raised when the portal rejects a request or returns no usable data."""


class Settings(BaseSettings):
    """Credentials and endpoints, resolved system env -> config/.env -> config/.env.example."""

    model_config = SettingsConfigDict(
        # Later files win, so config/.env overrides the committed example.
        env_file=("config/.env.example", "config/.env"),
        env_file_encoding="utf-8",
        env_prefix="ELERING_",
        extra="forbid",  # an unknown ELERING_* key is a typo, not a feature.
        # The example file ships blank credentials. Without this they'd satisfy
        # the required fields and we'd only find out at the 401.
        env_ignore_empty=True,
    )

    client_id: str
    client_secret: str = Field(repr=False)  # display guard only, not secret storage.
    eic: str
    token_url: str
    api_base_url: str


class AccountingInterval(BaseModel):
    """One measurement bucket. Gas fields stay None for an electricity point, and vice versa."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    period_start: datetime
    consumption_kwh: float | None = None
    production_kwh: float | None = None
    consumption_m3: float | None = None
    production_m3: float | None = None


class ApiError(BaseModel):
    """Per-metering-point failure; other points in the same response may still be fine."""

    model_config = ConfigDict(
        alias_generator=to_camel, populate_by_name=True, extra="allow"
    )

    message: str | None = None
    code: str | None = None
    trace_id: str | None = None


class MeteringPointData(BaseModel):
    """One metering point's slice of a response."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    metering_point_eic: str
    accounting_intervals: list[AccountingInterval] = Field(default_factory=list)
    error: ApiError | None = None


def configure_logging(*, verbose: bool = False) -> None:
    """Set up structlog for console output."""
    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="%H:%M:%S"),
            structlog.dev.ConsoleRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(10 if verbose else 20),
        # Not cached: a few dozen lines per run makes the speed-up irrelevant,
        # and caching would pin the processor chain, breaking log capture.
        cache_logger_on_first_use=False,
    )


def parse_moment(text: str) -> datetime:
    """Parse a CLI date or datetime into an aware UTC datetime. Naive input is read as UTC."""
    parsed = datetime.fromisoformat(text)
    return (
        parsed.replace(tzinfo=UTC) if parsed.tzinfo is None else parsed.astimezone(UTC)
    )


def iso_z(moment: datetime) -> str:
    """Format as the ``2024-04-01T10:00:00Z`` shape the API expects."""
    return moment.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def iter_windows(
    start: datetime, end: datetime, max_days: int = MAX_WINDOW_DAYS
) -> Iterator[tuple[datetime, datetime]]:
    """Split ``[start, end)`` into half-open windows of at most ``max_days``.

    Half-open matters: consecutive windows must not both claim the boundary
    instant, or that interval comes back twice.
    """
    if end <= start:
        raise ValueError(f"end ({iso_z(end)}) must be after start ({iso_z(start)})")

    step = timedelta(days=max_days)
    cursor = start
    while cursor < end:
        yield cursor, min(cursor + step, end)
        cursor += step


def get_access_token(client: httpx.Client, settings: Settings) -> str:
    """Exchange client credentials for a bearer token (valid ~5 minutes)."""
    log.info(
        "auth.requesting", token_url=settings.token_url, client_id=settings.client_id
    )

    response = client.post(
        settings.token_url,
        data={
            "grant_type": "client_credentials",
            "client_id": settings.client_id,
            "client_secret": settings.client_secret,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    if response.is_error:
        raise EleringError(
            f"token request failed [{response.status_code}]: {response.text}"
        )

    payload: dict[str, Any] = response.json()
    token = payload.get("access_token")
    if not isinstance(token, str):
        raise EleringError(f"token response had no access_token: {payload}")

    # `scope` is the useful bit when data comes back empty: if it lacks
    # read:metering-data, the key was issued without access at all.
    log.info(
        "auth.ok",
        scope=payload.get("scope"),
        expires_in=payload.get("expires_in"),
        token_chars=len(token),  # never the token itself.
    )
    return token


def fetch_window(
    client: httpx.Client,
    settings: Settings,
    token: str,
    start: datetime,
    end: datetime,
    eics: list[str],
    resolution: str,
    *,
    sleep: Callable[[float], None] = time.sleep,
) -> list[MeteringPointData]:
    """Fetch one <=31-day window. Retries once on 429, then gives up."""
    if len(eics) > MAX_EICS_PER_REQUEST:
        raise ValueError(
            f"at most {MAX_EICS_PER_REQUEST} metering points per request, got {len(eics)}"
        )

    params = {
        "startDateTime": iso_z(start),
        "endDateTime": iso_z(end),
        "resolution": resolution,
        "meteringPointEics": ",".join(eics),
    }
    url = f"{settings.api_base_url.rstrip('/')}/api/public/v1/metering-data"
    headers = {"Authorization": f"Bearer {token}"}

    # Built rather than sent directly so the fully-encoded URL can be logged --
    # this is the exact query that went out, paste-able into curl or a browser.
    request = client.build_request("GET", url, params=params, headers=headers)
    log.info("request.sent", method="GET", url=str(request.url))

    started = time.monotonic()
    response = client.send(request)
    if response.status_code == httpx.codes.TOO_MANY_REQUESTS:
        # We already pace ourselves, so a 429 means the budget is shared with
        # something else. One patient retry, then let it fail loudly.
        log.warning("request.rate_limited", retry_in=RETRY_AFTER_SECONDS)
        sleep(RETRY_AFTER_SECONDS)
        started = time.monotonic()
        response = client.send(
            client.build_request("GET", url, params=params, headers=headers)
        )

    log.info(
        "response.received",
        status=response.status_code,
        elapsed_ms=round((time.monotonic() - started) * 1000),
        bytes=len(response.content),
    )

    if response.is_error:
        # Body included on purpose: it carries the reason, e.g. the accepted
        # `resolution` values, which the published OpenAPI spec does not list.
        raise EleringError(
            f"metering-data request failed [{response.status_code}]: {response.text}"
        )

    points = [MeteringPointData.model_validate(item) for item in response.json()]

    if not points:
        # 200 with an empty array: the request was well-formed but matched no
        # metering point, so the EIC is almost certainly not on this API key.
        log.warning(
            "response.no_metering_points",
            requested_eics=eics,
            hint="200 OK but zero metering points -- check the EIC belongs to this API key",
            body_preview=response.text[:200],
        )

    for point in points:
        count = len(point.accounting_intervals)
        if point.error is not None or count:
            # Errors are reported by the caller; a point with data is logged here.
            if point.error is None:
                log.info("point.data", eic=point.metering_point_eic, intervals=count)
        else:
            # No error and no data: the request was accepted, there is simply
            # nothing recorded -- wrong period or resolution, or no agreement.
            log.warning(
                "point.no_data",
                eic=point.metering_point_eic,
                window=f"{iso_z(start)}..{iso_z(end)}",
                resolution=resolution,
                hint="no error returned -- period likely outside the grid agreement, "
                "or no readings at this resolution",
            )

    log.info(
        "window.done",
        window=f"{iso_z(start)}..{iso_z(end)}",
        points=len(points),
        intervals=sum(len(p.accounting_intervals) for p in points),
    )
    return points


def to_dataframe(points: list[MeteringPointData]) -> pd.DataFrame:
    """Flatten metering points into one tidy frame, deduplicated and sorted."""
    records = [
        {
            "metering_point_eic": point.metering_point_eic,
            "period_start": interval.period_start,
            "consumption_kwh": interval.consumption_kwh,
            "production_kwh": interval.production_kwh,
            "consumption_m3": interval.consumption_m3,
            "production_m3": interval.production_m3,
        }
        for point in points
        for interval in point.accounting_intervals
    ]

    frame = pd.DataFrame(records, columns=list(COLUMNS)).astype(COLUMNS)
    return (
        # Windows are half-open so overlap shouldn't happen; belt and braces in
        # case the server returns an inclusive end bound.
        frame.drop_duplicates(
            subset=["metering_point_eic", "period_start"], keep="last"
        )
        .sort_values(["metering_point_eic", "period_start"])
        .reset_index(drop=True)
    )


def fetch_metering_data(
    settings: Settings,
    start: datetime,
    end: datetime,
    resolution: str,
    *,
    eics: list[str] | None = None,
    client: httpx.Client | None = None,
    sleep: Callable[[float], None] = time.sleep,
) -> pd.DataFrame:
    """Fetch metering data for ``[start, end)`` as a DataFrame, chunking and throttling as needed."""
    targets = eics if eics is not None else [settings.eic]
    windows = list(iter_windows(start, end))
    log.info(
        "fetch.start",
        start=iso_z(start),
        end=iso_z(end),
        resolution=resolution,
        eics=targets,
        windows=len(windows),
    )

    collected: list[MeteringPointData] = []
    with ExitStack() as stack:
        if client is None:
            client = stack.enter_context(httpx.Client(timeout=REQUEST_TIMEOUT))

        for index, (window_start, window_end) in enumerate(windows):
            log.info(
                "window.start",
                n=f"{index + 1}/{len(windows)}",
                start=iso_z(window_start),
                end=iso_z(window_end),
            )
            if index:
                sleep(
                    RATE_LIMIT_SECONDS
                )  # 1 request / 5s; never sleep after the last one.

            token = get_access_token(client, settings)
            points = fetch_window(
                client,
                settings,
                token,
                window_start,
                window_end,
                targets,
                resolution,
                sleep=sleep,
            )
            for point in points:
                if point.error is not None:
                    log.warning(
                        "point.error",
                        eic=point.metering_point_eic,
                        code=point.error.code,
                        message=point.error.message,
                        trace_id=point.error.trace_id,
                    )
            collected.extend(points)

    failed = [p for p in collected if p.error is not None]
    if collected and len(failed) == len(collected):
        # Every point failed in every window — a partial result would be a lie.
        raise EleringError(
            f"all {len(failed)} metering point responses returned an error"
        )

    frame = to_dataframe(collected)
    if frame.empty:
        # Reaching here means no exception fired, so auth and every request
        # succeeded. Say so explicitly, otherwise an empty CSV looks like a bug.
        log.warning(
            "fetch.empty",
            reason="every request succeeded but returned no intervals",
            requested_eics=targets,
            window=f"{iso_z(start)}..{iso_z(end)}",
            resolution=resolution,
            points_in_responses=len(collected),
            points_with_errors=len(failed),
            hint="check the EIC, and that the period falls inside your grid agreement",
        )
    else:
        log.info(
            "fetch.done",
            rows=len(frame),
            points=frame["metering_point_eic"].nunique(),
            first=str(frame["period_start"].min()),
            last=str(frame["period_start"].max()),
        )
    return frame


def summarise(frame: pd.DataFrame) -> str:
    """One-line human summary of a result frame."""
    if frame.empty:
        return "no rows returned - the API answered successfully but had no data (see warnings above)"
    return (
        f"{len(frame)} rows | {frame['period_start'].min()} -> {frame['period_start'].max()} | "
        f"consumption {frame['consumption_kwh'].sum():.3f} kWh | "
        f"production {frame['production_kwh'].sum():.3f} kWh"
    )


def build_parser() -> argparse.ArgumentParser:
    """CLI surface."""
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--start",
        required=True,
        help="Start of period, e.g. 2026-01-01 or 2026-01-01T00:00:00Z",
    )
    parser.add_argument("--end", required=True, help="End of period (exclusive)")
    parser.add_argument(
        "--resolution",
        default="one_hour",
        help="Metering resolution passed through verbatim (default: one_hour)",
    )
    parser.add_argument(
        "--eic",
        action="append",
        help="Metering point EIC; repeatable. Defaults to ELERING_EIC",
    )
    parser.add_argument(
        "--out", type=Path, help="CSV path (default: data/<eic>_<start>_<end>.csv)"
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Debug logging")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Entry point: fetch, write CSV, print a summary."""
    args = build_parser().parse_args(argv)
    configure_logging(verbose=args.verbose)

    try:
        settings = Settings()  # values come from env/.env files.
        start, end = parse_moment(args.start), parse_moment(args.end)
        frame = fetch_metering_data(
            settings, start, end, args.resolution, eics=args.eic
        )
    except (EleringError, ValueError, httpx.HTTPError) as exc:
        log.error("fetch.failed", error=str(exc))
        return 1

    eics = args.eic or [settings.eic]
    out = args.out or Path("data") / f"{'_'.join(eics)}_{start:%Y%m%d}_{end:%Y%m%d}.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(out, index=False)

    log.info("csv.written", path=str(out), rows=len(frame))
    print(summarise(frame))
    return 0


if __name__ == "__main__":
    sys.exit(main())
