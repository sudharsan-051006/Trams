from fastapi import FastAPI

from .messaging import connect_nats, subscribe_to_user_created


app = FastAPI(title="Notification Service")

nc = None
js = None


@app.on_event("startup")
async def startup_event():
    global nc, js

    nc, js = await connect_nats()

    await subscribe_to_user_created(js)

    print("✅ Notification Service connected to NATS")
    print("👂 Listening for user.created events...")


@app.on_event("shutdown")
async def shutdown_event():
    if nc:
        await nc.close()


@app.get("/")
def root():
    return {
        "message": "Notification Service is running"
    }