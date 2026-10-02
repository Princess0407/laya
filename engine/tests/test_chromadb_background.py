# Copyright 2026 Aayush Chawla
# SPDX-License-Identifier: Apache-2.0

"""Tests for background ChromaDB init (#24)."""

import pytest


@pytest.mark.asyncio
async def test_wait_for_collection_returns_connected_collection(monkeypatch):
    from laya.db import chromadb_store

    sentinel = object()
    monkeypatch.setattr(chromadb_store, "_collection", sentinel)
    assert await chromadb_store.wait_for_collection(timeout=0.1) is sentinel


@pytest.mark.asyncio
async def test_background_connect_unblocks_waiters(tmp_path, monkeypatch):
    """Callers waiting during background init get the collection once it connects (#24)."""
    import asyncio

    from laya.db import chromadb_store

    monkeypatch.setattr(chromadb_store, "CHROMADB_DIR", tmp_path)
    monkeypatch.setattr(chromadb_store, "_choose_embedding_function", lambda *args, **kwargs: None)
    monkeypatch.setattr(chromadb_store, "_collection", None)

    connecting = asyncio.create_task(chromadb_store.connect_chromadb_background())
    await asyncio.sleep(0)
    waiter = asyncio.create_task(chromadb_store.wait_for_collection(timeout=30))
    await asyncio.sleep(0)
    assert not waiter.done()

    await connecting
    assert (await waiter).name == chromadb_store.COLLECTION_NAME
    chromadb_store.disconnect_chromadb()


@pytest.mark.asyncio
async def test_background_connect_failure_fails_waiters_fast(monkeypatch):
    from laya.db import chromadb_store

    def boom():
        raise OSError("disk full")

    monkeypatch.setattr(chromadb_store, "connect_chromadb", boom)
    monkeypatch.setattr(chromadb_store, "_collection", None)

    await chromadb_store.connect_chromadb_background()
    with pytest.raises(RuntimeError):
        await chromadb_store.wait_for_collection(timeout=30)


@pytest.mark.asyncio
async def test_wait_for_collection_does_not_wait_when_not_connecting(monkeypatch):
    """With no connect in flight, behave like get_collection (no 300s stall)."""
    from laya.db import chromadb_store

    monkeypatch.setattr(chromadb_store, "_collection", None)
    with pytest.raises(RuntimeError):
        await chromadb_store.wait_for_collection()


def test_status_is_starting_while_connect_in_flight(monkeypatch):
    from laya.db import chromadb_store

    monkeypatch.setattr(chromadb_store, "_collection", None)
    monkeypatch.setattr(chromadb_store, "_connecting", True)
    assert chromadb_store.get_chromadb_status() == "starting"


def test_status_is_unhealthy_when_not_connected_and_not_connecting(monkeypatch):
    from laya.db import chromadb_store

    monkeypatch.setattr(chromadb_store, "_collection", None)
    monkeypatch.setattr(chromadb_store, "_connecting", False)
    assert chromadb_store.get_chromadb_status() == "unhealthy"


def test_status_is_healthy_once_connected(monkeypatch):
    from laya.db import chromadb_store

    class _Collection:
        def count(self) -> int:
            return 0

    monkeypatch.setattr(chromadb_store, "_collection", _Collection())
    monkeypatch.setattr(chromadb_store, "_connecting", False)
    assert chromadb_store.get_chromadb_status() == "healthy"


@pytest.mark.asyncio
async def test_status_is_unhealthy_after_failed_background_connect(monkeypatch):
    from laya.db import chromadb_store

    def boom():
        raise OSError("disk full")

    monkeypatch.setattr(chromadb_store, "connect_chromadb", boom)
    monkeypatch.setattr(chromadb_store, "_collection", None)

    await chromadb_store.connect_chromadb_background()
    assert chromadb_store.get_chromadb_status() == "unhealthy"
