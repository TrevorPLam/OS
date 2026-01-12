import crypto from 'crypto'
import { expect, test, type Page } from '@playwright/test'

type E2EUser = {
  id: number
  username: string
  email: string
  first_name: string
  last_name: string
  date_joined: string
}

type E2EClient = {
  id: number
  company_name: string
  industry?: string
  status: string
  primary_contact_name: string
  primary_contact_email: string
  primary_contact_phone?: string
  country: string
  portal_enabled: boolean
  assigned_team: number[]
  client_since: string
  total_lifetime_value: string
  active_projects_count: number
  created_at: string
  updated_at: string
}

const buildUser = (overrides: Partial<E2EUser> = {}): E2EUser => {
  const suffix = crypto.randomUUID().slice(0, 8)
  return {
    id: 1,
    username: `e2e_${suffix}`,
    email: `e2e_${suffix}@example.com`,
    first_name: 'E2E',
    last_name: 'Tester',
    date_joined: new Date().toISOString(),
    ...overrides,
  }
}

const setupAuthRoutes = async (page: Page, initialUser: E2EUser | null = null) => {
  let currentUser: E2EUser | null = initialUser

  await page.route(/\/auth\/profile\/?(\?.*)?$/, async (route) => {
    if (!currentUser) {
      await route.fulfill({ status: 401, contentType: 'application/json', body: JSON.stringify({}) })
      return
    }

    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(currentUser),
    })
  })

  await page.route(/\/auth\/register\/?(\?.*)?$/, async (route) => {
    const payload = route.request().postDataJSON() as {
      username: string
      email: string
      first_name: string
      last_name: string
    }

    currentUser = buildUser({
      username: payload.username,
      email: payload.email,
      first_name: payload.first_name,
      last_name: payload.last_name,
    })

    await route.fulfill({
      status: 201,
      contentType: 'application/json',
      body: JSON.stringify({ user: currentUser, message: 'User created successfully' }),
    })
  })

  await page.route(/\/auth\/login\/?(\?.*)?$/, async (route) => {
    const payload = route.request().postDataJSON() as { username: string }
    currentUser = buildUser({ username: payload.username })
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ user: currentUser, message: 'Login successful' }),
    })
  })

  await page.route(/\/auth\/logout\/?(\?.*)?$/, async (route) => {
    currentUser = null
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ message: 'Logout successful' }),
    })
  })
}

const setupClientRoutes = async (page: Page) => {
  let clients: E2EClient[] = []

  await page.route(/\/clients\/clients\/?(\?.*)?$/, async (route) => {
    const method = route.request().method()

    if (method === 'GET') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ results: clients }),
      })
      return
    }

    if (method === 'POST') {
      const payload = route.request().postDataJSON() as Partial<E2EClient>
      const timestamp = new Date().toISOString()
      const newClient: E2EClient = {
        id: clients.length + 1,
        company_name: payload.company_name ?? 'New Client',
        industry: payload.industry ?? '',
        status: payload.status ?? 'active',
        primary_contact_name: payload.primary_contact_name ?? 'Primary Contact',
        primary_contact_email: payload.primary_contact_email ?? 'primary@example.com',
        primary_contact_phone: payload.primary_contact_phone ?? '',
        country: payload.country ?? 'USA',
        portal_enabled: payload.portal_enabled ?? false,
        assigned_team: payload.assigned_team ?? [],
        client_since: payload.client_since ?? timestamp,
        total_lifetime_value: payload.total_lifetime_value ?? '0.00',
        active_projects_count: payload.active_projects_count ?? 0,
        created_at: timestamp,
        updated_at: timestamp,
      }

      clients = [newClient, ...clients]
      await route.fulfill({
        status: 201,
        contentType: 'application/json',
        body: JSON.stringify(newClient),
      })
      return
    }

    await route.fulfill({ status: 405 })
  })
}

const setupPortalRoutes = async (page: Page) => {
  const now = new Date()
  const invoice = {
    id: 101,
    invoice_number: 'INV-2026-001',
    project_name: 'Retainer Project',
    project_code: 'RET-01',
    status: 'sent',
    issue_date: now.toISOString(),
    due_date: new Date(now.getTime() + 7 * 24 * 60 * 60 * 1000).toISOString(),
    paid_date: null,
    subtotal: '1500.00',
    tax_amount: '0.00',
    total_amount: '1500.00',
    amount_paid: '0.00',
    balance_due: '1500.00',
    currency: 'USD',
    line_items: [
      {
        description: 'Consulting Retainer',
        quantity: 1,
        rate: '1500.00',
        amount: '1500.00',
      },
    ],
    is_overdue: false,
    days_until_due: 7,
    can_pay_online: true,
    created_at: now.toISOString(),
  }

  const summary = {
    total_invoices: 1,
    total_billed: 1500,
    total_paid: 0,
    total_outstanding: 1500,
    overdue_count: 0,
    by_status: {
      sent: {
        count: 1,
        total: 1500,
      },
    },
  }

  const thread = {
    id: 33,
    client: 1,
    client_name: 'Acme Corp',
    date: now.toISOString(),
    is_active: true,
    archived_at: null,
    message_count: 0,
    last_message_at: null,
    last_message_by: null,
    last_message_by_name: null,
    created_at: now.toISOString(),
    updated_at: now.toISOString(),
    messages: [],
    recent_messages: [],
  }

  const emptyResults = { results: [] }

  await page.route(/\/clients\/projects\/?(\?.*)?$/, async (route) => {
    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(emptyResults) })
  })

  await page.route(/\/documents\/documents\/?(\?.*)?$/, async (route) => {
    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ results: [] }) })
  })

  await page.route(/\/clients\/invoices\/summary\/?$/, async (route) => {
    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(summary) })
  })

  await page.route(/\/clients\/invoices\/?(\?.*)?$/, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ results: [invoice] }),
    })
  })

  await page.route(/\/clients\/proposals\/?(\?.*)?$/, async (route) => {
    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(emptyResults) })
  })

  await page.route(/\/clients\/contracts\/?(\?.*)?$/, async (route) => {
    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(emptyResults) })
  })

  await page.route(/\/clients\/engagement-history\/?(\?.*)?$/, async (route) => {
    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(emptyResults) })
  })

  await page.route(/\/clients\/chat-threads\/active\/?$/, async (route) => {
    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(thread) })
  })

  let paymentLinkRequested = false
  await page.route(/\/clients\/invoices\/\d+\/generate_payment_link\/?$/, async (route) => {
    paymentLinkRequested = true
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        status: 'ready',
        payment_url: 'https://example.com/payments/inv-2026-001',
        invoice_number: invoice.invoice_number,
        amount_due: invoice.balance_due,
        currency: invoice.currency,
        message: 'Payment link generated',
      }),
    })
  })

  return {
    invoice,
    wasPaymentLinkRequested: () => paymentLinkRequested,
  }
}

test('registers a firm admin and creates a client record', async ({ page }) => {
  await setupAuthRoutes(page)
  await setupClientRoutes(page)

  await page.goto('/register')

  const uniqueSuffix = crypto.randomUUID().slice(0, 6)
  await page.getByLabel('First Name').fill('Firm')
  await page.getByLabel('Last Name').fill('Owner')
  await page.getByLabel('Username').fill(`firm_owner_${uniqueSuffix}`)
  await page.getByLabel('Email').fill(`firm_owner_${uniqueSuffix}@example.com`)
  await page.getByLabel('Password').fill('SecurePass123!')
  await page.getByLabel('Confirm Password').fill('SecurePass123!')
  await page.getByRole('button', { name: 'Sign Up' }).click()

  await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible()

  const clientName = `Acme Co ${uniqueSuffix}`

  await page.goto('/clients')
  await page.getByRole('button', { name: '+ Add Client' }).click()
  await page.getByLabel(/Company Name/).fill(clientName)
  await page.getByLabel(/Primary Contact Name/).fill('Ada Lovelace')
  await page.getByLabel(/Email/).fill('ada@example.com')
  await page.getByRole('button', { name: 'Create Client' }).click()

  await expect(page.getByRole('heading', { name: clientName })).toBeVisible()
})

test('creates an invoice and initiates payment from the client portal', async ({ page }) => {
  const user = buildUser({ username: 'portal_user' })
  await setupAuthRoutes(page, user)
  const portalMocks = await setupPortalRoutes(page)

  await page.goto('/client-portal')
  await expect(page.getByRole('heading', { name: 'Client Portal' })).toBeVisible()

  await page.getByRole('button', { name: '💰 Invoices' }).click()

  await page.getByText(portalMocks.invoice.invoice_number).click()

  const payButton = page.getByRole('button', { name: '💳 Pay Now' })
  await expect(payButton).toBeVisible()

  const [popup] = await Promise.all([
    page.waitForEvent('popup'),
    payButton.click(),
  ])

  await popup.waitForLoadState()
  await popup.close()

  expect(portalMocks.wasPaymentLinkRequested()).toBeTruthy()
})
