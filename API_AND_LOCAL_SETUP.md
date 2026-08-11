# API Documentation & Local Setup

## 1. System Overview

The application consists of three services:

| Service              |   Port | Purpose                                        |
| -------------------- | -----: | ---------------------------------------------- |
| API Gateway          | `8000` | Public API entry point and authentication      |
| User Service         | `8001` | User management and registration               |
| Notification Service | `8002` | Processes registration events and sends emails |
| NATS JetStream       | `4222` | Asynchronous messaging                         |

The client communicates with the **API Gateway**. The User Service and Notification Service communicate asynchronously through **NATS JetStream**.

---

# 2. API Documentation

FastAPI provides interactive API documentation through Swagger UI.

## API Gateway

```text
http://127.0.0.1:8000/docs
```

## User Service

```text
http://127.0.0.1:8001/docs
```

## Notification Service

```text
http://127.0.0.1:8002/docs
```

The `/docs` endpoints provide the available routes, request schemas, response schemas, and the option to test APIs directly from the browser.

---

# 3. API Gateway

The API Gateway is the public entry point for client requests.

### Base URL

```text
http://127.0.0.1:8000
```

### Authentication

Protected requests use JWT authentication.

```http
Authorization: Bearer <access_token>
```

The client should communicate with the API Gateway rather than directly accessing internal backend services.

---

# 4. User Registration

### Endpoint

```http
POST /users
```

### Purpose

Creates a new user.

### Request Body

```json
{
  "name": "Test User",
  "email": "test@example.com",
  "password": "StrongPassword123!"
}
```

### Processing Flow

```text
Client
   |
   | POST /users
   v
API Gateway
   |
   v
User Service
   |
   +------> Neon PostgreSQL
   |
   +------> NATS JetStream
                 |
                 | user.created
                 v
         Notification Service
                 |
                 v
              Email
```

### Successful Response

The User Service stores the user in Neon PostgreSQL and publishes a `user.created` event.

The Notification Service processes the event asynchronously.

### Possible Errors

```text
400 Bad Request
409 Conflict
500 Internal Server Error
```

`409 Conflict` is returned when the user already exists.

---

# 5. Get User

### Endpoint

```http
GET /users/{user_id}
```

### Purpose

Retrieves a user by ID.

### Example

```http
GET /users/1
```

### Successful Response

```json
{
  "id": 1,
  "name": "Test User",
  "email": "test@example.com"
}
```

### Possible Errors

```text
404 Not Found
```

Returned when the requested user does not exist.

---

# 6. Authentication

### Login Endpoint

```http
POST /auth/login
```

### Request

```json
{
  "email": "test@example.com",
  "password": "StrongPassword123!"
}
```

### Response

A successful login returns a JWT access token.

The token is then supplied to protected endpoints:

```http
Authorization: Bearer <access_token>
```

---

# 7. Notification Service

The Notification Service is primarily an event consumer.

It does not require the User Service to call it using REST.

### Event Subject

```text
user.created
```

### Event Publisher

```text
User Service
```

### Event Consumer

```text
Notification Service
```

### Event Processing

When the Notification Service receives a `user.created` event:

1. The event is decoded and validated.
2. User information is extracted.
3. A welcome email is sent.
4. The JetStream message is acknowledged.

The message is acknowledged **only after successful email delivery**.

---

# 8. Message Failure Handling

If email delivery fails:

```text
user.created received
        |
        v
Send email
        |
        X
   Email fails
        |
        v
No ACK
        |
        v
JetStream redelivery
```

When the service becomes available again, the unacknowledged message can be redelivered.

After successful processing:

```text
Email sent successfully
        |
        v
ACK
        |
        v
Message completed
```

The JetStream consumer is configured with an acknowledgement timeout and maximum delivery limit.

---

# 9. Local Setup

## Prerequisites

Install:

* Python 3.10+
* NATS Server
* Neon PostgreSQL database
* SMTP-enabled email account

---

# 10. Clone the Repository

```cmd
git clone https://github.com/sudharsan-051006/Trams.git
cd Trams
```

Use the actual repository directory containing the microservices assignment if the project is stored in a subdirectory.

---

# 11. Environment Variables

Create `.env` files from the provided `.env.example` files.

Do not commit `.env` files to GitHub.

---

## User Service `.env`

```env
DATABASE_URL=<NEON_DATABASE_URL>

NATS_URL=nats://localhost:4222
NATS_USER=user-service
NATS_PASSWORD=<NATS_PASSWORD>

JWT_SECRET=<JWT_SECRET>
```

---

## Notification Service `.env`

```env
NATS_URL=nats://localhost:4222
NATS_USER=notification-service
NATS_PASSWORD=<NATS_PASSWORD>

SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=<EMAIL_ADDRESS>
SMTP_PASSWORD=<EMAIL_APP_PASSWORD>
```

---

## API Gateway `.env`

Add the environment variables required by the API Gateway configuration.

Example:

```env
USER_SERVICE_URL=http://127.0.0.1:8001
JWT_SECRET=<JWT_SECRET>
```

---

# 12. Start NATS Server

The NATS executable is not included in the GitHub repository.

Download the NATS Server binary and locate:

```text
nats-server.exe
```

The project contains:

```text
nats_server.conf
```

Start NATS from the project root.

If `nats-server.exe` is available in PATH:

```cmd
nats-server.exe -c nats_server.conf -js
```

Or provide the full executable path:

```cmd
C:\path\to\nats-server.exe -c C:\path\to\project\nats_server.conf -js
```

NATS runs on:

```text
localhost:4222
```

Expected output:

```text
Starting JetStream
Listening for client connections on 0.0.0.0:4222
Server is ready
```

Keep this terminal running.

---

# 13. Install User Service

Open a new terminal:

```cmd
cd user-service
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Start the service:

```cmd
uvicorn app.main:app --reload --port 8001
```

User Service:

```text
http://127.0.0.1:8001
```

Swagger documentation:

```text
http://127.0.0.1:8001/docs
```

---

# 14. Install Notification Service

Open another terminal:

```cmd
cd notification-service
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Start the service:

```cmd
uvicorn app.main:app --reload --port 8002
```

Notification Service:

```text
http://127.0.0.1:8002
```

Swagger documentation:

```text
http://127.0.0.1:8002/docs
```

The service should display:

```text
Notification Service connected to NATS
Listening for user.created events...
```

---

# 15. Install API Gateway

Open another terminal:

```cmd
cd api-gateway
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Start the gateway:

```cmd
uvicorn app.main:app --reload --port 8000
```

API Gateway:

```text
http://127.0.0.1:8000
```

Swagger documentation:

```text
http://127.0.0.1:8000/docs
```

---

# 16. Required Terminals

The complete system requires four running processes:

```text
Terminal 1
└── NATS JetStream
    └── Port 4222

Terminal 2
└── User Service
    └── Port 8001

Terminal 3
└── Notification Service
    └── Port 8002

Terminal 4
└── API Gateway
    └── Port 8000
```

The recommended startup order is:

```text
1. NATS
   ↓
2. User Service
   ↓
3. Notification Service
   ↓
4. API Gateway
```

---

# 17. Testing the Registration Flow

Open:

```text
http://127.0.0.1:8000/docs
```

Use the registration endpoint.

Example:

```json
{
  "name": "Test User",
  "email": "test@example.com",
  "password": "StrongPassword123!"
}
```

After registration:

```text
API Gateway
     |
     v
User Service
     |
     +----> Neon PostgreSQL
     |
     +----> NATS JetStream
                |
                | user.created
                v
        Notification Service
                |
                v
           Welcome Email
                |
                v
               ACK
```

---

# 18. Verifying the Notification

The Notification Service terminal should show:

```text
📩 New user registration received!
User ID: <id>
Name: Test User
Email: test@example.com
📧 Sending welcome email...
✅ Email sent successfully.
✅ Message acknowledged by NATS.
```

The message is considered successfully processed only after the acknowledgement is sent to JetStream.

---

# 19. Failure Test

To test reliable message delivery, temporarily make the SMTP credentials invalid.

The Notification Service should show:

```text
❌ Notification failed
⚠️ Message will be redelivered.
```

Because the message was not acknowledged, JetStream keeps the message available for redelivery.

After correcting the SMTP credentials and restarting the Notification Service:

```text
📩 New user registration received!
📧 Sending welcome email...
✅ Email sent successfully.
✅ Message acknowledged by NATS.
```

This demonstrates failure recovery and reliable asynchronous processing.

---

# 20. Security Checklist

Before submitting the repository, verify:

* [ ] `.env` files are not committed.
* [ ] Real database credentials are not committed.
* [ ] SMTP passwords are not committed.
* [ ] JWT secrets are not committed.
* [ ] NATS service passwords are not committed.
* [ ] `venv/` directories are not committed.
* [ ] NATS executable is not committed.
* [ ] `jetstream/` data directory is not committed.
* [ ] `.env.example` files contain placeholders only.
* [ ] API authentication works.
* [ ] NATS authentication works.
* [ ] NATS subject permissions work.
* [ ] JetStream acknowledgement works.
* [ ] Failed messages can be redelivered.

---

# 21. Service URLs

| Component                 | URL                          |
| ------------------------- | ---------------------------- |
| API Gateway               | `http://127.0.0.1:8000`      |
| API Gateway Docs          | `http://127.0.0.1:8000/docs` |
| User Service              | `http://127.0.0.1:8001`      |
| User Service Docs         | `http://127.0.0.1:8001/docs` |
| Notification Service      | `http://127.0.0.1:8002`      |
| Notification Service Docs | `http://127.0.0.1:8002/docs` |
| NATS                      | `nats://localhost:4222`      |

---

# 22. Notes

* The API Gateway is the intended public entry point.
* The User Service and Notification Service communicate asynchronously using NATS JetStream.
* REST APIs are not used for User Service → Notification Service communication.
* JetStream provides message persistence and reliable delivery.
* Messages are manually acknowledged after successful notification processing.
* Neon PostgreSQL is used for persistent user data.
* Sensitive configuration is provided through environment variables.
* The NATS executable and local database/message data are not included in the repository.