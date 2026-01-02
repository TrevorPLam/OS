import React, { useState, useEffect } from 'react'
import { crmApi, Pipeline, Deal } from '../../api/crm'
import './DealAnalytics.css'

interface ForecastData {
  total_pipeline_value: number
  total_weighted_value: number
  monthly_forecast: Array<{
    month: string
    deal_count: number
    total_value: number
    weighted_value: number
  }>
}

const DealAnalytics: React.FC = () => {
  const [pipelines, setPipelines] = useState<Pipeline[]>([])
  const [selectedPipeline, setSelectedPipeline] = useState<Pipeline | null>(null)
  const [deals, setDeals] = useState<Deal[]>([])
  const [forecast, setForecast] = useState<ForecastData | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadData()
  }, [])

  useEffect(() => {
    if (selectedPipeline) {
      loadDealsAndForecast()
    }
  }, [selectedPipeline])

  const loadData = async () => {
    try {
      setLoading(true)
      const pipelinesData = await crmApi.getPipelines()
      setPipelines(pipelinesData)
      
      const defaultPipeline = pipelinesData.find(p => p.is_default) || pipelinesData[0]
      if (defaultPipeline) {
        setSelectedPipeline(defaultPipeline)
      }
    } catch (error) {
      console.error('Error loading pipelines:', error)
    } finally {
      setLoading(false)
    }
  }

  const loadDealsAndForecast = async () => {
    if (!selectedPipeline) return

    try {
      setLoading(true)
      const [dealsData, forecastData] = await Promise.all([
        crmApi.getDeals({ pipeline: selectedPipeline.id }),
        crmApi.getDealForecast(),
      ])
      
      setDeals(dealsData)
      setForecast(forecastData)
    } catch (error) {
      console.error('Error loading deals and forecast:', error)
    } finally {
      setLoading(false)
    }
  }

  const calculateWinLossMetrics = () => {
    const wonDeals = deals.filter(d => d.is_won)
    const lostDeals = deals.filter(d => d.is_lost)
    const activeDeals = deals.filter(d => d.is_active)
    const totalDeals = deals.length

    const wonValue = wonDeals.reduce((sum, d) => sum + parseFloat(d.value), 0)
    const lostValue = lostDeals.reduce((sum, d) => sum + parseFloat(d.value), 0)
    const activeValue = activeDeals.reduce((sum, d) => sum + parseFloat(d.value), 0)

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
  }

  const calculateAvgSalesCycle = (wonDeals: Deal[]) => {
    if (wonDeals.length === 0) return 0

    const cycles = wonDeals
      .filter(d => d.actual_close_date)
      .map(d => {
        const created = new Date(d.created_at)
        const closed = new Date(d.actual_close_date!)
        return Math.floor((closed.getTime() - created.getTime()) / (1000 * 60 * 60 * 24))
      })

    return cycles.length > 0 ? cycles.reduce((sum, days) => sum + days, 0) / cycles.length : 0
  }

  const calculateDealsByStage = () => {
    if (!selectedPipeline) return []

    const stageMap = new Map<number, { name: string; count: number; value: number; probability: number }>()

    deals.forEach(deal => {
      const stage = selectedPipeline.stages?.find(s => s.id === deal.stage)
      if (!stage) return

      const existing = stageMap.get(deal.stage) || { name: stage.name, count: 0, value: 0, probability: stage.probability }
      existing.count++
      existing.value += parseFloat(deal.value)
      stageMap.set(deal.stage, existing)
    })

    return Array.from(stageMap.values()).sort((a, b) => b.value - a.value)
  }

  const calculateTopLostReasons = () => {
    const lostDeals = deals.filter(d => d.is_lost && d.lost_reason)
    const reasonMap = new Map<string, number>()

    lostDeals.forEach(deal => {
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

  const formatMonth = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleDateString('en-US', { year: 'numeric', month: 'short' })
  }

  if (loading && pipelines.length === 0) {
    return <div className="loading">Loading...</div>
  }

  const metrics = calculateWinLossMetrics()
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
              const pipeline = pipelines.find(p => p.id === parseInt(e.target.value))
              setSelectedPipeline(pipeline || null)
            }}
          >
            {pipelines.map(pipeline => (
              <option key={pipeline.id} value={pipeline.id}>
                {pipeline.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="analytics-grid">
        {/* Win/Loss Metrics */}
        <div className="analytics-card full-width">
          <h2>Win/Loss Performance</h2>
          <div className="metrics-row">
            <div className="metric-box won">
              <div className="metric-icon">✓</div>
              <div className="metric-content">
                <div className="metric-value">{metrics.wonCount}</div>
                <div className="metric-label">Deals Won</div>
                <div className="metric-sub">{formatCurrency(metrics.wonValue)}</div>
              </div>
            </div>

            <div className="metric-box lost">
              <div className="metric-icon">✗</div>
              <div className="metric-content">
                <div className="metric-value">{metrics.lostCount}</div>
                <div className="metric-label">Deals Lost</div>
                <div className="metric-sub">{formatCurrency(metrics.lostValue)}</div>
              </div>
            </div>

            <div className="metric-box active">
              <div className="metric-icon">⏳</div>
              <div className="metric-content">
                <div className="metric-value">{metrics.activeCount}</div>
                <div className="metric-label">Active Deals</div>
                <div className="metric-sub">{formatCurrency(metrics.activeValue)}</div>
              </div>
            </div>

            <div className="metric-box rate">
              <div className="metric-icon">%</div>
              <div className="metric-content">
                <div className="metric-value">{metrics.winRate.toFixed(1)}%</div>
                <div className="metric-label">Win Rate</div>
                <div className="metric-sub">
                  {metrics.wonCount + metrics.lostCount} total closed
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Revenue Forecast */}
        <div className="analytics-card">
          <h2>Revenue Forecast</h2>
          {forecast && (
            <>
              <div className="forecast-summary">
                <div className="forecast-metric">
                  <div className="forecast-value">{formatCurrency(forecast.total_pipeline_value)}</div>
                  <div className="forecast-label">Total Pipeline Value</div>
                </div>
                <div className="forecast-metric">
                  <div className="forecast-value">{formatCurrency(forecast.total_weighted_value)}</div>
                  <div className="forecast-label">Weighted Forecast</div>
                </div>
              </div>

              <div className="forecast-chart">
                <h3>Monthly Revenue Projection</h3>
                {forecast.monthly_forecast.length === 0 ? (
                  <p className="no-data">No forecast data available</p>
                ) : (
                  <div className="forecast-bars">
                    {forecast.monthly_forecast.map((month, index) => {
                      const maxValue = Math.max(...forecast.monthly_forecast.map(m => m.weighted_value))
                      const barHeight = maxValue > 0 ? (month.weighted_value / maxValue) * 100 : 0

                      return (
                        <div key={index} className="forecast-bar-container">
                          <div className="forecast-bar" style={{ height: `${barHeight}%` }}>
                            <div className="forecast-bar-tooltip">
                              <div>{formatCurrency(month.weighted_value)}</div>
                              <div className="tooltip-deals">{month.deal_count} deals</div>
                            </div>
                          </div>
                          <div className="forecast-bar-label">{formatMonth(month.month)}</div>
                          <div className="forecast-bar-value">{formatCurrency(month.weighted_value)}</div>
                        </div>
                      )
                    })}
                  </div>
                )}
              </div>
            </>
          )}
        </div>

        {/* Performance Metrics */}
        <div className="analytics-card">
          <h2>Performance Metrics</h2>
          <div className="performance-metrics">
            <div className="performance-metric">
              <div className="performance-label">Average Deal Size</div>
              <div className="performance-value">{formatCurrency(metrics.avgDealSize)}</div>
            </div>

            <div className="performance-metric">
              <div className="performance-label">Average Sales Cycle</div>
              <div className="performance-value">{Math.round(metrics.avgSalesCycle)} days</div>
            </div>

            <div className="performance-metric">
              <div className="performance-label">Win Rate</div>
              <div className="performance-value">{metrics.winRate.toFixed(1)}%</div>
            </div>
          </div>
        </div>

        {/* Deals by Stage */}
        <div className="analytics-card">
          <h2>Pipeline Distribution</h2>
          {dealsByStage.length === 0 ? (
            <p className="no-data">No active deals</p>
          ) : (
            <div className="stage-list">
              {dealsByStage.map((stage, index) => (
                <div key={index} className="stage-item">
                  <div className="stage-info">
                    <div className="stage-name">{stage.name}</div>
                    <div className="stage-meta">
                      {stage.count} deals • {stage.probability}% probability
                    </div>
                  </div>
                  <div className="stage-value">{formatCurrency(stage.value)}</div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Top Lost Reasons */}
        <div className="analytics-card full-width">
          <h2>Top Reasons for Lost Deals</h2>
          {topLostReasons.length === 0 ? (
            <p className="no-data">No lost deals with reasons</p>
          ) : (
            <div className="lost-reasons">
              {topLostReasons.map((item, index) => (
                <div key={index} className="lost-reason-item">
                  <div className="lost-reason-rank">#{index + 1}</div>
                  <div className="lost-reason-text">{item.reason}</div>
                  <div className="lost-reason-count">{item.count} deals</div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default DealAnalytics
