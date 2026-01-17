import { useState, useEffect } from 'react'
// @ts-ignore
import { Responsive, WidthProvider } from 'react-grid-layout/legacy'
import { SectorPieChart } from '../components/analytics/SectorPieChart'
import { BenchmarkChart } from '../components/analytics/BenchmarkChart'
import { MonthlyHeatmap } from '../components/analytics/MonthlyHeatmap'
import { WidgetPeriodReturn } from '../components/analytics/WidgetPeriodReturn'
import { WidgetBestWorst } from '../components/analytics/WidgetBestWorst'
import { WidgetRisk } from '../components/analytics/WidgetRisk'
import { WidgetConcentration } from '../components/analytics/WidgetConcentration'
import 'react-grid-layout/css/styles.css'
import 'react-resizable/css/styles.css'

const ResponsiveGridLayout = WidthProvider(Responsive)

export function AnalyticsPage() {
  const [layouts, setLayouts] = useState({
    lg: [
      { i: 'period-short', x: 0, y: 0, w: 1, h: 1 },
      { i: 'period-long', x: 1, y: 0, w: 1, h: 1 },
      { i: 'best-day', x: 2, y: 0, w: 1, h: 1 },
      { i: 'worst-day', x: 3, y: 0, w: 1, h: 1 },
      
      { i: 'heatmap', x: 0, y: 1, w: 2, h: 3 },
      { i: 'sector', x: 2, y: 1, w: 2, h: 3 },
      
      { i: 'benchmark', x: 0, y: 4, w: 2, h: 3 },
      { i: 'concentration', x: 2, y: 4, w: 2, h: 2 },
      
      { i: 'risk-mdd', x: 2, y: 6, w: 1, h: 1 },
      { i: 'risk-score', x: 3, y: 6, w: 1, h: 1 },
    ],
    md: [
      { i: 'period-short', x: 0, y: 0, w: 1, h: 1 },
      { i: 'period-long', x: 1, y: 0, w: 1, h: 1 },
      { i: 'best-day', x: 0, y: 1, w: 1, h: 1 },
      { i: 'worst-day', x: 1, y: 1, w: 1, h: 1 },
      
      { i: 'heatmap', x: 0, y: 2, w: 2, h: 3 },
      { i: 'sector', x: 0, y: 5, w: 2, h: 3 },
      { i: 'benchmark', x: 0, y: 8, w: 2, h: 3 },
      
      { i: 'concentration', x: 0, y: 11, w: 2, h: 2 },
      { i: 'risk-mdd', x: 0, y: 13, w: 1, h: 1 },
      { i: 'risk-score', x: 1, y: 13, w: 1, h: 1 },
    ],
    sm: [
      { i: 'period-short', x: 0, y: 0, w: 1, h: 1 },
      { i: 'period-long', x: 0, y: 1, w: 1, h: 1 },
      { i: 'best-day', x: 0, y: 2, w: 1, h: 1 },
      { i: 'worst-day', x: 0, y: 3, w: 1, h: 1 },
      { i: 'heatmap', x: 0, y: 4, w: 1, h: 3 },
      { i: 'sector', x: 0, y: 7, w: 1, h: 3 },
      { i: 'benchmark', x: 0, y: 10, w: 1, h: 3 },
      { i: 'concentration', x: 0, y: 13, w: 1, h: 2 },
      { i: 'risk-mdd', x: 0, y: 15, w: 1, h: 1 },
      { i: 'risk-score', x: 0, y: 16, w: 1, h: 1 },
    ]
  })

  // Load layout from local storage
  useEffect(() => {
    const savedLayouts = localStorage.getItem('analytics-layout-v5')
    if (savedLayouts) {
      try {
        setLayouts(JSON.parse(savedLayouts))
      } catch (e) {
        console.error('Failed to parse layout', e)
      }
    }
  }, [])

  const onLayoutChange = (_: any, allLayouts: any) => {
    setLayouts(allLayouts)
    localStorage.setItem('analytics-layout-v5', JSON.stringify(allLayouts))
  }

  const renderDragHandle = () => (
    <div className="drag-handle absolute top-2 right-2 p-1 cursor-move opacity-0 group-hover:opacity-100 transition-opacity z-10 bg-gray-100/50 hover:bg-gray-200 rounded shadow-sm">
      <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-gray-500"><polyline points="5 9 2 12 5 15"></polyline><polyline points="9 5 12 2 15 5"></polyline><polyline points="19 9 22 12 19 15"></polyline><polyline points="9 19 12 22 15 19"></polyline><circle cx="12" cy="12" r="1"></circle></svg>
    </div>
  )

  return (
    <div className="pb-10">
      <div className="mb-6 flex justify-between items-end">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-gray-900">포트폴리오 분석</h1>
          <p className="text-sm text-gray-500 mt-1">
            드래그하여 카드의 위치를 변경하거나 크기를 조절할 수 있습니다.
          </p>
        </div>
        <button 
          onClick={() => {
            localStorage.removeItem('analytics-layout-v5')
            window.location.reload()
          }}
          className="text-xs text-gray-400 hover:text-gray-600 underline"
        >
          레이아웃 초기화
        </button>
      </div>

      <ResponsiveGridLayout
        className="layout"
        layouts={layouts}
        breakpoints={{ lg: 1200, md: 996, sm: 768, xs: 480, xxs: 0 }}
        cols={{ lg: 4, md: 2, sm: 1, xs: 1, xxs: 1 }}
        rowHeight={150}
        onLayoutChange={onLayoutChange}
        isDraggable={true}
        isResizable={true}
        draggableHandle=".drag-handle"
        margin={[16, 16]}
      >
        <div key="period-short" className="relative group h-full">
          {renderDragHandle()}
          <WidgetPeriodReturn type="short" />
        </div>
        <div key="period-long" className="relative group h-full">
          {renderDragHandle()}
          <WidgetPeriodReturn type="long" />
        </div>
        <div key="best-day" className="relative group h-full">
          {renderDragHandle()}
          <WidgetBestWorst type="best" />
        </div>
        <div key="worst-day" className="relative group h-full">
          {renderDragHandle()}
          <WidgetBestWorst type="worst" />
        </div>

        <div key="heatmap" className="relative group h-full">
          {renderDragHandle()}
          <MonthlyHeatmap />
        </div>

        <div key="sector" className="relative group h-full">
          {renderDragHandle()}
          <SectorPieChart />
        </div>

        <div key="benchmark" className="relative group h-full">
          {renderDragHandle()}
          <BenchmarkChart />
        </div>

        <div key="risk-mdd" className="relative group h-full">
          {renderDragHandle()}
          <WidgetRisk type="mdd" />
        </div>
        <div key="risk-score" className="relative group h-full">
          {renderDragHandle()}
          <WidgetRisk type="score" />
        </div>
        <div key="concentration" className="relative group h-full">
          {renderDragHandle()}
          <WidgetConcentration />
        </div>
      </ResponsiveGridLayout>
    </div>
  )
}
