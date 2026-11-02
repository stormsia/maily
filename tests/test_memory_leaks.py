from __future__ import annotations

import gc
import tracemalloc
from datetime import datetime, timezone

import httpx
import pytest

from maily.schemas import MessageDetailOut


@pytest.mark.asyncio
async def test_memory_httpx_client_lifecycle_no_leaks():
    """Verify 500 async HTTP client sessions leave no uncollected memory leaks."""
    gc.collect()
    tracemalloc.start()
    snapshot_before = tracemalloc.take_snapshot()

    for _ in range(500):
        transport = httpx.MockTransport(
            lambda req: httpx.Response(200, json={"status": "ok"})
        )
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            resp = await client.get("/health")
            assert resp.status_code == 200

    gc.collect()
    snapshot_after = tracemalloc.take_snapshot()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    top_stats = snapshot_after.compare_to(snapshot_before, "lineno")
    total_leaked_bytes = sum(stat.size_diff for stat in top_stats if stat.size_diff > 0)
    total_leaked_mb = total_leaked_bytes / (1024 * 1024)
    peak_mb = peak / (1024 * 1024)

    # Peak memory during 500 client requests should stay under 25 MB
    assert peak_mb < 25.0, f"Peak memory was too high: {peak_mb:.2f} MB"
    # Uncollected memory difference must be under 2 MB (no leak in transport/client)
    assert (
        total_leaked_mb < 2.0
    ), f"Memory leak detected: {total_leaked_mb:.2f} MB uncollected"


def test_memory_batch_message_processing_high_watermark():
    """Verify processing 5,000 message models remains under 25 MB RAM and cleans up completely."""
    sample_payload = {
        "id": 101,
        "message_api_id": "msg_mem_test_9988",
        "subject": "Security verification code: 928374",
        "from_address": "security@service.example.com",
        "from_name": "Security Center",
        "seen": False,
        "has_attachments": False,
        "size": 2048,
        "received_at": datetime.now(timezone.utc),
        "text": "Your login code is 928374. Do not share with anyone.",
        "html": ["<p>Your login code is <b>928374</b></p>"],
    }

    gc.collect()
    tracemalloc.start()

    # Process 5,000 models in batches of 100
    for _ in range(50):
        batch = [MessageDetailOut.model_validate(sample_payload) for _ in range(100)]
        dumped = [m.model_dump(mode="json") for m in batch]
        assert len(dumped) == 100
        del batch
        del dumped

    gc.collect()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    peak_mb = peak / (1024 * 1024)
    current_mb = current / (1024 * 1024)

    # High watermark assertion: peak memory must remain strictly under 25 MB
    assert peak_mb < 25.0, f"Processing peak memory exceeded limit: {peak_mb:.2f} MB"
    # Retained memory after garbage collection must be under 1.5 MB
    assert (
        current_mb < 1.5
    ), f"Retained memory too high after batch processing: {current_mb:.2f} MB"


def test_memory_crypto_rotation_memory_stability():
    """Verify repeated Fernet encryption/decryption cycles do not leak buffer memory."""
    from cryptography.fernet import Fernet

    from maily.crypto import decrypt, encrypt

    key = Fernet.generate_key().decode()
    payload = "X" * 4096  # 4 KB payload

    gc.collect()
    tracemalloc.start()

    for _ in range(1000):
        cipher = encrypt(key, payload)
        plain = decrypt(key, cipher)
        assert len(plain) == 4096

    gc.collect()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    peak_mb = peak / (1024 * 1024)
    current_mb = current / (1024 * 1024)

    assert peak_mb < 15.0, f"Crypto peak memory exceeded: {peak_mb:.2f} MB"
    assert current_mb < 1.0, f"Crypto retained memory too high: {current_mb:.2f} MB"
