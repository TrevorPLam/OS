import React, { useState, useEffect } from 'react'
import { crmApi, Pipeline } from '../../api/crm'
import './CRM.css'

interface ForecastData {
  total_pipeline_value: number
  total_weighted_value: number
  monthly_forecast: Array<{
    month: string | null
    deal_count: number
    total_value: number
    weighted_value: number
  }>
}

interface WinLossData {
  summary: {
    total_closed: number
    won_count: number
    lost_count: number
    win_rate: number
    loss_rate: number
    won_value: number
    lost_value: number
    avg_won_deal: number
    avg_lost_deal: number
  }
  monthly_won: Array<{
    month: string
    deal_count: number
    total_value: number
  }>
  monthly_lost: Array<{
    month: string
    deal_count: number
    total_value: number
  }>
  top_loss_reasons: Array<{
    lost_reason: string
    count: number
  }>
}

interface PipelineAnalyticsData {
  total_deals: number
  total_value: number
  total_weighted_value: number
  average_deal_value: number
  average_probability: number
  stage_breakdown: Array<{
    stage_id: number
    stage_name: string
    deal_count: number
    total_value: number
    weighted_value: number
  }>
}

const PipelineAnalytics: React.FC = () => {
  const [pipelines, setPipelines] = useState<Pipeline[]>([])
  const [selectedPipeline, setSelectedPipeline] = useState<number | null>(null)
  const [loading, setLoading] = useState(true)
  const [forecastData, setForecastData] = useState<ForecastData | null>(null)
  const [winLossData, setWinLossData] = useState<WinLossData | null>(null)
  const [pipelineAnalytics, setPipelineAnalytics] = useState<PipelineAnalyticsData | null>(null)

  useEffect(() => {
    loadData()
  }, [])

  useEffect(() => {
    if (selectedPipeline) {
      loadPipelineAnalytics(selectedPipeline)
    }
  }, [selectedPipeline])

  const loadData = async () => {
    try {
      setLoading(true)
      const [pipelinesData, forecastResponse, winLossResponse] = await Promise.all([
        crmApi.getPipelines(),
        fetch('/api/crm/deals/forecast/', {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
          },
        }).then(res => res.json()),
        fetch('/api/crm/deals/win_loss_report/', {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
          },
        }).then(res => res.json()),
      ])
      
      setPipelines(pipelinesData)
      setForecastData(forecastResponse)
      setWinLossData(winLossResponse)
      
      // Select the default or first pipeline
      const defaultPipeline = pipelinesData.find(p => p.is_default) || pipelinesData[0]
      if (defaultPipeline) {
        setSelectedPipeline(defaultPipeline.id)
      }
    } catch (error) {
      console.error('Error loading data:', error)
    } finally {
      setLoading(false)
    }
  }

  const loadPipelineAnalytics = async (pipelineId: number) => {
    try {
      const response = await fetch(`/api/crm/pipelines/${pipelineId}/analytics/`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      })
      const data = await response.json()
      setPipelineAnalytics(data)
    } catch (error) {
      console.error('Error loading pipeline analytics:', error)
    }
  }

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value)
  }

  const formatMonth = (dateString: string | null) => {
    if (!dateString) return 'No Date'
    const date = new Date(dateString)
    return date.toLocaleDateString('en-US', { year: 'numeric', month: 'short' })
  }

  if (loading) {
    return <div className="loading-spinner">Loading analytics...</div>
  }

  return (
    <div className="crm-page pipeline-analytics">
      <div className="page-header">
        <div className="header-left">
          <h1>Pipeline Analytics & Forecasting</h1>
          <p className="subtitle">Revenue forecasting and performance insights</p>
        </div>
        <div className="header-right">
          <div className="pipeline-selector">
            <label>Pipeline:</label>
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
      </div>

      {/* Win/Loss Summary */}
      {winLossData && (
        <div className="analytics-section">
          <h2>Win/Loss Performance</h2>
          <div className="performance-grid">
            <div className="metric-card">
              <h4>Win Rate</h4>
              <p className="metric-value" style={{ color: '#059669' }}>
                {winLossData.summary.win_rate}%
              </p>
              <small>{winLossData.summary.won_count} won deals</small>
            </div>
            <div className="metric-card">
              <h4>Loss Rate</h4>
              <p className="metric-value" style={{ color: '#dc2626' }}>
                {winLossData.summary.loss_rate}%
              </p>
              <small>{winLossData.summary.lost_count} lost deals</small>
            </div>
            <div className="metric-card">
              <h4>Total Closed</h4>
              <p className="metric-value">{winLossData.summary.total_closed}</p>
              <small>Total deals closed</small>
            </div>
            <div className="metric-card">
              <h4>Won Revenue</h4>
              <p className="metric-value" style={{ color: '#059669' }}>
                {formatCurrency(winLossData.summary.won_value)}
              </p>
              <small>Avg: {formatCurrency(winLossData.summary.avg_won_deal)}</small>
            </div>
            <div className="metric-card">
              <h4>Lost Revenue</h4>
              <p className="metric-value" style={{ color: '#dc2626' }}>
                {formatCurrency(winLossData.summary.lost_value)}
              </p>
              <small>Avg: {formatCurrency(winLossData.summary.avg_lost_deal)}</small>
            </div>
          </div>

          {/* Top Loss Reasons */}
          {winLossData.top_loss_reasons.length > 0 && (
            <div className="loss-reasons">
              <h3>Top Loss Reasons</h3>
              <div className="reasons-list">
                {winLossData.top_loss_reasons.map((reason, index) => (
                  <div key={index} className="reason-item">
                    <span className="reason-text">{reason.lost_reason}</span>
                    <span className="reason-count">{reason.count} deals</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Pipeline Forecast */}
      {forecastData && (
        <div className="analytics-section">
          <h2>Revenue Forecast</h2>
          <div className="forecast-summary">
            <div className="forecast-metric">
              <h4>Total Pipeline Value</h4>
              <p className="metric-value">{formatCurrency(forecastData.total_pipeline_value)}</p>
            </div>
            <div className="forecast-metric">
              <h4>Weighted Value</h4>
              <p className="metric-value">{formatCurrency(forecastData.total_weighted_value)}</p>
              <small>Based on deal probabilities</small>
            </div>
          </div>

          <div className="forecast-timeline">
            <h3>Monthly Forecast</h3>
            <div className="timeline-grid">
              {forecastData.monthly_forecast.map((month, index) => (
                <div key={index} className="timeline-item">
                  <h4>{formatMonth(month.month)}</h4>
                  <div className="timeline-stats">
                    <div className="timeline-stat">
                      <span className="stat-label">Deals</span>
                      <span className="stat-value">{month.deal_count}</span>
                    </div>
                    <div className="timeline-stat">
                      <span className="stat-label">Value</span>
                      <span className="stat-value">{formatCurrency(month.total_value)}</span>
                    </div>
                    <div className="timeline-stat">
                      <span className="stat-label">Weighted</span>
                      <span className="stat-value">{formatCurrency(month.weighted_value)}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Pipeline-Specific Analytics */}
      {pipelineAnalytics && (
        <div className="analytics-section">
          <h2>Pipeline Performance</h2>
          <div className="performance-grid">
            <div className="metric-card">
              <h4>Active Deals</h4>
              <p className="metric-value">{pipelineAnalytics.total_deals}</p>
            </div>
            <div className="metric-card">
              <h4>Total Value</h4>
              <p className="metric-value">{formatCurrency(pipelineAnalytics.total_value)}</p>
            </div>
            <div className="metric-card">
              <h4>Weighted Value</h4>
              <p className="metric-value">{formatCurrency(pipelineAnalytics.total_weighted_value)}</p>
            </div>
            <div className="metric-card">
              <h4>Avg Deal Size</h4>
              <p className="metric-value">{formatCurrency(pipelineAnalytics.average_deal_value)}</p>
            </div>
            <div className="metric-card">
              <h4>Avg Probability</h4>
              <p className="metric-value">{pipelineAnalytics.average_probability.toFixed(1)}%</p>
            </div>
          </div>

          <div className="stage-breakdown">
            <h3>Stage Breakdown</h3>
            <div className="stage-list">
              {pipelineAnalytics.stage_breakdown.map(stage => (
                <div key={stage.stage_id} className="stage-item">
                  <div className="stage-header">
                    <h4>{stage.stage_name}</h4>
                    <span className="stage-count">{stage.deal_count} deals</span>
                  </div>
                  <div className="stage-metrics">
                    <div className="stage-metric">
                      <span className="metric-label">Total Value:</span>
                      <span className="metric-value">{formatCurrency(stage.total_value)}</span>
                    </div>
                    <div className="stage-metric">
                      <span className="metric-label">Weighted Value:</span>
                      <span className="metric-value">{formatCurrency(stage.weighted_value)}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default PipelineAnalytics
