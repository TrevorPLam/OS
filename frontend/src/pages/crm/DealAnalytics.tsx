import React, { useEffect, useMemo, useState } from 'react'
import { Deal, Pipeline, useDealForecast, useDeals, usePipelines } from '../../api/crm'
import './DealAnalytics.css'

const DealAnalytics: React.FC = () => {
  const { data: pipelines = [], isLoading: pipelinesLoading } = usePipelines()
  const [selectedPipeline, setSelectedPipeline] = useState<Pipeline | null>(null)
  const { data: deals = [] } = useDeals(
    selectedPipeline ? { pipeline: selectedPipeline.id } : undefined,
  )
  const { data: forecast } = useDealForecast()
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (pipelines.length > 0 && !selectedPipeline) {
      const defaultPipeline = pipelines.find((pipeline) => pipeline.is_default) || pipelines[0]
      if (defaultPipeline) {
        setSelectedPipeline(defaultPipeline)
      }
    }
  }, [pipelines, selectedPipeline])

  useEffect(() => {
    if (!pipelinesLoading) {
      setLoading(false)
    }
  }, [pipelinesLoading])

  const winLossMetrics = useMemo(() => {
    const wonDeals = deals.filter((deal) => deal.is_won)
    const lostDeals = deals.filter((deal) => deal.is_lost)
    const activeDeals = deals.filter((deal) => deal.is_active)
    const totalDeals = deals.length

    const wonValue = wonDeals.reduce((sum, deal) => sum + parseFloat(deal.value), 0)
    const lostValue = lostDeals.reduce((sum, deal) => sum + parseFloat(deal.value), 0)
    const activeValue = activeDeals.reduce((sum, deal) => sum + parseFloat(deal.value), 0)

    const winRate = totalDeals > 0 ? (wonDeals.length / (wonDeals.length + lostDeals.length)) * 100 : 0
    const avgDealSize = wonDeals.length > 0 ? wonValue / wonDeals.length : 0
    const avgSalesCycle = calculateAvgSalesCycle(wonDeals)

    return {
      wonCount: wonDeals.length,
      lostCount: lostDeals.length,
      activeCount: activeDeals.length,
      wonValue,
      lostValue,
      activeValue,
      winRate,
      avgDealSize,
      avgSalesCycle,
    }
  }, [deals])

  const calculateAvgSalesCycle = (wonDeals: Deal[]) => {
    if (wonDeals.length === 0) return 0

    const cycles = wonDeals
      .filter((deal) => deal.actual_close_date)
      .map((deal) => {
        const created = new Date(deal.created_at)
        const closed = new Date(deal.actual_close_date!)
        return Math.floor((closed.getTime() - created.getTime()) / (1000 * 60 * 60 * 24))
      })

    return cycles.length > 0 ? cycles.reduce((sum, days) => sum + days, 0) / cycles.length : 0
  }

  const calculateDealsByStage = () => {
    if (!selectedPipeline || !selectedPipeline.stages) return []

    const stageMap = new Map<number, { name: string; count: number; value: number; probability: number }>()

    deals.forEach((deal) => {
      const stage = selectedPipeline.stages?.find((stageEntry) => stageEntry.id === deal.stage)
      if (!stage) return

      const existing = stageMap.get(deal.stage) || {
        name: stage.name,
        count: 0,
        value: 0,
        probability: stage.probability,
      }
      existing.count++
      existing.value += parseFloat(deal.value)
      stageMap.set(deal.stage, existing)
    })

    return Array.from(stageMap.values()).sort((a, b) => b.value - a.value)
  }

  const calculateTopLostReasons = () => {
    const lostDeals = deals.filter((deal) => deal.is_lost && deal.lost_reason)
    const reasonMap = new Map<string, number>()

    lostDeals.forEach((deal) => {
      const reason = deal.lost_reason || 'Unknown'
      reasonMap.set(reason, (reasonMap.get(reason) || 0) + 1)
    })

    return Array.from(reasonMap.entries())
      .map(([reason, count]) => ({ reason, count }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 5)
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

  if (loading && pipelines.length === 0) {
    return <div className="loading">Loading...</div>
  }

  const metrics = calculateWinLossMetrics
  const dealsByStage = calculateDealsByStage()
  const topLostReasons = calculateTopLostReasons()

  return (
    <div className="analytics-page">
      <div className="analytics-header">
        <div>
          <h1>Pipeline Analytics & Forecasting</h1>
          <p>Performance metrics and revenue projections</p>
        </div>

        <div className="pipeline-selector">
          <label>Pipeline:</label>
          <select
            value={selectedPipeline?.id || ''}
            onChange={(e) => {
              const pipeline = pipelines.find((pipelineEntry) => pipelineEntry.id === parseInt(e.target.value))
              setSelectedPipeline(pipeline || null)
            }}
          >
            {pipelines.map((pipeline) => (
              <option key={pipeline.id} value={pipeline.id}>
                {pipeline.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="analytics-grid">
        <div className="analytics-card full-width">
          <h2>Win/Loss Performance</h2>
          <div className="metrics-row">
            <div className="metric-box won">
              <div className="metric-icon">✓</div>
              <div className="metric-content">
                <div className="metric-value">{metrics.wonCount}</div>
                <div className="metric-label">Deals Won</div>
              </div>
            </div>
            <div className="metric-box lost">
              <div className="metric-icon">✕</div>
              <div className="metric-content">
                <div className="metric-value">{metrics.lostCount}</div>
                <div className="metric-label">Deals Lost</div>
              </div>
            </div>
            <div className="metric-box active">
              <div className="metric-icon">•</div>
              <div className="metric-content">
                <div className="metric-value">{metrics.activeCount}</div>
                <div className="metric-label">Active Deals</div>
              </div>
            </div>
            <div className="metric-box win-rate">
              <div className="metric-icon">%</div>
              <div className="metric-content">
                <div className="metric-value">{metrics.winRate.toFixed(1)}%</div>
                <div className="metric-label">Win Rate</div>
              </div>
            </div>
          </div>
        </div>

        <div className="analytics-card">
          <h3>Revenue Summary</h3>
          <div className="revenue-stats">
            <div className="stat">
              <span className="stat-label">Won Value</span>
              <span className="stat-value won">{formatCurrency(metrics.wonValue)}</span>
            </div>
            <div className="stat">
              <span className="stat-label">Lost Value</span>
              <span className="stat-value lost">{formatCurrency(metrics.lostValue)}</span>
            </div>
            <div className="stat">
              <span className="stat-label">Pipeline Value</span>
              <span className="stat-value">{formatCurrency(metrics.activeValue)}</span>
            </div>
            <div className="stat">
              <span className="stat-label">Avg Deal Size</span>
              <span className="stat-value">{formatCurrency(metrics.avgDealSize)}</span>
            </div>
            <div className="stat">
              <span className="stat-label">Avg Sales Cycle</span>
              <span className="stat-value">{metrics.avgSalesCycle.toFixed(0)} days</span>
            </div>
          </div>
        </div>

        <div className="analytics-card">
          <h3>Stage Distribution</h3>
          <div className="stage-distribution">
            {dealsByStage.map((stage) => (
              <div key={stage.name} className="stage-item">
                <div className="stage-info">
                  <span className="stage-name">{stage.name}</span>
                  <span className="stage-count">{stage.count} deals</span>
                </div>
                <div className="stage-bar">
                  <div
                    className="stage-bar-fill"
                    style={{ width: `${(stage.value / metrics.activeValue) * 100}%` }}
                  />
                </div>
                <span className="stage-value">{formatCurrency(stage.value)}</span>
              </div>
            ))}
          </div>
        </div>

        {forecast && (
          <div className="analytics-card full-width">
            <h2>Revenue Forecast</h2>
            <div className="forecast-summary">
              <div className="forecast-stat">
                <span className="stat-label">Total Pipeline Value</span>
                <span className="stat-value">{formatCurrency(forecast.total_pipeline_value)}</span>
              </div>
              <div className="forecast-stat">
                <span className="stat-label">Weighted Forecast</span>
                <span className="stat-value">{formatCurrency(forecast.total_weighted_value)}</span>
              </div>
            </div>
            <div className="forecast-chart">
              {forecast.monthly_forecast.map((month, index) => (
                <div key={index} className="forecast-bar">
                  <div
                    className="bar-fill"
                    style={{
                      height: `${(month.weighted_value / forecast.total_weighted_value) * 100}%`,
                    }}
                  />
                  <span className="bar-label">{formatMonth(month.month)}</span>
                  <span className="bar-value">{formatCurrency(month.weighted_value)}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {topLostReasons.length > 0 && (
          <div className="analytics-card full-width">
            <h2>Top Loss Reasons</h2>
            <div className="loss-reasons-chart">
              {topLostReasons.map((reason) => (
                <div key={reason.reason} className="reason-bar">
                  <span className="reason-label">{reason.reason}</span>
                  <div className="reason-bar-container">
                    <div
                      className="reason-bar-fill"
                      style={{ width: `${(reason.count / topLostReasons[0].count) * 100}%` }}
                    />
                  </div>
                  <span className="reason-count">{reason.count}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default DealAnalytics
