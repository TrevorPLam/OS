import React, { useEffect, useMemo, useState } from 'react'
import {
  Deal,
  PipelineStage,
  useCreateDeal,
  useDeals,
  useDeleteDeal,
  useMarkDealLost,
  useMarkDealWon,
  useMoveDealToStage,
  usePipelineStages,
  usePipelines,
  useStaleDeals,
  useUpdateDeal,
} from '../../api/crm'
import { useConfirmDialog } from '../../components/ConfirmDialog'
import ErrorDisplay from '../../components/ErrorDisplay'
import './Deals.css'

const Deals: React.FC = () => {
  const [selectedPipelineId, setSelectedPipelineId] = useState<number | null>(null)
  const [showModal, setShowModal] = useState(false)
  const [editingDeal, setEditingDeal] = useState<Deal | null>(null)
  const [draggedDeal, setDraggedDeal] = useState<Deal | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [filterStale, setFilterStale] = useState(false)
  const [dealToDelete, setDealToDelete] = useState<number | null>(null)
  const { data: pipelines = [], isLoading: pipelinesLoading, error: pipelinesError } = usePipelines()
  const {
    data: stages = [],
    isLoading: stagesLoading,
    error: stagesError,
  } = usePipelineStages(selectedPipelineId ?? undefined)
  const {
    data: activeDeals = [],
    isLoading: dealsLoading,
    error: dealsError,
  } = useDeals(
    selectedPipelineId ? { pipeline: selectedPipelineId, is_active: true } : undefined,
  )
  const { data: staleDeals = [], error: staleDealsError } = useStaleDeals()
  const createDealMutation = useCreateDeal()
  const updateDealMutation = useUpdateDeal()
  const deleteDealMutation = useDeleteDeal()
  const moveDealMutation = useMoveDealToStage()
  const markDealWonMutation = useMarkDealWon()
  const markDealLostMutation = useMarkDealLost()
  const [actionError, setActionError] = useState<string | null>(null)

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

  const [formData, setFormData] = useState({
    name: '',
    description: '',
    value: '',
    probability: 50,
    expected_close_date: '',
    owner: null as number | null,
  })

  useEffect(() => {
    if (!selectedPipelineId && pipelines.length > 0) {
      const defaultPipeline = pipelines.find((pipeline) => pipeline.is_default) || pipelines[0]
      if (defaultPipeline) {
        setSelectedPipelineId(defaultPipeline.id)
      }
    }
  }, [pipelines, selectedPipelineId])

  const selectedDeals = useMemo(() => {
    if (!selectedPipelineId) return []
    if (filterStale) {
      return staleDeals.filter((deal) => deal.pipeline === selectedPipelineId)
    }
    return activeDeals
  }, [activeDeals, filterStale, selectedPipelineId, staleDeals])

  const sortedStages = useMemo(
    () => [...stages].sort((a, b) => a.display_order - b.display_order),
    [stages],
  )

  const getDealsByStage = (stageId: number) => {
    const stageDeals = selectedDeals.filter((deal) => deal.stage === stageId)

    if (searchQuery) {
      const query = searchQuery.toLowerCase()
      return stageDeals.filter(
        (deal) =>
          deal.name.toLowerCase().includes(query) ||
          deal.description?.toLowerCase().includes(query) ||
          deal.account_name?.toLowerCase().includes(query),
      )
    }

    return stageDeals
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
      await moveDealMutation.mutateAsync({
        id: draggedDeal.id,
        stageId: targetStageId,
        notes: 'Moved via drag and drop',
      })
    } catch {
      setActionError('Unable to move the deal. Please try again.')
    } finally {
      setDraggedDeal(null)
    }
  }

  const openModal = (deal?: Deal) => {
    if (deal) {
      setEditingDeal(deal)
      setFormData({
        name: deal.name,
        description: deal.description || '',
        value: deal.value,
        probability: deal.probability,
        expected_close_date: deal.expected_close_date,
        owner: deal.owner || null,
      })
    } else {
      setEditingDeal(null)
      setFormData({
        name: '',
        description: '',
        value: '',
        probability: 50,
        expected_close_date: '',
        owner: null,
      })
    }
    setShowModal(true)
  }

  const resetForm = () => {
    setShowModal(false)
    setEditingDeal(null)
    setFormData({
      name: '',
      description: '',
      value: '',
      probability: 50,
      expected_close_date: '',
      owner: null,
    })
    setActionError(null)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedPipelineId) return

    try {
      const dealData = {
        ...formData,
        pipeline: selectedPipelineId,
        stage: sortedStages[0]?.id,
      }

      if (editingDeal) {
        await updateDealMutation.mutateAsync({ id: editingDeal.id, data: dealData })
      } else {
        await createDealMutation.mutateAsync(dealData)
      }

      resetForm()
      setActionError(null)
    } catch {
      setActionError('Unable to save the deal. Please check the details and try again.')
    }
  }

  const handleDelete = (id: number) => {
    setDealToDelete(id)
    deleteDialog.show()
  }

  const handleMarkWon = async (id: number) => {
    try {
      await markDealWonMutation.mutateAsync(id)
      setActionError(null)
    } catch {
      setActionError('Unable to mark the deal as won. Please try again.')
    }
  }

  const handleMarkLost = async (id: number) => {
    const reason = window.prompt('Enter reason for losing the deal:')
    if (!reason) return

    try {
      await markDealLostMutation.mutateAsync({ id, reason })
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

  const getStageColor = (stage: PipelineStage) => {
    if (stage.is_closed_won) return '#48bb78'
    if (stage.is_closed_lost) return '#f56565'
    return '#4299e1'
  }

  const calculateMetrics = () => {
    const totalValue = selectedDeals.reduce((sum, deal) => sum + parseFloat(deal.value), 0)
    const totalWeightedValue = selectedDeals.reduce((sum, deal) => sum + parseFloat(deal.weighted_value), 0)
    const avgDealSize = selectedDeals.length > 0 ? totalValue / selectedDeals.length : 0

    return {
      totalValue,
      totalWeightedValue,
      avgDealSize,
      dealCount: selectedDeals.length,
    }
  }

  const metrics = calculateMetrics()

  if (pipelinesLoading && pipelines.length === 0) {
    return <div className="loading">Loading...</div>
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
    <div className="deals-page">
      {(stagesError || dealsError || staleDealsError || actionError) && (
        <ErrorDisplay
          error={
            actionError ||
            stagesError ||
            dealsError ||
            staleDealsError ||
            'Something went wrong. Please try again.'
          }
          variant="banner"
          onDismiss={() => setActionError(null)}
        />
      )}
      <div className="deals-header">
        <div>
          <h1>Sales Pipeline</h1>
          <div className="pipeline-metrics">
            <div className="metric">
              <span className="metric-value">{formatCurrency(metrics.totalValue.toString())}</span>
              <span className="metric-label">Total Value</span>
            </div>
            <div className="metric">
              <span className="metric-value">{formatCurrency(metrics.totalWeightedValue.toString())}</span>
              <span className="metric-label">Weighted Value</span>
            </div>
            <div className="metric">
              <span className="metric-value">{metrics.dealCount}</span>
              <span className="metric-label">Active Deals</span>
            </div>
            <div className="metric">
              <span className="metric-value">{formatCurrency(metrics.avgDealSize.toString())}</span>
              <span className="metric-label">Avg Deal Size</span>
            </div>
          </div>
        </div>

        <div className="header-actions">
          <div className="pipeline-selector">
            <label>Pipeline:</label>
            <select
              value={selectedPipelineId || ''}
              onChange={(e) => setSelectedPipelineId(parseInt(e.target.value))}
            >
              {pipelines.map((pipeline) => (
                <option key={pipeline.id} value={pipeline.id}>
                  {pipeline.name}
                </option>
              ))}
            </select>
          </div>

          <button onClick={() => openModal()} className="btn btn-primary">
            + Add Deal
          </button>
        </div>
      </div>

      <div className="deals-filters">
        <input
          type="text"
          placeholder="Search deals..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="search-input"
        />

        <label className="filter-checkbox">
          <input
            type="checkbox"
            checked={filterStale}
            onChange={(e) => setFilterStale(e.target.checked)}
          />
          Show only stale deals
        </label>
      </div>

      <div className="pipeline-board">
        {stagesLoading || dealsLoading ? <div className="loading">Loading deals...</div> : null}
        {sortedStages.map((stage) => (
          <div
            key={stage.id}
            className="pipeline-column"
            onDragOver={handleDragOver}
            onDrop={(e) => handleDrop(e, stage.id)}
          >
            <div className="column-header" style={{ borderTopColor: getStageColor(stage) }}>
              <h3>{stage.name}</h3>
              <span className="deal-count">{getDealsByStage(stage.id).length}</span>
              <span className="stage-probability">{stage.probability}%</span>
            </div>

            <div className="column-deals">
              {getDealsByStage(stage.id).map((deal) => (
                <div
                  key={deal.id}
                  className={`deal-card ${deal.is_stale ? 'stale' : ''}`}
                  draggable
                  onDragStart={(e) => handleDragStart(e, deal)}
                >
                  <div className="deal-card-header">
                    <h4>{deal.name}</h4>
                    {deal.is_stale && <span className="stale-badge">⚠️ Stale</span>}
                  </div>

                  {deal.account_name && <p className="deal-account">🏢 {deal.account_name}</p>}

                  <div className="deal-value">
                    <span className="value">{formatCurrency(deal.value)}</span>
                    <span className="probability">
                      {deal.probability}% • {formatCurrency(deal.weighted_value)}
                    </span>
                  </div>

                  <div className="deal-meta">
                    <span className="close-date">
                      📅 {new Date(deal.expected_close_date).toLocaleDateString()}
                    </span>
                    {deal.owner_name && <span className="owner">👤 {deal.owner_name}</span>}
                  </div>

                  <div className="deal-actions">
                    <button onClick={() => openModal(deal)} className="btn-text">
                      Edit
                    </button>
                    {!stage.is_closed_won && !stage.is_closed_lost && (
                      <>
                        <button onClick={() => handleMarkWon(deal.id)} className="btn-text text-success">
                          Won
                        </button>
                        <button onClick={() => handleMarkLost(deal.id)} className="btn-text text-danger">
                          Lost
                        </button>
                      </>
                    )}
                    <button onClick={() => handleDelete(deal.id)} className="btn-text text-danger">
                      Delete
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>

      {showModal && (
        <div className="modal-overlay" onClick={resetForm}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>{editingDeal ? 'Edit Deal' : 'Create Deal'}</h2>
              <button className="modal-close" onClick={resetForm}>
                ✕
              </button>
            </div>

            <form onSubmit={handleSubmit} className="deal-form">
              <div className="form-group">
                <label htmlFor="name">Deal Name *</label>
                <input
                  id="name"
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  required
                />
              </div>

              <div className="form-group">
                <label htmlFor="description">Description</label>
                <textarea
                  id="description"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  rows={3}
                />
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="value">Deal Value *</label>
                  <input
                    id="value"
                    type="number"
                    step="0.01"
                    min="0"
                    value={formData.value}
                    onChange={(e) => setFormData({ ...formData, value: e.target.value })}
                    required
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="probability">Probability (%)</label>
                  <input
                    id="probability"
                    type="number"
                    min="0"
                    max="100"
                    value={formData.probability}
                    onChange={(e) => setFormData({ ...formData, probability: parseInt(e.target.value) })}
                  />
                </div>
              </div>

              <div className="form-group">
                <label htmlFor="expected_close_date">Expected Close Date *</label>
                <input
                  id="expected_close_date"
                  type="date"
                  value={formData.expected_close_date}
                  onChange={(e) => setFormData({ ...formData, expected_close_date: e.target.value })}
                  required
                />
              </div>

              <div className="modal-actions">
                <button type="button" onClick={resetForm} className="btn btn-secondary">
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary">
                  {editingDeal ? 'Update' : 'Create'}
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

export default Deals
