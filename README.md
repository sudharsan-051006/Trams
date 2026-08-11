# Microservices User Registration & Notification System

A small **event-driven microservices system** designed to demonstrate distributed systems concepts including asynchronous communication, secure inter-service communication, reliable message delivery, authentication, validation, and scalable service architecture.

---

## Architecture

```text
                              Client
                                |
                                | HTTP
                                v
                     +----------------------+
                     |     API Gateway      |
                     |        :8000         |
                     |     JWT Auth         |
                     +----------+-----------+
                                |
                                | HTTP
                                v
                     +----------------------+
                     |     User Service     |
                     |        :8001         |
                     +----------+-----------+
                                |
                    +-----------+-----------+
                    |                       |
                    |                       |
                    v                       v
             +-------------+       +------------------+
             |    Neon     |       |  NATS JetStream  |
             | PostgreSQL  |       |                  |
             +-------------+       |  user.created    |
                                   +--------+---------+
                                            |
                                            | Async Event
                                            v
                                  +---------------------+
                                  | Notification Service|
                                  |        :8002        |
                                  +----------+----------+
                                             |
                                             | SMTP
                                             v
                                       Welcome Email
```

### Communication Model

The **User Service and Notification Service do not communicate through REST APIs or WebSockets**.

They communicate asynchronously through:

```text
User Service
     |
     | publish: user.created
     v
NATS JetStream
     |
     | consume
     v
Notification Service
```

---

# 1. Project Overview

The system allows users to register through an API Gateway.

After registration:

1. The API Gateway forwards the request to the User Service.
2. The User Service validates the data.
3. The user is stored in Neon PostgreSQL.
4. The User Service publishes a `user.created` event to NATS JetStream.
5. The Notification Service consumes the event asynchronously.
6. A welcome email is sent to the registered user.
7. The message is acknowledged only after successful email delivery.

This architecture keeps the User Service independent from the Notification Service.

---

# 2. Components

## API Gateway

**Port:** `8000`

The API Gateway acts as the public entry point for clients.

Responsibilities:

* Route client requests
* Authentication
* JWT validation
* Request handling
* Prevent direct exposure of internal services

API documentation:

```text
http://127.0.0.1:8000/docs
```

---

## User Service

**Port:** `8001`

Responsibilities:

* User registration
* User authentication
* User retrieval
* Input validation
* Password hashing
* PostgreSQL persistence
* Publishing `user.created` events

The User Service communicates with the Notification Service only through NATS JetStream.

API documentation:

```text
http://127.0.0.1:8001/docs
```

---

## Notification Service

**Port:** `8002`

Responsibilities:

* Consume `user.created` events
* Send welcome emails
* Handle email failures
* Acknowledge successfully processed messages
* Allow failed messages to be redelivered

API documentation:

```text
http://127.0.0.1:8002/docs
```

---

# 3. Technology Stack

* Python 3.10+
* FastAPI
* SQLAlchemy
* PostgreSQL
* Neon PostgreSQL
* NATS
* NATS JetStream
* JWT
* Argon2
* Pydantic
* SMTP
* Uvicorn

---

# 4. Event Flow

When a new user registers:

```text
Client
  |
  v
API Gateway
  |
  | HTTP
  v
User Service
  |
  +----------------------+
  |                      |
  v                      v
Neon PostgreSQL       NATS JetStream
                         |
                         | user.created
                         v
                Notification Service
                         |
                         v
                   SMTP Server
                         |
                         v
                    User Email
```

The important point is that the User Service **does not wait for the email to be sent**.

The notification process happens asynchronously.

---

# 5. NATS and JetStream

## NATS

NATS is used as the message broker between the User Service and Notification Service.

The User Service publishes:

```text
user.created
```

The Notification Service subscribes to:

```text
user.created
```

## JetStream

JetStream provides persistence and reliable message delivery.

Messages are stored in the:

```text
USER_EVENTS
```

stream.

The stream captures:

```text
user.created
```

events.

---

# 6. Reliable Message Delivery

The Notification Service uses a durable JetStream consumer with manual acknowledgement.

The message is acknowledged only after successful processing.

```text
Message received
       |
       v
Send email
       |
       +------ SUCCESS ------> ACK
       |
       |
       +------ FAILURE ------> No ACK
                                |
                                v
                         Message redelivered
```

The consumer uses an acknowledgement timeout and maximum delivery limit.

This prevents successfully processed messages from being repeatedly delivered while still allowing failed messages to be retried.

---

# 7. Failure Handling

The system was tested with an SMTP authentication failure.

When email delivery failed:

```text
📩 New user registration received!
📧 Sending welcome email...
❌ Notification failed
⚠️ Message will be redelivered.
```

Because the message was not acknowledged, JetStream retained the unacknowledged event.

After the Notification Service was restarted with valid SMTP credentials:

```text
📩 New user registration received!
📧 Sending welcome email...
✅ Email sent successfully.
✅ Message acknowledged by NATS.
```

This demonstrates reliable asynchronous processing and recovery from service failures.

---

# 8. Security

## JWT Authentication

The API Gateway uses JWT-based authentication for protected endpoints.

```text
Client
  |
  | Login
  v
API Gateway
  |
  v
JWT Access Token
  |
  v
Protected Endpoints
```

Protected requests use:

```http
Authorization: Bearer <access_token>
```

---

## Password Security

User passwords are never stored as plaintext.

Passwords are hashed using **Argon2** before being stored in PostgreSQL.

---

## NATS Authentication

NATS authentication is enabled.

Separate credentials are used for the services:

```text
user-service
notification-service
```

NATS permissions restrict access to the subjects required by each service.

The services also have access to the NATS request/reply subjects required for JetStream operations.

---

## Environment Variables

Sensitive values are stored in environment variables.

Examples include:

* Database credentials
* JWT secret
* NATS credentials
* SMTP credentials

Actual `.env` files are not committed to the repository.

---

# 9. Project Structure

```text
microservices-assignment/
│
├── api-gateway/
│   ├── app/
│   │   └── main.py
│   ├── requirements.txt
│   └── .env.example
│
├── user-service/
│   ├── app/
│   │   ├── main.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── database.py
│   │   ├── auth.py
│   │   └── messaging.py
│   ├── requirements.txt
│   └── .env.example
│
├── notification-service/
│   ├── app/
│   │   ├── main.py
│   │   ├── messaging.py
│   │   └── email_service.py
│   ├── requirements.txt
│   └── .env.example
│
├── nats_server.conf
├── .gitignore
└── README.md
```

---

# 10. Prerequisites

Install the following before running the project:

* Python 3.10 or later
* NATS Server
* Neon PostgreSQL database
* SMTP-enabled email account

---

# 11. NATS Server Setup

NATS Server is required to run the messaging layer.

The NATS executable is **not included in this repository**.

Download the NATS Server binary for your operating system and make `nats-server` available in your PATH.

For Windows, the executable is:

```text
nats-server.exe
```

The repository contains:

```text
nats_server.conf
```

which contains the NATS server configuration, JetStream configuration, and authentication settings.

---

# 12. Start NATS Server

Open a terminal in the project root.

If `nats-server.exe` is available in your PATH:

```cmd
nats-server.exe -c nats_server.conf -js
```

Alternatively, provide the full path to the executable:

```cmd
C:\path\to\nats-server.exe -c C:\path\to\microservices-assignment\nats_server.conf -js
```

Example on Windows:

```cmd
E:\Downloads\nats-server-v2.14.4-windows-amd64\nats-server.exe -c D:\Internships\Trams\microservices-assignment\nats_server.conf -js
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

# 13. Environment Configuration

Create `.env` files using the provided `.env.example` files.

## User Service

Example:

```env
DATABASE_URL=<NEON_DATABASE_URL>

NATS_URL=nats://localhost:4222
NATS_USER=user-service
NATS_PASSWORD=<NATS_PASSWORD>

JWT_SECRET=<JWT_SECRET>
```

## Notification Service

Example:

```env
NATS_URL=nats://localhost:4222
NATS_USER=notification-service
NATS_PASSWORD=<NATS_PASSWORD>

SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=<EMAIL_ADDRESS>
SMTP_PASSWORD=<EMAIL_APP_PASSWORD>
```

## API Gateway

Use the environment variables required by the gateway configuration.

**Never commit real credentials to GitHub.**

---

# 14. Install Dependencies

Each service has its own Python environment.

## User Service

```cmd
cd user-service
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## Notification Service

```cmd
cd notification-service
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## API Gateway

```cmd
cd api-gateway
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

---

# 15. Run the Services

The system requires four terminals.

## Terminal 1 — NATS

```cmd
nats-server.exe -c nats_server.conf -js
```

Port:

```text
4222
```

---

## Terminal 2 — User Service

```cmd
cd user-service
venv\Scripts\activate
uvicorn app.main:app --reload --port 8001
```

Port:

```text
8001
```

---

## Terminal 3 — Notification Service

```cmd
cd notification-service
venv\Scripts\activate
uvicorn app.main:app --reload --port 8002
```

Port:

```text
8002
```

---

## Terminal 4 — API Gateway

```cmd
cd api-gateway
venv\Scripts\activate
uvicorn app.main:app --reload --port 8000
```

Port:

```text
8000
```

---

# 16. Service Ports

| Component            |   Port |
| -------------------- | -----: |
| NATS                 | `4222` |
| API Gateway          | `8000` |
| User Service         | `8001` |
| Notification Service | `8002` |

The client should communicate with the **API Gateway** rather than directly accessing the internal services.

---

# 17. API Documentation

FastAPI automatically provides OpenAPI/Swagger documentation.

### API Gateway

```text
http://127.0.0.1:8000/docs
```

### User Service

```text
http://127.0.0.1:8001/docs
```

### Notification Service

```text
http://127.0.0.1:8002/docs
```

---

# 18. User Registration

A typical registration request:

```http
POST /users
```

Example:

```json
{
  "name": "Test User",
  "email": "test@example.com",
  "password": "StrongPassword123!"
}
```

The request flows through:

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
                  v
          Notification Service
                  |
                  v
              Email
```

---

# 19. Authentication

Login is performed through the API.

Example:

```http
POST /auth/login
```

Request:

```json
{
  "email": "test@example.com",
  "password": "StrongPassword123!"
}
```

A JWT access token is returned after successful authentication.

Protected requests include:

```http
Authorization: Bearer <access_token>
```

---

# 20. API Error Handling

The services return appropriate HTTP errors for invalid requests and application failures.

Examples include:

```text
400 Bad Request
401 Unauthorized
404 Not Found
409 Conflict
500 Internal Server Error
```

Input validation is performed using Pydantic schemas.

---

# 21. Database

The User Service uses **Neon PostgreSQL** for persistent user data.

The database connection string is supplied through:

```env
DATABASE_URL=<NEON_DATABASE_URL>
```

The database is not included in the repository.

---

# 22. Email Notification

The Notification Service uses SMTP to send welcome emails.

SMTP credentials are supplied through environment variables:

```env
SMTP_HOST=
SMTP_PORT=
SMTP_USERNAME=
SMTP_PASSWORD=
```

For Gmail, an **App Password** should be used instead of the normal account password when SMTP authentication requires it.

---

# 23. Git Security

The following files/directories should not be committed:

```text
.env
venv/
__pycache__/
*.pyc
jetstream/
```

The repository contains `.env.example` files instead of real credentials.

The NATS executable is also not included in the repository.

---

# 24. Demo

The demonstration video shows:

1. Starting NATS with JetStream.
2. Starting the User Service.
3. Starting the Notification Service.
4. Starting the API Gateway.
5. Registering a new user.
6. User persistence in Neon PostgreSQL.
7. `user.created` event being published.
8. Notification Service consuming the event.
9. Welcome email delivery.
10. JetStream message acknowledgement.
11. Failure and redelivery behavior.

**Demo Video:** `<ADD_DEMO_VIDEO_URL>`

---

# 25. Submission

**GitHub Repository:**

`[<ADD_GITHUB_REPOSITORY_URL>](https://github.com/sudharsan-051006/Trams)`

**Demo Video:**

`<ADD_DEMO_VIDEO_URL>`

---

# 26. Key Design Decisions

### Why NATS?

NATS provides lightweight, high-performance asynchronous messaging suitable for communication between microservices.

### Why JetStream?

JetStream provides persistence, durable consumers, acknowledgements, and message redelivery, making the notification workflow more reliable than simple fire-and-forget messaging.

### Why asynchronous communication?

The User Service should not be blocked by email delivery.

The user registration can complete immediately while the Notification Service processes the email asynchronously.

### Why an API Gateway?

The gateway provides a single entry point for clients and centralizes authentication and request routing while keeping internal services separated.

---

# 27. Summary

This project demonstrates:

* Microservices architecture
* API Gateway pattern
* Event-driven architecture
* NATS messaging
* NATS JetStream
* Asynchronous communication
* Durable consumers
* Manual acknowledgements
* Message redelivery
* JWT authentication
* Argon2 password hashing
* Environment-based configuration
* PostgreSQL persistence
* SMTP email notifications
* Input validation
* Error handling
* Secure inter-service communication
* Failure recovery
