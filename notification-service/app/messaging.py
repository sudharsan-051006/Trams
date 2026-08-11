import os
import json
import nats

from dotenv import load_dotenv
from .email_service import send_welcome_email


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

    print("✅ Notification Service connected to NATS")

    js = nc.jetstream()

    return nc, js


async def subscribe_to_user_created(js):

    async def message_handler(msg):

        try:
            data = json.loads(
                msg.data.decode()
            )

            print("\n📩 New user registration received!")
            print(f"User ID: {data['user_id']}")
            print(f"Name: {data['name']}")
            print(f"Email: {data['email']}")

            print("📧 Sending welcome email...")

            await send_welcome_email(
                data["email"],
                data["name"]
            )

            # ACK only after email is successfully sent
            await msg.ack()

            print("✅ Email sent successfully.")
            print("✅ Message acknowledged by NATS.")

        except Exception as e:

            print(
                f"❌ Notification failed: {e}"
            )

            print(
                "⚠️ Message will be redelivered."
            )

    await js.subscribe(
        "user.created",
        durable="notification-service",
        manual_ack=True,
        cb=message_handler
    )

    print("👂 Listening for user.created events...")