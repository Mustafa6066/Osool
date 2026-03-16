"""
Image Mirror Service
====================
Downloads property images from Nawy CDN and uploads them to
S3-compatible storage (Railway PostgreSQL S3 / Cloudflare R2 / MinIO).

This ensures image availability even if the source CDN changes URLs
or goes down, and allows serving optimised thumbnails from our own CDN.

Env vars:
  S3_ENDPOINT   – e.g. https://s3.us-east-1.amazonaws.com or R2 endpoint
  S3_BUCKET     – bucket name
  S3_ACCESS_KEY – access key ID
  S3_SECRET_KEY – secret access key
  S3_REGION     – region (default: auto)
"""

import os
import logging
import hashlib
from io import BytesIO

import httpx
import boto3
from botocore.config import Config as BotoConfig
from sqlalchemy import text

from app.database import AsyncSessionLocal

logger = logging.getLogger(__name__)

S3_ENDPOINT = os.getenv("S3_ENDPOINT", "")
S3_BUCKET = os.getenv("S3_BUCKET", "osool-images")
S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY", "")
S3_SECRET_KEY = os.getenv("S3_SECRET_KEY", "")
S3_REGION = os.getenv("S3_REGION", "auto")

_s3_client = None


def _get_s3():
    global _s3_client
    if _s3_client is None:
        if not S3_ENDPOINT or not S3_ACCESS_KEY:
            raise RuntimeError("S3 not configured — set S3_ENDPOINT + S3_ACCESS_KEY")
        _s3_client = boto3.client(
            "s3",
            endpoint_url=S3_ENDPOINT,
            aws_access_key_id=S3_ACCESS_KEY,
            aws_secret_access_key=S3_SECRET_KEY,
            region_name=S3_REGION,
            config=BotoConfig(signature_version="s3v4"),
        )
    return _s3_client


def _image_key(url: str) -> str:
    """Deterministic S3 key from source URL."""
    h = hashlib.sha256(url.encode()).hexdigest()[:16]
    ext = url.rsplit(".", 1)[-1].split("?")[0][:5] or "jpg"
    return f"properties/{h}.{ext}"


async def mirror_property_images(batch_size: int = 50):
    """
    Find properties with image_url but no mirrored_image_url,
    download from source, upload to S3, update the row.

    Called by scheduler (e.g. Sundays 05:00 UTC).
    """
    s3 = _get_s3()
    mirrored = 0
    failed = 0

    async with AsyncSessionLocal() as db:
        rows = await db.execute(
            text("""
                SELECT id, image_url
                FROM properties
                WHERE image_url IS NOT NULL
                  AND image_url != ''
                  AND (mirrored_image_url IS NULL OR mirrored_image_url = '')
                LIMIT :limit
            """),
            {"limit": batch_size},
        )
        props = rows.fetchall()

        if not props:
            logger.info("[IMAGE] No images to mirror")
            return {"mirrored": 0, "failed": 0}

        logger.info(f"[IMAGE] Mirroring {len(props)} property images...")

        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as http:
            for prop_id, image_url in props:
                try:
                    resp = await http.get(image_url)
                    resp.raise_for_status()

                    key = _image_key(image_url)
                    content_type = resp.headers.get("content-type", "image/jpeg")

                    s3.upload_fileobj(
                        BytesIO(resp.content),
                        S3_BUCKET,
                        key,
                        ExtraArgs={"ContentType": content_type},
                    )

                    # Build the public URL
                    mirrored_url = f"{S3_ENDPOINT.rstrip('/')}/{S3_BUCKET}/{key}"

                    await db.execute(
                        text("UPDATE properties SET mirrored_image_url = :url WHERE id = :id"),
                        {"url": mirrored_url, "id": prop_id},
                    )
                    mirrored += 1
                except Exception as e:
                    logger.warning(f"[IMAGE] Failed to mirror {image_url}: {e}")
                    failed += 1

        await db.commit()

    logger.info(f"[IMAGE] Done — mirrored={mirrored}, failed={failed}")
    return {"mirrored": mirrored, "failed": failed}
