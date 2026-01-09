import crypto from 'crypto'
import { expect, test, type APIRequestContext, type Page } from '@playwright/test'

const API_BASE_URL = process.env.E2E_API_URL ?? 'http://localhost:8000/api'
const PASSWORD = 'SecurePass123!'

type E2EUser = {
  username: string
  email: string
  first_name: string
  last_name: string
  password: string
  password2: string
}

const buildUser = (): E2EUser => {
  const suffix = crypto.randomUUID().slice(0, 8)
  return {
    username: `e2e_user_${suffix}`,
    email: `e2e_${suffix}@example.com`,
    first_name: 'E2E',
    last_name: 'Tester',
    password: PASSWORD,
    password2: PASSWORD,
  }
}

const registerUser = async (request: APIRequestContext, user: E2EUser) => {
  const response = await request.post(`${API_BASE_URL}/auth/register/`, { data: user })
  expect(response.ok()).toBeTruthy()
}

const loginThroughUI = async (page: Page, user: E2EUser) => {
  await page.goto('/login')
  await page.getByLabel('Username').fill(user.username)
  await page.getByLabel('Password').fill(user.password)
  await page.getByRole('button', { name: 'Sign In' }).click()
  await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible({ timeout: 15_000 })
}

const decodeBase32 = (input: string) => {
  const alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ234567'
  const cleaned = input.toUpperCase().replace(/=+$/, '')
  let bits = ''
  for (const char of cleaned) {
    const index = alphabet.indexOf(char)
    if (index === -1) {
      throw new Error(`Invalid base32 character: ${char}`)
    }
    bits += index.toString(2).padStart(5, '0')
  }
  const bytes = bits.match(/.{1,8}/g) ?? []
  return Buffer.from(bytes.map((byte) => parseInt(byte.padEnd(8, '0'), 2)))
}

const decodeSecret = (secret: string) => {
  const trimmed = secret.trim()
  if (/^[0-9a-f]+$/i.test(trimmed)) {
    return Buffer.from(trimmed, 'hex')
  }
  return decodeBase32(trimmed)
}

const generateTotp = (secret: string) => {
  const key = decodeSecret(secret)
  const step = 30
  const counter = Math.floor(Date.now() / 1000 / step)
  const counterBuffer = Buffer.alloc(8)
  counterBuffer.writeBigInt64BE(BigInt(counter))

  const hmac = crypto.createHmac('sha1', key).update(counterBuffer).digest()
  const offset = hmac[hmac.length - 1] & 0x0f
  const code = (hmac.readUInt32BE(offset) & 0x7fffffff) % 1_000_000

  return code.toString().padStart(6, '0')
}

test('registers a new account', async ({ page }) => {
  const user = buildUser()

  await page.goto('/register')
  await page.getByLabel('First Name').fill(user.first_name)
  await page.getByLabel('Last Name').fill(user.last_name)
  await page.getByLabel('Username').fill(user.username)
  await page.getByLabel('Email').fill(user.email)
  await page.getByLabel('Password').fill(user.password)
  await page.getByLabel('Confirm Password').fill(user.password2)
  await page.getByRole('button', { name: 'Sign Up' }).click()

  await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible({ timeout: 15_000 })
})

test('logs in with valid credentials', async ({ page }) => {
  const user = buildUser()
  await registerUser(page.request, user)

  await loginThroughUI(page, user)
})

test('enrolls and verifies TOTP MFA', async ({ page }) => {
  const user = buildUser()
  await registerUser(page.request, user)

  await loginThroughUI(page, user)

  const enrollResponse = await page.request.post(`${API_BASE_URL}/auth/mfa/enroll/totp/`)
  expect(enrollResponse.ok()).toBeTruthy()
  const enrollData = await enrollResponse.json()

  const totpCode = generateTotp(enrollData.secret)
  const verifyResponse = await page.request.post(`${API_BASE_URL}/auth/mfa/verify/totp/`, {
    data: {
      device_id: enrollData.device_id,
      code: totpCode,
    },
  })
  expect(verifyResponse.ok()).toBeTruthy()

  const statusResponse = await page.request.get(`${API_BASE_URL}/auth/mfa/status/`)
  expect(statusResponse.ok()).toBeTruthy()
  const statusData = await statusResponse.json()
  expect(statusData.totp_enabled).toBeTruthy()
})

test('initiates OAuth connection from calendar settings', async ({ page }) => {
  const user = buildUser()
  await registerUser(page.request, user)
  await loginThroughUI(page, user)

  await page.route('**/calendar/oauth-connections/', async (route) => {
    if (route.request().method() === 'GET') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([]),
      })
      return
    }
    await route.continue()
  })

  await page.route('**/calendar/oauth-connections/initiate_google_oauth/', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        authorization_url: '/calendar/oauth/callback?code=mock-code&state=mock-state',
        state: 'mock-state',
        provider: 'google',
      }),
    })
  })

  await page.route('**/calendar/oauth-connections/oauth_callback/', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ message: 'Calendar connected successfully!' }),
    })
  })

  await page.goto('/calendar-sync')
  await expect(page.getByRole('heading', { name: 'Calendar Sync Settings' })).toBeVisible()

  await page.getByRole('button', { name: 'Connect Google Calendar' }).click()

  await expect(page.getByRole('heading', { name: 'Success!' })).toBeVisible({ timeout: 10_000 })
})
