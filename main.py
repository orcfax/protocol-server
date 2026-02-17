"""FastAPI demo for Orcfax Express"""

import asyncio
import argparse
import binascii
import logging
import time
import importlib

from contextlib import asynccontextmanager
from typing import Final

import cbor2
import uvicorn

from cryptography import exceptions
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.hazmat.primitives import serialization

from fastapi import FastAPI, Header, Response
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles


import config
import helpers

# Set up logging.
logging.basicConfig(
    format="%(asctime)-15s %(levelname)s :: %(filename)s:%(lineno)s:%(funcName)s() :: %(message)s",  # noqa: E501
    datefmt="%Y-%m-%d %H:%M:%S",
    level="INFO",
    handlers=[
        logging.StreamHandler(),
    ],
)

# Format logs using UTC time.
logging.Formatter.converter = time.gmtime


logger = logging.getLogger(config.UVICORN_LOGGER)


TAG_DATA: Final[str] = "data"
TAG_DEBUG: Final[str] = "debug"
TAG_UTILITY: Final[str] = "utility"


@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(runner.run_main())
    yield


app = FastAPI(lifespan=lifespan)
runner = helpers.BackgroundRunner()


def all_headers(response: Response) -> Response:
    """Return all known headers."""
    response.headers["X-FEED-ID"] = runner.feed
    response.headers["X-empty-string"] = ""
    response.headers["X-NODE-ID"] = runner.uuid
    response.headers["X-ORCFAX"] = "hello Orcfax!"
    return response


@app.head("/data", include_in_schema=False)
@app.get("/data", tags=[TAG_DATA])
async def data(response: Response):
    all_headers(response)
    return runner.valuedata


@app.head("/data_debug", include_in_schema=False)
@app.get("/data_debug", tags=[TAG_DEBUG])
async def data(response: Response):
    all_headers(response)
    return runner.valuedata_debug


@app.head("/data_plural", include_in_schema=False)
@app.get("/data_plural", tags=[TAG_DATA])
async def data(response: Response):
    all_headers(response)
    return runner.pluraldata


@app.head("/pkey", include_in_schema=False)
@app.get("/pkey", tags=[TAG_DATA])
async def key(response: Response):
    all_headers(response)
    data = runner.keypair.pkey_as_data()
    return data


@app.get("/pem", tags=[TAG_UTILITY])
async def key() -> str:
    return runner.keypair.pkey_as_pem()


@app.get("/verify_cbor", tags=[TAG_UTILITY])
async def verify_signature_cbor(
    pkey: str = "58205a002828b53dd51c3081eb419494a4c47a93a220253cdca1cc39856b6ec5a2c4",
    signature: str = "49e9c8656eb5ea0db5e59039a9004199d36193dd7f01406b6af4537d0df6ceac0b6d28c3d5eeeaa2e9a99dee2c674b5be8ac6dd11c9513b125d55f4a3670ad0b",
    data: str = "7b2263757272656e74223a20312c202261766572616765223a2031302c202274696d65223a2031323334357d",
):
    pkey_data = binascii.unhexlify(pkey)
    ed25519_key = Ed25519PublicKey.from_public_bytes(cbor2.loads(pkey_data))
    unhex_signature = binascii.unhexlify(signature)
    raw_bytes = ed25519_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    try:
        ed25519_key.verify(unhex_signature, data.encode())
    except exceptions.InvalidSignature:
        return {"valid": False}

    try:
        data = binascii.unhexlify(data).decode()
    except binascii.Error:
        pass

    return {
        "valid": True,
        "signing key": pkey,
        "ed25519": raw_bytes.hex(),
        "payload": data,
    }


@app.get("/verify", tags=[TAG_UTILITY])
async def verify_signature(
    pkey: str = "5a002828b53dd51c3081eb419494a4c47a93a220253cdca1cc39856b6ec5a2c4",
    signature: str = "49e9c8656eb5ea0db5e59039a9004199d36193dd7f01406b6af4537d0df6ceac0b6d28c3d5eeeaa2e9a99dee2c674b5be8ac6dd11c9513b125d55f4a3670ad0b",
    data: str = "7b2263757272656e74223a20312c202261766572616765223a2031302c202274696d65223a2031323334357d",
):
    pkey_hex = binascii.unhexlify(pkey)
    ed25519_key = Ed25519PublicKey.from_public_bytes(pkey_hex)
    unhex_signature = binascii.unhexlify(signature)
    raw_bytes = ed25519_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    try:
        ed25519_key.verify(unhex_signature, data.encode())
    except exceptions.InvalidSignature:
        return {"valid": False}

    try:
        data = binascii.unhexlify(data).decode()
    except binascii.Error:
        pass

    return {
        "valid": True,
        "signing key": pkey,
        "ed25519": raw_bytes.hex(),
        "payload": data,
    }


# Must be defined after all the other routes.
#
# Ref: https://stackoverflow.com/a/73916745/23789970
#
app.mount("/", StaticFiles(directory="static", html=True), name="static")


def main():
    """Primary entry point for this script."""

    parser = argparse.ArgumentParser(
        prog="Orcfax Express (Demo)",
        description="Demo express server",
        epilog="for more information visit https://orcfax.io/",
    )

    parser.add_argument(
        "--port",
        help="provide a port on which to run the app",
        required=False,
        default=8001,
    )

    parser.add_argument(
        "--reload",
        help="enable reload in development mode",
        required=False,
        default=False,
        action="store_true",
    )

    parser.add_argument(
        "--workers",
        help="enable more workers",
        required=False,
        default=1,
        type=int,
    )

    args = parser.parse_args()

    logger.info(
        "attempting API startup, try setting `--port` arg if there are any issues"
    )

    import_str = "src.page.api"

    try:
        importlib.import_module(import_str)
        import_str = f"{import_str}:app"
    except ModuleNotFoundError:
        import_str = "main:app"
        logger.info("importing from %s", import_str)

    uvicorn.run(
        import_str,
        host="0.0.0.0",
        port=int(args.port),
        access_log=False,
        log_level="info",
        reload=args.reload,
        workers=args.workers,
    )


if __name__ == "__main__":
    main()
