# IA message pipeline — README et architecture

> Source: `ai_message_codebase/README.md`

# AI MESSAGE PIPELINE

This is a small open-source project that connects WhatsApp messages to an AI response flow using Node.js, Ollama, Redis, and Prisma.

The project is intended to receive messages from the WhatsApp Business API, store the conversation history, generate a reply with a local language model, and send the answer back to the user.

## Why this project exists

This project is a small experimental backend for building AI-assisted WhatsApp interactions. It demonstrates how a webhook can receive messages, queue them for processing, call a local language model, and return a response automatically.

It is designed as a simple foundation for developers who want to experiment with WhatsApp automation, local AI inference, and event-driven backends.

## Overview

The application follows a simple asynchronous workflow:

1. A WhatsApp webhook receives an incoming message.
2. The message is pushed to a BullMQ queue managed by Redis.
3. A worker processes the job, stores the message in the database, and calls an AI model.
4. The AI response is saved and sent back to the user through the WhatsApp API.

## Main features

- WhatsApp webhook handling for inbound messages
- Message queue processing with BullMQ and Redis
- Conversation persistence through Prisma and MySQL/MariaDB
- AI response generation using Ollama
- WhatsApp message sending through the Meta Graph API
- Basic health check endpoint
- Tier-based system prompts for different user categories

## Architecture

The project uses a classic backend structure:

- Express for the HTTP server
- Prisma for database access and schema management
- BullMQ for background jobs
- Redis as the queue backend
- Ollama as the local model inference engine
- WhatsApp Cloud API for outbound messaging

The main flow is:

- Webhook controller: receives and validates incoming WhatsApp events
- Queue layer: decouples the webhook from the processing work
- Worker: performs the business logic and model calls
- Database: stores users, messages, prompts, and escalations

## Technologies used

- Node.js
- Express
- Prisma
- BullMQ
- Redis
- MySQL/MariaDB
- Ollama
- Axios
- dotenv
- Helmet
- CORS

## Prerequisites

Before running the project, make sure you have:

- Node.js v18 or newer
- npm installed
- A Redis instance running
- A MySQL or MariaDB database available
- Ollama installed and a model available locally

## Installation

Clone the repository:

```bash
git clone <repository-url>
cd ai-message-pipeline
```

Install dependencies:

```bash
npm install
```

Generate the Prisma client:

```bash
npx prisma generate
```

Apply database migrations:

```bash
npx prisma migrate deploy
```

## Configuration

Create a `.env` file at the project root with the required environment variables.

Example variables:

```env
DATABASE_URL=mysql://user:password@localhost:3306/database_name
REDIS_HOST=127.0.0.1
REDIS_PORT=6379
WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id
WHATSAPP_TOKEN=your_whatsapp_token
WHATSAPP_VERIFY_TOKEN=your_webhook_verify_token
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:latest
```

Additional configuration may be required depending on the deployment environment.

## Architecture flow

```text
[WhatsApp] -> [Webhook Controller] -> [Redis Queue] -> [Worker] -> [Ollama] -> [WhatsApp API]
```

## System prompts

The project supports tier-based system prompts. These prompts define the behavior of the AI depending on the user's category.

You can configure them in the database through the `SystemPrompt` model in Prisma. This is useful if you want different tones, instructions, or safety rules for different user groups.

## Running the application

Start the server:

```bash
npm start
```

For development mode:

```bash
npm run dev
```

The server exposes a basic health endpoint at:

```text
/health
```

## Project structure

```text
ai-message-pipeline/
├── src/                          # Application source code
│   ├── app.js                    # Express application setup
│   ├── server.js                 # Server entry point
│   ├── config/                   # Configuration files for queues, database, and environment
│   ├── controllers/              # HTTP controllers and route handlers
│   │   └── whatsapp/             # WhatsApp webhook controller and routes
│   ├── middlewares/              # Request validation and security middleware
│   ├── services/                 # Business logic and external API integrations
│   │   ├── ollama.service.js     # AI model calls through Ollama
│   │   ├── whatsapp.service.js   # WhatsApp API messaging helper
│   │   └── notify.service.js     # Notify integration helper
│   ├── workers/                  # Background job workers
│   │   └── whatsapp.worker.js    # Queue consumer for WhatsApp processing
│   ├── views/                    # Template views for the web layer
│   └── public/                   # Static assets such as CSS and JavaScript
├── prisma/                        # Prisma schema and migrations
│   ├── schema.prisma             # Database models and relations
│   └── migrations/               # Database migration history
├── storage/                       # Local storage for uploaded or generated files
├── logs/                          # Runtime logs
├── .env                           # Environment variables (not committed)
├── package.json                   # Project dependencies and scripts
└── README.md                      # Project documentation
```

## Contributing

Contributions are welcome. If you want to improve the project, you can:

1. Fork the repository.
2. Create a feature branch.
3. Make your changes.
4. Submit a pull request with a clear explanation of the improvement.

## Notes

This repository is a lightweight prototype and a learning-oriented project. It works as a basic backend foundation for WhatsApp-based AI interactions, but it is not yet a fully production-ready platform.

- The project uses queue-based processing, but monitoring and production hardening are still minimal.
- The current implementation focuses mainly on the backend webhook and AI processing flow.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

