# IA message pipeline — package.json

> Source: `ai_message_codebase/package.json`

```json
{
  "name": "ai-message-pipeline",
  "version": "1.0.0",
  "description": "WhatsApp AI messaging pipeline with Ollama, Redis, and Prisma",
  "license": "MIT",
  "author": "Nicoletta Moumbounou",
  "type": "commonjs",
  "main": "src/server.js",
  "scripts": {
    "start": "node src/server.js",
    "dev": "nodemon src/server.js",
    "test": "node --test"
  },
  "dependencies": {
    "@prisma/adapter-mariadb": "^7.8.0",
    "@prisma/client": "^7.8.0",
    "axios": "^1.17.0",
    "bullmq": "^5.78.0",
    "cors": "^2.8.6",
    "dotenv": "^17.4.2",
    "express": "^5.2.1",
    "helmet": "^8.2.0",
    "nodemon": "^3.1.14",
    "prisma": "^7.8.0",
    "winston": "^3.19.0"
  }
}

```
