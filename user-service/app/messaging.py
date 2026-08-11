import os

import nats
from dotenv import load_dotenv
from nats.js.api import StreamConfig

load_dotenv()

NATS_URL = os.getenv("NATS_URL")
NATS_USER = os.getenv("NATS_USER")
NATS_PASSWORD = os.getenv("NATS_PASSWORD")


async def connect_nats():

    nc = await nats.connect(
        servers=[NATS_URL],
        user=NATS_USER,
        password=NATS_PASSWORD
    )

    print("✅ User Service connected to NATS")

    js = nc.jetstream()

    try:
        await js.stream_info("USER_EVENTS")
        print("✅ USER_EVENTS stream already exists")

    except Exception:
        print("⚠️ USER_EVENTS stream not found. Creating it...")

        await js.add_stream(
            config=StreamConfig(
                name="USER_EVENTS",
                subjects=["user.created"]
            )
        )

        print("✅ USER_EVENTS stream created")

    return nc, js