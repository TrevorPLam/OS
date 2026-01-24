import React, { useEffect, useState } from 'react'
import { useForecast, usePipelineAnalytics, usePipelines, useWinLossReport } from '../../api/crm'
import './CRM.css'

const PipelineAnalytics: React.FC = () => {
  const { data: pipelines = [], isLoading: pipelinesLoading, error: pipelinesError } = usePipelines()
  const { data: forecastData, error: forecastError } = useForecast()
  const { data: winLossData, error: winLossError } = useWinLossReport()
  const [selectedPipeline, setSelectedPipeline] = useState<number | null>(null)
  const { data: pipelineAnalytics, error: pipelineAnalyticsError } = usePipelineAnalytics(
    selectedPipeline ?? undefined,
  )

  useEffect(() => {
    if (!selectedPipeline && pipelines.length > 0) {
      const defaultPipeline = pipelines.find((pipeline) => pipeline.is_default) || pipelines[0]
      if (defaultPipeline) {
        setSelectedPipeline(defaultPipeline.id)
      }
    }
  }, [pipelines, selectedPipeline])

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

  if (pipelinesLoading) {
    return <div className="loading-spinner">Loading analytics...</div>
  }

  if (pipelinesError) {
    return <div className="error">Unable to load pipelines. Please refresh and try again.</div>
  }

  return (
    <div className="crm-page pipeline-analytics">
      {(forecastError || winLossError || pipelineAnalyticsError) && (
        <div className="error">
          {forecastError?.message ||
            winLossError?.message ||
            pipelineAnalyticsError?.message ||
            'Something went wrong. Please try again.'}
        </div>
      )}
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
              {pipelines.map((pipeline) => (
                <option key={pipeline.id} value={pipeline.id}>
                  {pipeline.name} {pipeline.is_default && '(Default)'}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

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
            </div>
          </div>
          <div className="forecast-chart">
            {forecastData.monthly_forecast.map((month, index) => (
              <div key={index} className="forecast-bar">
                <div
                  className="bar-fill"
                  style={{ height: `${(month.weighted_value / forecastData.total_weighted_value) * 100}%` }}
                />
                <span className="bar-label">{formatMonth(month.month)}</span>
                <span className="bar-value">{formatCurrency(month.weighted_value)}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {pipelineAnalytics && (
        <div className="analytics-section">
          <h2>Pipeline Performance</h2>
          <div className="performance-metrics">
            <div className="metric-card">
              <h4>Total Deals</h4>
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
          </div>
          <div className="stage-breakdown">
            <h3>Stage Breakdown</h3>
            <div className="stage-grid">
              {pipelineAnalytics.stage_breakdown.map((stage) => (
                <div key={stage.stage_id} className="stage-card">
                  <h4>{stage.stage_name}</h4>
                  <p>{stage.deal_count} deals</p>
                  <p>Value: {formatCurrency(stage.total_value)}</p>
                  <p>Weighted: {formatCurrency(stage.weighted_value)}</p>
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
