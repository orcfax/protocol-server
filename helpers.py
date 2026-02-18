"""Helpers."""

import asyncio
import binascii
import json
import logging
import os
import random
import statistics
import time
import uuid

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Final

import html_helper

import nanoid

import pycardano as pyc

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.hazmat.primitives import serialization


import config

logger = logging.getLogger(config.UVICORN_LOGGER)


static: Final[str] = "static"
archive: Final[str] = "archive"
keyfile: Final[str] = "keys.json"
index_html: Final[str] = "index.html"
archive_html: Final[str] = "archive.html"
data_feed_file_one: Final[str] = "datafeed_one.json"
data_feed_file_two: Final[str] = "datafeed_two.json"
UTC_TIME_FORMAT: Final[str] = "%Y-%m-%dT%H:%M:%SZ"


class KeyPair:
    """KeyPair for signing data."""

    def __init__(self):
        self.skey = pyc.PaymentSigningKey.generate()
        self.pkey = pyc.PaymentVerificationKey.from_signing_key(self.skey)

    def sign_data(self, data: bytes):
        """Generate new key-pair and sign the given data."""
        signed_data = self.skey.sign(data)
        return binascii.hexlify(signed_data).decode(), data.decode()

    @property
    def pkey_cbor(self) -> str:
        """Return pkey as cbor."""
        return self.pkey.to_cbor_hex()

    @property
    def pkey_ed25519(self) -> str:
        """Return pkey as ed25519."""
        ed25519 = Ed25519PublicKey.from_public_bytes(self.pkey.to_primitive())
        raw_bytes = ed25519.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
        return binascii.hexlify(raw_bytes).decode()

    def pkey_as_data(self) -> dict:
        """Return pkey as data + other representations."""
        ed25519 = Ed25519PublicKey.from_public_bytes(self.pkey.to_primitive())
        raw_bytes = ed25519.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
        json_data = self.pkey.to_json()
        data = json.loads(json_data)
        resp = {}
        resp["ed25519"] = binascii.hexlify(raw_bytes).decode()
        resp["cbor"] = data["cborHex"]
        return resp

    def pkey_as_pem(self) -> str:
        """Return pkey as data + other representations."""
        ed25519 = Ed25519PublicKey.from_public_bytes(self.pkey.to_primitive())
        raw_bytes = ed25519.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        return raw_bytes


class BackgroundRunner:
    """Via. https://github.com/fastapi/fastapi/issues/2713

    NB. for demonstration purposes, this code is handling two data feeds.
    Before extending it should be abstracted into a base class handling
    the generic functions and then separate abstracted classes handling
    feed specific implementations. Rules for abstraction should become
    clearer the more this is used.
    """

    max: Final[int] = 120
    seconds: Final[int] = 30

    data_feed: Final[int] = f"custom/FEED/{nanoid.generate(size=6)}"
    epoch_feed: Final[int] = f"custom/FEED/epoch1"

    def __init__(self):
        self.values = []
        self.value = 0
        self.keypair = KeyPair()
        self.uuid = f"{uuid.uuid4()}"
        self.feed = self.data_feed
        self.feed_epoch = self.epoch_feed
        self.epoch_year = 0
        self.epoch_day = 0
        with open(os.path.join(static, keyfile), "w", encoding="utf-8") as pkey:
            pkey.write(json.dumps(self.keypair.pkey_as_data(), indent=2))
        with open(os.path.join(static, index_html), "w", encoding="utf-8") as index:
            index.write(html_helper.page)

    def ls_data_files(self) -> str:
        """List files in the data directory"""
        li = ""
        for item in os.listdir(os.path.join(archive, f"{self.epoch_year}")):
            if item in (".gitignore"):
                continue
            if item.endswith("html"):
                continue
            li = f'{li}<li><a href="{self.epoch_year}/{item}">{item}</li>\n'
        return li

    def write_indices(self, data: dict, filename: str):
        """Write index adata.

        Format: JSONL:

            - key data
            - signed data

        Parsing:

            - key above data signed the data.
            - read both together to determine if correct.

        """
        date = datetime.now(timezone.utc)
        epoch_year = self.get_granular_timestamp(date.year)
        if self.epoch_year != epoch_year:
            self.epoch_year = epoch_year
        Path(f"{archive}/{epoch_year}").mkdir(parents=True, exist_ok=True)
        epoch_day = self.get_granular_timestamp(date.year, date.month, date.day)
        if self.epoch_day != epoch_day:
            self.epoch_day = epoch_day
        current_fname = f"{self.epoch_day}-{filename}".replace("json", "jsonl")
        with open(
            os.path.join(archive, f"{epoch_year}", current_fname), "a"
        ) as archive_file:
            # write key data.
            archive_file.write(json.dumps(data))
            archive_file.write("\n")
            # write data.
            archive_file.write(json.dumps(self.keypair.pkey_as_data()))
            archive_file.write("\n")
        archive_replace: Final[str] = "{{!!ARCHIVE-LIST!!}}"
        with open(os.path.join(archive, archive_html), "w") as html:
            li = self.ls_data_files()
            page = html_helper.archive.replace(archive_replace, li)
            html.write(page)

    async def write_feed_data(self, data: dict, file_name: str):
        """Write feed data."""
        with open(os.path.join(static, file_name), "w", encoding="utf-8") as datafeed:
            datafeed.write(json.dumps(data, indent=2))
        self.write_indices(data, file_name)

    async def run_main(self):
        while True:
            self.value = random.randrange(-3, 41)
            if len(self.values) > self.max:
                self.values.pop(0)
            self.values.append(self.value)
            feed_one = self.valuedata
            await self.write_feed_data(
                feed_one,
                data_feed_file_one,
            )
            feed_two = self.pluraldata
            await self.write_feed_data(feed_two, data_feed_file_two)
            await asyncio.sleep(self.seconds)

    @staticmethod
    def get_granular_timestamp(
        year: int = 1970, month: int = 1, day: int = 1, hour: int = 0
    ):
        """Return a UTC timestamp with differing granularity.

        Default return is '0'.
        """
        return int(datetime(year, month, day, hour, tzinfo=timezone.utc).timestamp())

    @property
    def pluraldata(self):
        """Return data easily pluralized.

        Current example, unix timestamp for current  hour/minute.
        """
        date = datetime.now(timezone.utc)
        epoch_hour = self.get_granular_timestamp(
            date.year, date.month, date.day, date.hour
        )
        data = {
            "feed_id": self.feed_epoch,
            "current": epoch_hour * 1000,
            "time": int(time.time()) * 1000,
        }
        signed_hex, data_hex = self.keypair.sign_data(
            binascii.hexlify(json.dumps(data).encode())
        )
        return {
            "data": data,
            "description": "current unix epoch to the hour, e.g. if 12:25 == 1771326000000 (ms)",
            "payload": data_hex,
            "signature": signed_hex,
        }

    @property
    def valuedata(self):
        """Return a signed data structure to the caller."""
        mean = self.value
        try:
            mean = statistics.mean(self.values)
        except statistics.StatisticsError:
            pass
        data = {
            "feed_id": self.feed,
            "current": self.value,
            "average": mean,
            "time": int(time.time()) * 1000,
        }
        signed_hex, data_hex = self.keypair.sign_data(
            binascii.hexlify(json.dumps(data).encode())
        )
        return {
            "data": data,
            "description": "current data and its average for the past hour including current timestamp (ms)",
            "payload": data_hex,
            "signature": signed_hex,
        }

    @property
    def valuedata_debug(self):
        """Return a signed data structure to the caller."""
        mean = self.value
        try:
            mean = statistics.mean(self.values)
        except statistics.StatisticsError:
            pass
        data = {
            "feed_id": self.feed,
            "current": self.value,
            "average": mean,
            "time": int(time.time()) * 1000,
        }
        signed_json, data_json = self.keypair.sign_data(json.dumps(data).encode())
        signed_hex, data_hex = self.keypair.sign_data(
            binascii.hexlify(json.dumps(data).encode())
        )
        return {
            "data": data,
            "description": "current data and its average for the past hour including current timestamp (ms)",
            "data (json)": data_json,
            "signature (json)": signed_json,
            "payload (hex)": data_hex,
            "signature (hex)": signed_hex,
            "pkey_cbor": self.keypair.pkey_cbor,
            "pkey_ed25519": self.keypair.pkey_ed25519,
        }
