import { useEffect, useMemo, useState } from 'react'
import { SiteMessage, SiteMessagePayload, trackingApi } from '../api/tracking'
import ErrorDisplay from '../components/ErrorDisplay'
import './SiteMessages.css'

type VariantDraft = {
  label: string
  headline: string
  body: string
  cta_text: string
  cta_url: string
}

const emptyForm: SiteMessagePayload = {
  name: '',
  message_type: 'modal',
  status: 'draft',
  targeting_rules: {},
  content: {},
  personalization_tokens: [],
  form_schema: {},
  frequency_cap: 1,
  active_from: '',
  active_until: '',
}

const defaultVariant: VariantDraft = {
  label: '',
  headline: '',
  body: '',
  cta_text: '',
  cta_url: '',
}

export const SiteMessages = () => {
  const [messages, setMessages] = useState<SiteMessage[]>([])
  const [form, setForm] = useState<SiteMessagePayload>({ ...emptyForm })
  const [editingId, setEditingId] = useState<number | null>(null)
  const [headline, setHeadline] = useState('')
  const [body, setBody] = useState('')
  const [ctaText, setCtaText] = useState('')
  const [ctaUrl, setCtaUrl] = useState('')
  const [segmentsInput, setSegmentsInput] = useState('')
  const [variants, setVariants] = useState<VariantDraft[]>([])
  const [previewVariant, setPreviewVariant] = useState('base')
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)
  const [actionError, setActionError] = useState<string | null>(null)

  const previewContent = useMemo(() => {
    if (previewVariant === 'base') {
      return { headline, body, cta_text: ctaText, cta_url: ctaUrl }
    }
    const match = variants.find((variant) => variant.label === previewVariant)
    if (match) {
      return match
    }
    return { headline, body, cta_text: ctaText, cta_url: ctaUrl }
  }, [previewVariant, variants, headline, body, ctaText, ctaUrl])

  const experiments = useMemo(
    () => variants.map((variant) => variant.label).filter(Boolean),
    [variants]
  )

  const loadMessages = async () => {
    setLoading(true)
    setLoadError(null)
    try {
      const data = await trackingApi.listSiteMessages()
      setMessages(data)
    } catch {
      setLoadError('Unable to load site messages. Confirm you have permissions and a firm selected.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadMessages()
  }, [])

  const resetForm = () => {
    setForm({ ...emptyForm })
    setEditingId(null)
    setHeadline('')
    setBody('')
    setCtaText('')
    setCtaUrl('')
    setSegmentsInput('')
    setVariants([])
    setPreviewVariant('base')
    setActionError(null)
  }

  const handleSelectMessage = (message: SiteMessage) => {
    setEditingId(message.id!)
    setForm({
      name: message.name,
      message_type: message.message_type,
      status: message.status,
      targeting_rules: message.targeting_rules || {},
      content: message.content || {},
      personalization_tokens: message.personalization_tokens || [],
      form_schema: message.form_schema || {},
      frequency_cap: message.frequency_cap,
      active_from: message.active_from || '',
      active_until: message.active_until || '',
    })
    const content = message.content || {}
    setHeadline((content.headline as string) || '')
    setBody((content.body as string) || '')
    setCtaText((content.cta_text as string) || '')
    setCtaUrl((content.cta_url as string) || '')
    const segmentList = (message.targeting_rules?.segments as string[]) || []
    setSegmentsInput(segmentList.join(', '))

    const variantEntries = Object.entries(
      (content.variants as Record<string, Partial<VariantDraft>>) || {}
    )
    setVariants(
      variantEntries.map(([label, value]) => ({
        label,
        headline: value.headline || '',
        body: value.body || '',
        cta_text: value.cta_text || '',
        cta_url: value.cta_url || '',
      }))
    )
    setPreviewVariant('base')
  }

  const handleVariantChange = (index: number, field: keyof VariantDraft, value: string) => {
    const updated = [...variants]
    updated[index] = { ...updated[index], [field]: value }
    setVariants(updated)
  }

  const normalizeDate = (value?: string | null) => {
    if (!value) return null
    return value
  }

  const buildPayload = (): SiteMessagePayload => {
    const segments = segmentsInput
      .split(',')
      .map((segment) => segment.trim())
      .filter(Boolean)

    const contentVariants = variants.reduce<Record<string, VariantDraft>>((acc, variant) => {
      if (variant.label) {
        acc[variant.label] = {
          headline: variant.headline,
          body: variant.body,
          cta_text: variant.cta_text,
          cta_url: variant.cta_url,
          label: variant.label,
        }
      }
      return acc
    }, {})

    return {
      ...form,
      targeting_rules: {
        ...(form.targeting_rules || {}),
        segments,
        experiments,
      },
      content: {
        headline,
        body,
        cta_text: ctaText,
        cta_url: ctaUrl,
        variants: contentVariants,
      },
      active_from: normalizeDate(form.active_from),
      active_until: normalizeDate(form.active_until),
    }
  }

  const handleSubmit = async () => {
    setSaving(true)
    setActionError(null)
    const payload = buildPayload()
    try {
      if (editingId) {
        await trackingApi.updateSiteMessage(editingId, payload)
      } else {
        await trackingApi.createSiteMessage(payload)
      }
      await loadMessages()
      resetForm()
    } catch {
      setActionError('Unable to save site message. Please verify required fields.')
    } finally {
      setSaving(false)
    }
  }

  const previewVariants = ['base', ...experiments]

  if (loadError) {
    return (
      <ErrorDisplay
        error={loadError}
        title="Failed to Load Site Messages"
        variant="card"
      />
    );
  }

  return (
    <div className="site-messages">
      {actionError && (
        <ErrorDisplay
          error={actionError}
          variant="banner"
          onDismiss={() => setActionError(null)}
        />
      )}
      <div className="page-header">
        <div>
          <h1>Site Messages</h1>
          <p className="text-muted">
            Build on-site messages with targeting, frequency caps, and A/B test variants. Draft messages stay private;
            published messages are evaluated via the tracking SDK.
          </p>
        </div>
        <button className="btn" onClick={resetForm}>
          New Message
        </button>
      </div>

      <div className="grid two-columns">
        <div className="card">
          <div className="card-header">
            <h3>{editingId ? 'Edit Site Message' : 'Create Site Message'}</h3>
            <p className="text-muted">Define targeting, content, and delivery rules.</p>
          </div>

          <div className="form-grid">
            <label>
              Name
              <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
            </label>
            <label>
              Message Type
              <select
                value={form.message_type}
                onChange={(e) =>
                  setForm({ ...form, message_type: e.target.value as SiteMessagePayload['message_type'] })
                }
              >
                <option value="modal">Modal</option>
                <option value="slide_in">Slide In</option>
                <option value="banner">Banner</option>
              </select>
            </label>
            <label>
              Status
              <select
                value={form.status}
                onChange={(e) => setForm({ ...form, status: e.target.value as SiteMessagePayload['status'] })}
              >
                <option value="draft">Draft</option>
                <option value="published">Published</option>
                <option value="archived">Archived</option>
              </select>
            </label>
            <label>
              Frequency Cap (per visitor per day)
              <input
                type="number"
                min={1}
                value={form.frequency_cap}
                onChange={(e) => setForm({ ...form, frequency_cap: Number(e.target.value) })}
              />
            </label>
            <label>
              Active From (ISO)
              <input
                placeholder="2026-01-06T00:00:00Z"
                value={form.active_from || ''}
                onChange={(e) => setForm({ ...form, active_from: e.target.value })}
              />
            </label>
            <label>
              Active Until (ISO)
              <input
                placeholder="2026-02-01T00:00:00Z"
                value={form.active_until || ''}
                onChange={(e) => setForm({ ...form, active_until: e.target.value })}
              />
            </label>
          </div>

          <div className="form-grid">
            <label>
              Segments (comma separated)
              <input
                placeholder="vip, returning, beta"
                value={segmentsInput}
                onChange={(e) => setSegmentsInput(e.target.value)}
              />
            </label>
            <label>
              Personalization Tokens (optional)
              <input
                placeholder="contact.first_name, firm.name"
                value={(form.personalization_tokens || []).join(', ')}
                onChange={(e) =>
                  setForm({
                    ...form,
                    personalization_tokens: e.target.value
                      .split(',')
                      .map((token) => token.trim())
                      .filter(Boolean),
                  })
                }
              />
            </label>
          </div>

          <div className="content-editor">
            <h4>Content</h4>
            <div className="form-grid">
              <label>
                Headline
                <input value={headline} onChange={(e) => setHeadline(e.target.value)} />
              </label>
              <label>
                Body
                <textarea value={body} onChange={(e) => setBody(e.target.value)} rows={3} />
              </label>
              <label>
                CTA Label
                <input value={ctaText} onChange={(e) => setCtaText(e.target.value)} />
              </label>
              <label>
                CTA URL
                <input value={ctaUrl} onChange={(e) => setCtaUrl(e.target.value)} />
              </label>
            </div>
          </div>

          <div className="content-editor">
            <div className="editor-header">
              <div>
                <h4>A/B Variants</h4>
                <p className="text-muted">Add variants to run experiments; delivery sticks per visitor.</p>
              </div>
              <button className="btn-secondary" onClick={() => setVariants([...variants, { ...defaultVariant }])}>
                + Add Variant
              </button>
            </div>
            {variants.length === 0 && <p className="text-muted">No variants configured.</p>}
            {variants.map((variant, index) => (
              <div key={index} className="variant-row">
                <input
                  placeholder="Variant label (e.g., control-b)"
                  value={variant.label}
                  onChange={(e) => handleVariantChange(index, 'label', e.target.value)}
                />
                <input
                  placeholder="Headline"
                  value={variant.headline}
                  onChange={(e) => handleVariantChange(index, 'headline', e.target.value)}
                />
                <input
                  placeholder="Body"
                  value={variant.body}
                  onChange={(e) => handleVariantChange(index, 'body', e.target.value)}
                />
                <input
                  placeholder="CTA text"
                  value={variant.cta_text}
                  onChange={(e) => handleVariantChange(index, 'cta_text', e.target.value)}
                />
                <input
                  placeholder="CTA URL"
                  value={variant.cta_url}
                  onChange={(e) => handleVariantChange(index, 'cta_url', e.target.value)}
                />
                <button
                  className="link-button"
                  onClick={() => setVariants(variants.filter((_, idx) => idx !== index))}
                >
                  Remove
                </button>
              </div>
            ))}
          </div>

          <div className="actions">
            <button className="btn-primary" onClick={handleSubmit} disabled={saving}>
              {saving ? 'Saving...' : editingId ? 'Update Message' : 'Create Message'}
            </button>
            {editingId && (
              <button className="btn-secondary" onClick={resetForm}>
                Cancel
              </button>
            )}
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <h3>Preview</h3>
            <p className="text-muted">Live rendering with selected variant.</p>
          </div>

          <div className="preview-controls">
            <label>
              Variant
              <select value={previewVariant} onChange={(e) => setPreviewVariant(e.target.value)}>
                {previewVariants.map((variantKey) => (
                  <option key={variantKey} value={variantKey}>
                    {variantKey === 'base' ? 'Base' : variantKey}
                  </option>
                ))}
              </select>
            </label>
          </div>

          <div className={`site-message-preview ${form.message_type}`}>
            <div className="preview-headline">{previewContent.headline || 'Headline'}</div>
            <div className="preview-body">{previewContent.body || 'Body copy for your site message.'}</div>
            <button className="btn-primary">{previewContent.cta_text || 'Call to Action'}</button>
            {previewContent.cta_url && (
              <div className="preview-link">
                Target URL: <span>{previewContent.cta_url}</span>
              </div>
            )}
          </div>

          <div className="meta">
            <p>
              <strong>Segments:</strong> {segmentsInput || 'None'}
            </p>
            <p>
              <strong>Experiments:</strong> {experiments.length ? experiments.join(', ') : 'Not configured'}
            </p>
          </div>
        </div>
      </div>

      <div className="card">
        <div className="card-header">
          <h3>Existing Messages</h3>
          <p className="text-muted">Select a message to edit targeting, variants, or copy.</p>
        </div>
        {loading ? (
          <div>Loading site messages...</div>
        ) : messages.length === 0 ? (
          <div className="text-muted">No site messages created yet.</div>
        ) : (
          <div className="table">
            <div className="table-head">
              <div>Name</div>
              <div>Type</div>
              <div>Status</div>
              <div>Active Window</div>
              <div>Experiments</div>
            </div>
            <div className="table-body">
              {messages.map((message) => (
                <div
                  key={message.id}
                  className="table-row clickable"
                  onClick={() => handleSelectMessage(message)}
                  role="button"
                >
                  <div>{message.name}</div>
                  <div>
                    <span className="badge badge-muted">{message.message_type}</span>
                  </div>
                  <div>
                    <span className={`badge ${message.status === 'published' ? 'badge-success' : 'badge-muted'}`}>
                      {message.status}
                    </span>
                  </div>
                  <div className="text-muted">
                    {message.active_from ? new Date(message.active_from).toLocaleDateString() : '—'} →{' '}
                    {message.active_until ? new Date(message.active_until).toLocaleDateString() : '—'}
                  </div>
                  <div className="text-muted">
                    {(message.targeting_rules?.experiments as string[])?.join(', ') || '—'}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default SiteMessages
