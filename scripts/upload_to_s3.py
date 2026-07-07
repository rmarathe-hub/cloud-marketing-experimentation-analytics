#!/usr/bin/env python3
"""Upload local raw and processed datasets to AWS S3."""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import boto3
from botocore.exceptions import BotoCoreError, ClientError, NoCredentialsError, ProfileNotFound
from dotenv import load_dotenv

from paths import (
    AVAZU_CLEAN_PARQUET,
    AVAZU_RAW_CSV,
    HILLSTROM_CLEAN_PARQUET,
    HILLSTROM_RAW_CSV,
    PROCESSED_DIR,
    PROJECT_ROOT,
    S3_UPLOAD_SUMMARY,
)

REQUIRED_ENV_VARS = ("S3_BUCKET", "AWS_REGION")


@dataclass(frozen=True)
class UploadConfig:
    aws_profile: str | None
    aws_region: str
    bucket: str
    raw_prefix: str
    processed_prefix: str
    marts_prefix: str
    export_prefix: str


@dataclass(frozen=True)
class UploadTarget:
    local_path: Path
    s3_key: str


def load_config(env_path: Path | None = None) -> UploadConfig:
    load_dotenv(env_path or PROJECT_ROOT / ".env")

    missing = [name for name in REQUIRED_ENV_VARS if not os.getenv(name)]
    if missing:
        raise ValueError(
            "Missing required environment variables: "
            + ", ".join(missing)
            + ". Copy .env.example to .env and set your bucket details."
        )

    bucket = os.environ["S3_BUCKET"].strip()
    if not bucket or bucket == "your-bucket-name":
        raise ValueError("S3_BUCKET is not configured. Set a real bucket name in .env.")

    return UploadConfig(
        aws_profile=os.getenv("AWS_PROFILE") or None,
        aws_region=os.environ["AWS_REGION"].strip(),
        bucket=bucket,
        raw_prefix=os.getenv("S3_RAW_PREFIX", "raw").strip("/"),
        processed_prefix=os.getenv("S3_PROCESSED_PREFIX", "processed").strip("/"),
        marts_prefix=os.getenv("S3_MARTS_PREFIX", "marts").strip("/"),
        export_prefix=os.getenv("S3_EXPORT_PREFIX", "exports").strip("/"),
    )


def get_upload_targets(config: UploadConfig) -> list[UploadTarget]:
    return [
        UploadTarget(
            local_path=AVAZU_RAW_CSV,
            s3_key=f"{config.raw_prefix}/avazu_train.csv",
        ),
        UploadTarget(
            local_path=HILLSTROM_RAW_CSV,
            s3_key=f"{config.raw_prefix}/hillstrom_email.csv",
        ),
        UploadTarget(
            local_path=AVAZU_CLEAN_PARQUET,
            s3_key=f"{config.processed_prefix}/avazu_clean.parquet",
        ),
        UploadTarget(
            local_path=HILLSTROM_CLEAN_PARQUET,
            s3_key=f"{config.processed_prefix}/hillstrom_clean.parquet",
        ),
    ]


def validate_local_files(targets: list[UploadTarget]) -> None:
    missing = [str(target.local_path) for target in targets if not target.local_path.exists()]
    if missing:
        raise FileNotFoundError(
            "Missing required local files before upload:\n  - " + "\n  - ".join(missing)
        )


def create_s3_client(config: UploadConfig):
    session_kwargs: dict[str, Any] = {"region_name": config.aws_region}
    if config.aws_profile:
        session_kwargs["profile_name"] = config.aws_profile

    session = boto3.Session(**session_kwargs)
    return session.client("s3")


def verify_bucket_access(client, bucket: str) -> None:
    try:
        client.head_bucket(Bucket=bucket)
    except NoCredentialsError as exc:
        raise RuntimeError(
            "AWS credentials not found. Run `aws configure --profile marketing-analytics` "
            "or set AWS_PROFILE in .env."
        ) from exc
    except ProfileNotFound as exc:
        raise RuntimeError(
            f"AWS profile not found. Configure the profile named in AWS_PROFILE ({exc})."
        ) from exc
    except ClientError as exc:
        error_code = exc.response.get("Error", {}).get("Code", "Unknown")
        if error_code in {"404", "NoSuchBucket", "NotFound"}:
            raise RuntimeError(f"S3 bucket not found or inaccessible: {bucket}") from exc
        if error_code in {"403", "AccessDenied"}:
            raise RuntimeError(f"Access denied for S3 bucket: {bucket}") from exc
        raise RuntimeError(f"Unable to access S3 bucket {bucket}: {error_code}") from exc
    except BotoCoreError as exc:
        raise RuntimeError(f"AWS connection error while checking bucket {bucket}.") from exc


def _file_size_mb(path: Path) -> float:
    return path.stat().st_size / (1024 * 1024)


def _display_local_path(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def upload_targets(
    client,
    config: UploadConfig,
    targets: list[UploadTarget],
) -> dict[str, Any]:
    results: list[dict[str, Any]] = []

    for target in targets:
        size_mb = round(_file_size_mb(target.local_path), 2)
        entry = {
            "local_file": _display_local_path(target.local_path),
            "s3_uri": f"s3://{config.bucket}/{target.s3_key}",
            "s3_key": target.s3_key,
            "size_mb": size_mb,
            "status": "pending",
            "error": None,
        }

        try:
            client.upload_file(
                Filename=str(target.local_path),
                Bucket=config.bucket,
                Key=target.s3_key,
            )
            entry["status"] = "success"
            print(
                f"✓ {entry['local_file']} -> s3://{config.bucket}/{target.s3_key} "
                f"({size_mb:.2f} MB)"
            )
        except (ClientError, BotoCoreError) as exc:
            entry["status"] = "failed"
            entry["error"] = exc.__class__.__name__
            print(
                f"✗ {entry['local_file']} -> s3://{config.bucket}/{target.s3_key} "
                f"({size_mb:.2f} MB) [{entry['error']}]"
            )

        results.append(entry)

    failures = [item for item in results if item["status"] != "success"]
    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "bucket": config.bucket,
        "aws_region": config.aws_region,
        "aws_profile": config.aws_profile,
        "prefixes": {
            "raw": config.raw_prefix,
            "processed": config.processed_prefix,
            "marts": config.marts_prefix,
            "exports": config.export_prefix,
        },
        "uploads": results,
        "uploaded_count": sum(1 for item in results if item["status"] == "success"),
        "failed_count": len(failures),
        "success": len(failures) == 0,
    }
    return summary


def write_upload_summary(summary: dict[str, Any], path: Path | None = None) -> Path:
    output_path = path or S3_UPLOAD_SUMMARY
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(summary, indent=2))
    return output_path


def main() -> int:
    print("=" * 60)
    print("AWS S3 upload")
    print("=" * 60)

    try:
        config = load_config()
        targets = get_upload_targets(config)
        validate_local_files(targets)
        client = create_s3_client(config)
        verify_bucket_access(client, config.bucket)

        print(f"Bucket:  s3://{config.bucket}")
        print(f"Region:  {config.aws_region}")
        if config.aws_profile:
            print(f"Profile: {config.aws_profile}")
        print()

        summary = upload_targets(client, config, targets)
        output_path = write_upload_summary(summary)

        print()
        print(f"Summary written to {output_path}")
        print(
            f"Uploaded {summary['uploaded_count']} of {len(summary['uploads'])} files."
        )

        if not summary["success"]:
            return 1
        return 0

    except (ValueError, FileNotFoundError, RuntimeError) as exc:
        print(f"Upload failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
