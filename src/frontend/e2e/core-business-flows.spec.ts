import crypto from 'crypto'
import { expect, test, type APIRequestContext } from '@playwright/test'

const API_BASE_URL = process.env.E2E_API_URL ?? 'http://localhost:8000/api/v1'
const E2E_SEED_HEADER = process.env.E2E_SEED_HEADER ?? 'X-E2E-Seed'
const E2E_SEED_VALUE = process.env.E2E_SEED_VALUE ?? 'local-e2e-token'
const PASSWORD = 'SecurePass123!'

const formatDate = (date: Date) => date.toISOString().slice(0, 10)

const buildProvisionPayload = () => {
  const suffix = crypto.randomUUID().slice(0, 8)
  return {
    firm_name: `E2E Firm ${suffix}`,
    firm_slug: `e2e-firm-${suffix}`,
    admin_email: `e2e_admin_${suffix}@example.com`,
    admin_password: PASSWORD,
    admin_first_name: 'E2E',
    admin_last_name: 'Admin',
    timezone: 'America/Los_Angeles',
    currency: 'USD',
    subscription_tier: 'professional',
}

const provisionFirm = async (request: APIRequestContext) => {
  const payload = buildProvisionPayload()
  const response = await request.post(`${API_BASE_URL}/auth/provision-firm/`, {
    data: payload,
    headers: {
      [E2E_SEED_HEADER]: E2E_SEED_VALUE,
    },
  })

  expect(response.ok()).toBeTruthy()
  const data = await response.json()
  return {
    ...payload,
    ...data,
  }
}

test('provisions a firm and completes client-to-payment workflow', async ({ page, request }) => {
  const seed = await provisionFirm(request)

  await page.goto('/login')
  await page.getByLabel('Username').fill(seed.admin_username)
  await page.getByLabel('Password').fill(seed.admin_password)
  await page.getByRole('button', { name: 'Sign In' }).click()
  await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible({ timeout: 15_000 })

  const companyName = `E2E Client ${crypto.randomUUID().slice(0, 6)}`
  await page.goto('/clients')
  await expect(page.getByRole('heading', { name: 'Clients' })).toBeVisible()
  await page.getByRole('button', { name: '+ Add Client' }).click()
  await page.getByLabel('Company Name *').fill(companyName)
  await page.getByLabel('Industry').fill('Technology')
  await page.getByLabel('Primary Contact Name *').fill('E2E Contact')
  await page.getByLabel('Primary Contact Email *').fill('e2e.contact@example.com')
  await page.getByRole('button', { name: 'Create Client' }).click()
  await expect(page.getByText(companyName)).toBeVisible()

  const clientsResponse = await page.request.get(
    `${API_BASE_URL}/clients/clients/?search=${encodeURIComponent(companyName)}`
  )
  expect(clientsResponse.ok()).toBeTruthy()
  const clientsData = await clientsResponse.json()
  const clients = clientsData.results ?? clientsData
  const client = clients.find((item: { id: number; company_name: string }) => item.company_name === companyName)
  expect(client).toBeTruthy()

  const today = new Date()
  const dueDate = new Date()
  dueDate.setDate(dueDate.getDate() + 30)

  const invoicePayload = {
    client: client.id,
    invoice_number: `INV-${crypto.randomUUID().slice(0, 8)}`,
    subtotal: '1250.00',
    tax_amount: '0.00',
    total_amount: '1250.00',
    issue_date: formatDate(today),
    due_date: formatDate(dueDate),
    currency: 'USD',
    status: 'sent',
    line_items: [
      {
        description: 'E2E services',
        quantity: 1,
        rate: '1250.00',
        amount: '1250.00',
      },
    ],

  const invoiceResponse = await page.request.post(`${API_BASE_URL}/finance/invoices/`, {
    data: invoicePayload,
  })
  expect(invoiceResponse.ok()).toBeTruthy()
  const invoice = await invoiceResponse.json()

  const paymentPayload = {
    client: client.id,
    payment_number: `PAY-${crypto.randomUUID().slice(0, 8)}`,
    payment_date: formatDate(today),
    amount: invoice.total_amount,
    currency: 'USD',
    payment_method: 'bank_transfer',
    status: 'cleared',
    cleared_date: formatDate(today),
  }

  const paymentResponse = await page.request.post(`${API_BASE_URL}/finance/payments/`, {
    data: paymentPayload,
  })
  expect(paymentResponse.ok()).toBeTruthy()
  const payment = await paymentResponse.json()

  const allocationResponse = await page.request.post(
    `${API_BASE_URL}/finance/payments/${payment.id}/allocate/`,
    {
      data: {
        invoice_id: invoice.id,
        amount: invoice.total_amount,
        notes: 'E2E full payment',
      },
    }
  )
  expect(allocationResponse.ok()).toBeTruthy()

  const refreshedInvoiceResponse = await page.request.get(`${API_BASE_URL}/finance/invoices/${invoice.id}/`)
  expect(refreshedInvoiceResponse.ok()).toBeTruthy()
  const refreshedInvoice = await refreshedInvoiceResponse.json()
  expect(refreshedInvoice.status).toBe('paid')
})
