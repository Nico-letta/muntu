# IA message pipeline E2E Test Specifications

## `app.test.js`

```javascript
const test = require('node:test');
const assert = require('node:assert/strict');
const { once } = require('node:events');

const app = require('../src/app');

async function withServer(fn) {
  const server = app.listen(0);
  await once(server, 'listening');

  const address = server.address();
  const port = typeof address === 'object' && address ? address.port : 0;

  try {
    await fn(port);
  } finally {
    await new Promise((resolve, reject) => {
      server.close((err) => (err ? reject(err) : resolve()));
    });
  }
}

test('GET /health returns a healthy response', async () => {
  await withServer(async (port) => {
    const response = await fetch(`http://127.0.0.1:${port}/health`);
    assert.equal(response.status, 200);

    const body = await response.json();
    assert.equal(body.status, 'UP');
  });
});

test('GET webhook verification accepts the configured token', async () => {
  process.env.WHATSAPP_VERIFY_TOKEN = 'test-webhook-token';

  await withServer(async (port) => {
    const url = new URL(`http://127.0.0.1:${port}/api/v1/webhook/whatsapp`);
    url.searchParams.set('hub.mode', 'subscribe');
    url.searchParams.set('hub.verify_token', 'test-webhook-token');
    url.searchParams.set('hub.challenge', 'challenge-123');

    const response = await fetch(url);
    assert.equal(response.status, 200);
    assert.equal(await response.text(), 'challenge-123');
  });
});

```

