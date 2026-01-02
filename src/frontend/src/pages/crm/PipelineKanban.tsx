import React, { useState, useEffect } from 'react'
import { crmApi, Deal, Pipeline, PipelineStage } from '../../api/crm'
import './CRM.css'

const PipelineKanban: React.FC = () => {
  const [pipelines, setPipelines] = useState<Pipeline[]>([])
  const [selectedPipeline, setSelectedPipeline] = useState<number | null>(null)
  const [stages, setStages] = useState<PipelineStage[]>([])
  const [deals, setDeals] = useState<Deal[]>([])
  const [loading, setLoading] = useState(true)
  const [showDealModal, setShowDealModal] = useState(false)
  const [editingDeal, setEditingDeal] = useState<Deal | null>(null)
  const [draggedDeal, setDraggedDeal] = useState<Deal | null>(null)
  const [searchTerm, setSearchTerm] = useState('')

  const [formData, setFormData] = useState<Partial<Deal>>({
    name: '',
    description: '',
    value: '0',
    expected_close_date: '',
    owner: undefined,
    account: undefined,
  })

  useEffect(() => {
    loadData()
  }, [])

  useEffect(() => {
    if (selectedPipeline) {
      loadPipelineData(selectedPipeline)
    }
  }, [selectedPipeline])

  const loadData = async () => {
    try {
      setLoading(true)
      const pipelinesData = await crmApi.getPipelines()
      setPipelines(pipelinesData)
      
      // Select the default or first pipeline
      const defaultPipeline = pipelinesData.find(p => p.is_default) || pipelinesData[0]
      if (defaultPipeline) {
        setSelectedPipeline(defaultPipeline.id)
      }
    } catch (error) {
      console.error('Error loading pipelines:', error)
    } finally {
      setLoading(false)
    }
  }

  const loadPipelineData = async (pipelineId: number) => {
    try {
      setLoading(true)
      const [stagesData, dealsData] = await Promise.all([
        crmApi.getPipelineStages(pipelineId),
        crmApi.getDeals({ pipeline: pipelineId }),
      ])
      setStages(stagesData.sort((a, b) => a.display_order - b.display_order))
      setDeals(dealsData)
    } catch (error) {
      console.error('Error loading pipeline data:', error)
    } finally {
      setLoading(false)
    }
  }

  const getDealsByStage = (stageId: number) => {
    return deals
      .filter(deal => deal.stage === stageId)
      .filter(deal => 
        searchTerm === '' || 
        deal.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (deal.account_name && deal.account_name.toLowerCase().includes(searchTerm.toLowerCase()))
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
      await crmApi.moveDealToStage(draggedDeal.id, targetStageId)
      await loadPipelineData(selectedPipeline!)
    } catch (error) {
      console.error('Error moving deal:', error)
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
      stage: stages[0]?.id,
    })
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
    setShowDealModal(true)
  }

  const handleSaveDeal = async () => {
    try {
      if (editingDeal) {
        await crmApi.updateDeal(editingDeal.id, formData)
      } else {
        await crmApi.createDeal(formData)
      }
      setShowDealModal(false)
      await loadPipelineData(selectedPipeline!)
    } catch (error) {
      console.error('Error saving deal:', error)
    }
  }

  const handleDeleteDeal = async (dealId: number) => {
    if (!window.confirm('Are you sure you want to delete this deal?')) return

    try {
      await crmApi.deleteDeal(dealId)
      await loadPipelineData(selectedPipeline!)
    } catch (error) {
      console.error('Error deleting deal:', error)
    }
  }

  const handleMarkWon = async (dealId: number) => {
    try {
      await crmApi.markDealWon(dealId)
      await loadPipelineData(selectedPipeline!)
    } catch (error) {
      console.error('Error marking deal as won:', error)
    }
  }

  const handleMarkLost = async (dealId: number) => {
    const reason = window.prompt('Please provide a reason for losing this deal:')
    if (reason === null) return // User cancelled

    try {
      await crmApi.markDealLost(dealId, reason)
      await loadPipelineData(selectedPipeline!)
    } catch (error) {
      console.error('Error marking deal as lost:', error)
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
      .filter(deal => deal.is_active)
      .reduce((sum, deal) => sum + parseFloat(deal.value), 0)
  }

  const getTotalWeightedValue = () => {
    return deals
      .filter(deal => deal.is_active)
      .reduce((sum, deal) => sum + parseFloat(deal.weighted_value), 0)
  }

  if (loading && !selectedPipeline) {
    return <div className="loading-spinner">Loading pipelines...</div>
  }

  return (
    <div className="crm-page pipeline-kanban">
      <div className="page-header">
        <div className="header-left">
          <h1>Pipeline</h1>
          <div className="pipeline-selector">
            <select
              value={selectedPipeline || ''}
              onChange={(e) => setSelectedPipeline(parseInt(e.target.value))}
              className="pipeline-select"
            >
              {pipelines.map(pipeline => (
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
              <span className="metric-value">{deals.filter(d => d.is_active).length}</span>
            </div>
          </div>
          <input
            type="text"
            placeholder="Search deals..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="search-input"
          />
          <button onClick={handleCreateDeal} className="btn btn-primary">
            + New Deal
          </button>
        </div>
      </div>

      <div className="kanban-board">
        {stages.map(stage => {
          const stageDeals = getDealsByStage(stage.id)
          const stageValue = stageDeals.reduce((sum, deal) => sum + parseFloat(deal.value), 0)
          
          return (
            <div
              key={stage.id}
              className="kanban-column"
              onDragOver={handleDragOver}
              onDrop={(e) => handleDrop(e, stage.id)}
            >
              <div className="column-header">
                <h3>{stage.name}</h3>
                <div className="column-stats">
                  <span className="deal-count">{stageDeals.length} deals</span>
                  <span className="stage-value">{formatCurrency(stageValue.toString())}</span>
                  <span className="stage-probability">{stage.probability}% prob</span>
                </div>
              </div>
              <div className="column-content">
                {stageDeals.map(deal => (
                  <div
                    key={deal.id}
                    className={`deal-card ${draggedDeal?.id === deal.id ? 'dragging' : ''} ${deal.is_stale ? 'stale' : ''}`}
                    draggable
                    onDragStart={(e) => handleDragStart(e, deal)}
                  >
                    <div className="deal-card-header">
                      <h4>{deal.name}</h4>
                      <div className="deal-actions">
                        <button onClick={() => handleEditDeal(deal)} className="btn-icon" title="Edit">
                          ✏️
                        </button>
                        <button onClick={() => handleDeleteDeal(deal.id)} className="btn-icon" title="Delete">
                          🗑️
                        </button>
                      </div>
                    </div>
                    <div className="deal-card-body">
                      {deal.account_name && (
                        <div className="deal-info">
                          <span className="info-label">Account:</span>
                          <span className="info-value">{deal.account_name}</span>
                        </div>
                      )}
                      <div className="deal-info">
                        <span className="info-label">Value:</span>
                        <span className="info-value">{formatCurrency(deal.value)}</span>
                      </div>
                      <div className="deal-info">
                        <span className="info-label">Weighted:</span>
                        <span className="info-value">{formatCurrency(deal.weighted_value)}</span>
                      </div>
                      {deal.expected_close_date && (
                        <div className="deal-info">
                          <span className="info-label">Close Date:</span>
                          <span className="info-value">{new Date(deal.expected_close_date).toLocaleDateString()}</span>
                        </div>
                      )}
                      {deal.owner_name && (
                        <div className="deal-info">
                          <span className="info-label">Owner:</span>
                          <span className="info-value">{deal.owner_name}</span>
                        </div>
                      )}
                      {deal.is_stale && (
                        <div className="deal-badge stale-badge">
                          Stale ({deal.stale_days} days)
                        </div>
                      )}
                    </div>
                    <div className="deal-card-footer">
                      <button onClick={() => handleMarkWon(deal.id)} className="btn btn-success btn-sm">
                        Mark Won
                      </button>
                      <button onClick={() => handleMarkLost(deal.id)} className="btn btn-danger btn-sm">
                        Mark Lost
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )
        })}
      </div>

      {showDealModal && (
        <div className="modal-overlay" onClick={() => setShowDealModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h2>{editingDeal ? 'Edit Deal' : 'Create Deal'}</h2>
            <form onSubmit={(e) => { e.preventDefault(); handleSaveDeal(); }}>
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
              <div className="form-group">
                <label>Value *</label>
                <input
                  type="number"
                  step="0.01"
                  value={formData.value}
                  onChange={(e) => setFormData({ ...formData, value: e.target.value })}
                  required
                />
              </div>
              <div className="form-group">
                <label>Stage *</label>
                <select
                  value={formData.stage}
                  onChange={(e) => setFormData({ ...formData, stage: parseInt(e.target.value) })}
                  required
                >
                  {stages.map(stage => (
                    <option key={stage.id} value={stage.id}>
                      {stage.name}
                    </option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label>Expected Close Date</label>
                <input
                  type="date"
                  value={formData.expected_close_date}
                  onChange={(e) => setFormData({ ...formData, expected_close_date: e.target.value })}
                />
              </div>
              <div className="modal-actions">
                <button type="button" onClick={() => setShowDealModal(false)} className="btn btn-secondary">
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary">
                  {editingDeal ? 'Update' : 'Create'} Deal
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

export default PipelineKanban
