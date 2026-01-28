import React, { useEffect, useMemo, useState } from 'react'
import {
  Deal,
  useCreateDeal,
  useDeals,
  useDeleteDeal,
  useMarkDealLost,
  useMarkDealWon,
  useMoveDealToStage,
  usePipelineStages,
  usePipelines,
  useUpdateDeal,
} from '../../api/crm'
import { useConfirmDialog } from '../../components/ConfirmDialog'
import ErrorDisplay from '../../components/ErrorDisplay'
import './CRM.css'

const PipelineKanban: React.FC = () => {
  const [selectedPipeline, setSelectedPipeline] = useState<number | null>(null)
  const { data: pipelines = [], isLoading: pipelinesLoading, error: pipelinesError } = usePipelines()
  const { data: stages = [], error: stagesError } = usePipelineStages(selectedPipeline ?? undefined)
  const {
    data: deals = [],
    isLoading: dealsLoading,
    error: dealsError,
  } = useDeals(selectedPipeline ? { pipeline: selectedPipeline } : undefined)
  const createDealMutation = useCreateDeal()
  const updateDealMutation = useUpdateDeal()
  const deleteDealMutation = useDeleteDeal()
  const moveDealMutation = useMoveDealToStage()
  const markDealWonMutation = useMarkDealWon()
  const markDealLostMutation = useMarkDealLost()
  const [showDealModal, setShowDealModal] = useState(false)
  const [editingDeal, setEditingDeal] = useState<Deal | null>(null)
  const [draggedDeal, setDraggedDeal] = useState<Deal | null>(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [actionError, setActionError] = useState<string | null>(null)
  const [dealToDelete, setDealToDelete] = useState<number | null>(null)

  // Confirm dialog for delete
  const deleteDialog = useConfirmDialog({
    title: 'Delete Deal',
    message: 'Are you sure you want to delete this deal? This action cannot be undone.',
    variant: 'danger',
    confirmText: 'Delete',
    onConfirm: async () => {
      if (dealToDelete === null) return
      try {
        await deleteDealMutation.mutateAsync(dealToDelete)
        setActionError(null)
      } catch {
        setActionError('Unable to delete the deal. Please try again.')
      } finally {
        setDealToDelete(null)
      }
    },
  })

  const [formData, setFormData] = useState<Partial<Deal>>({
    name: '',
    description: '',
    value: '0',
    expected_close_date: '',
    owner: undefined,
    account: undefined,
  })

  useEffect(() => {
    if (!selectedPipeline && pipelines.length > 0) {
      const defaultPipeline = pipelines.find((pipeline) => pipeline.is_default) || pipelines[0]
      if (defaultPipeline) {
        setSelectedPipeline(defaultPipeline.id)
      }
    }
  }, [pipelines, selectedPipeline])

  const sortedStages = useMemo(
    () => [...stages].sort((a, b) => a.display_order - b.display_order),
    [stages],
  )

  const getDealsByStage = (stageId: number) => {
    return deals
      .filter((deal) => deal.stage === stageId)
      .filter(
        (deal) =>
          searchTerm === '' ||
          deal.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
          (deal.account_name && deal.account_name.toLowerCase().includes(searchTerm.toLowerCase())),
      )
      .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
  }

  const handleDragStart = (e: React.DragEvent, deal: Deal) => {
    setDraggedDeal(deal)
    e.dataTransfer.effectAllowed = 'move'
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    e.dataTransfer.dropEffect = 'move'
  }

  const handleDrop = async (e: React.DragEvent, targetStageId: number) => {
    e.preventDefault()
    if (!draggedDeal) return

    if (draggedDeal.stage === targetStageId) {
      setDraggedDeal(null)
      return
    }

    try {
      await moveDealMutation.mutateAsync({ id: draggedDeal.id, stageId: targetStageId })
    } catch {
      setActionError('Unable to move the deal. Please try again.')
    } finally {
      setDraggedDeal(null)
    }
  }

  const handleCreateDeal = () => {
    setEditingDeal(null)
    setFormData({
      name: '',
      description: '',
      value: '0',
      expected_close_date: '',
      owner: undefined,
      account: undefined,
      pipeline: selectedPipeline || undefined,
      stage: sortedStages[0]?.id,
    })
    setActionError(null)
    setShowDealModal(true)
  }

  const handleEditDeal = (deal: Deal) => {
    setEditingDeal(deal)
    setFormData({
      name: deal.name,
      description: deal.description,
      value: deal.value,
      expected_close_date: deal.expected_close_date,
      owner: deal.owner,
      account: deal.account,
      pipeline: deal.pipeline,
      stage: deal.stage,
    })
    setActionError(null)
    setShowDealModal(true)
  }

  const handleSaveDeal = async () => {
    try {
      if (editingDeal) {
        await updateDealMutation.mutateAsync({ id: editingDeal.id, data: formData })
      } else {
        await createDealMutation.mutateAsync(formData)
      }
      setShowDealModal(false)
      setActionError(null)
    } catch {
      setActionError('Unable to save the deal. Please try again.')
    }
  }

  const handleDeleteDeal = (dealId: number) => {
    setDealToDelete(dealId)
    deleteDialog.show()
  }

  const handleMarkWon = async (dealId: number) => {
    try {
      await markDealWonMutation.mutateAsync(dealId)
      setActionError(null)
    } catch {
      setActionError('Unable to mark the deal as won. Please try again.')
    }
  }

  const handleMarkLost = async (dealId: number) => {
    const reason = window.prompt('Please provide a reason for losing this deal:')
    if (reason === null) return

    try {
      await markDealLostMutation.mutateAsync({ id: dealId, reason })
      setActionError(null)
    } catch {
      setActionError('Unable to mark the deal as lost. Please try again.')
    }
  }

  const formatCurrency = (value: string) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(parseFloat(value))
  }

  const getTotalPipelineValue = () => {
    return deals
      .filter((deal) => deal.is_active)
      .reduce((sum, deal) => sum + parseFloat(deal.value), 0)
  }

  const getTotalWeightedValue = () => {
    return deals
      .filter((deal) => deal.is_active)
      .reduce((sum, deal) => sum + parseFloat(deal.weighted_value), 0)
  }

  if (pipelinesLoading && !selectedPipeline) {
    return <div className="loading-spinner">Loading pipelines...</div>
  }

  if (pipelinesError) {
    return (
      <ErrorDisplay
        error={pipelinesError}
        title="Failed to Load Pipelines"
        variant="card"
      />
    )
  }

  return (
    <div className="crm-page pipeline-kanban">
      {(stagesError || dealsError || actionError) && (
        <ErrorDisplay
          error={
            actionError ||
            stagesError ||
            dealsError ||
            'Something went wrong. Please try again.'
          }
          variant="banner"
          onDismiss={() => setActionError(null)}
        />
      )}
      <div className="page-header">
        <div className="header-left">
          <h1>Pipeline</h1>
          <div className="pipeline-selector">
            <select
              value={selectedPipeline || ''}
              onChange={(e) => setSelectedPipeline(parseInt(e.target.value))}
              className="pipeline-select"
            >
              {pipelines.map((pipeline) => (
                <option key={pipeline.id} value={pipeline.id}>
                  {pipeline.name} {pipeline.is_default && '(Default)'}
                </option>
              ))}
            </select>
          </div>
        </div>
        <div className="header-right">
          <div className="pipeline-metrics">
            <div className="metric">
              <span className="metric-label">Total Value:</span>
              <span className="metric-value">{formatCurrency(getTotalPipelineValue().toString())}</span>
            </div>
            <div className="metric">
              <span className="metric-label">Weighted Value:</span>
              <span className="metric-value">{formatCurrency(getTotalWeightedValue().toString())}</span>
            </div>
            <div className="metric">
              <span className="metric-label">Active Deals:</span>
              <span className="metric-value">{deals.filter((deal) => deal.is_active).length}</span>
            </div>
          </div>
        </div>
      </div>

      <div className="pipeline-filters">
        <input
          type="text"
          placeholder="Search deals..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="search-input"
        />
        <button onClick={handleCreateDeal} className="btn-primary">
          + New Deal
        </button>
      </div>

      <div className="pipeline-stages">
        {dealsLoading ? <div className="loading">Loading deals...</div> : null}
        {sortedStages.map((stage) => (
          <div
            key={stage.id}
            className="pipeline-stage"
            onDragOver={handleDragOver}
            onDrop={(e) => handleDrop(e, stage.id)}
          >
            <div className="stage-header">
              <h3>{stage.name}</h3>
              <span className="stage-count">{getDealsByStage(stage.id).length}</span>
            </div>
            <div className="stage-probability">{stage.probability}% probability</div>

            <div className="deals-container">
              {getDealsByStage(stage.id).map((deal) => (
                <div
                  key={deal.id}
                  className={`deal-card ${deal.is_won ? 'won' : deal.is_lost ? 'lost' : ''}`}
                  draggable
                  onDragStart={(e) => handleDragStart(e, deal)}
                >
                  <div className="deal-header">
                    <h4>{deal.name}</h4>
                    <span className="deal-value">{formatCurrency(deal.value)}</span>
                  </div>

                  <div className="deal-details">
                    {deal.account_name && (
                      <div className="deal-account">
                        <span className="icon">🏢</span>
                        <span>{deal.account_name}</span>
                      </div>
                    )}
                    {deal.expected_close_date && (
                      <div className="deal-date">
                        <span className="icon">📅</span>
                        <span>{new Date(deal.expected_close_date).toLocaleDateString()}</span>
                      </div>
                    )}
                    {deal.owner_name && (
                      <div className="deal-owner">
                        <span className="icon">👤</span>
                        <span>{deal.owner_name}</span>
                      </div>
                    )}
                  </div>

                  <div className="deal-actions">
                    {!deal.is_won && !deal.is_lost && (
                      <>
                        <button onClick={() => handleMarkWon(deal.id)} className="btn-small btn-success">
                          Won
                        </button>
                        <button onClick={() => handleMarkLost(deal.id)} className="btn-small btn-danger">
                          Lost
                        </button>
                      </>
                    )}
                    <button onClick={() => handleEditDeal(deal)} className="btn-small">
                      Edit
                    </button>
                    <button onClick={() => handleDeleteDeal(deal.id)} className="btn-small btn-danger">
                      Delete
                    </button>
                  </div>
                </div>
              ))}

              {getDealsByStage(stage.id).length === 0 && (
                <div className="empty-stage">No deals</div>
              )}
            </div>
          </div>
        ))}
      </div>

      {showDealModal && (
        <div className="modal-overlay" onClick={() => setShowDealModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h2>{editingDeal ? 'Edit Deal' : 'New Deal'}</h2>
            <form
              onSubmit={(e) => {
                e.preventDefault()
                void handleSaveDeal()
              }}
              className="crm-form"
            >
              <div className="form-group">
                <label>Deal Name *</label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  required
                />
              </div>

              <div className="form-group">
                <label>Description</label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  rows={3}
                />
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>Value *</label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    value={formData.value}
                    onChange={(e) => setFormData({ ...formData, value: e.target.value })}
                    required
                  />
                </div>
                <div className="form-group">
                  <label>Expected Close Date</label>
                  <input
                    type="date"
                    value={formData.expected_close_date}
                    onChange={(e) => setFormData({ ...formData, expected_close_date: e.target.value })}
                  />
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>Pipeline Stage</label>
                  <select
                    value={formData.stage || ''}
                    onChange={(e) => setFormData({ ...formData, stage: parseInt(e.target.value) })}
                  >
                    {sortedStages.map((stage) => (
                      <option key={stage.id} value={stage.id}>
                        {stage.name}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="form-actions">
                <button type="button" onClick={() => setShowDealModal(false)} className="btn-secondary">
                  Cancel
                </button>
                <button type="submit" className="btn-primary">
                  {editingDeal ? 'Update' : 'Create'} Deal
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Delete confirmation dialog */}
      <deleteDialog.ConfirmDialog />
    </div>
  )
}

export default PipelineKanban
