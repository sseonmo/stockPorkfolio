import { SectorPieChart } from './SectorPieChart'

export function WidgetSectorPie() {
  // SectorPieChart already has Card internally, so we just use it directly
  // or modify SectorPieChart to accept className and not render Card internally.
  // For now, let's wrap it or modify it. 
  // SectorPieChart renders a Card with fixed height 500px. We need it to fill the parent.
  
  return (
    <div className="h-full w-full">
      <SectorPieChart />
    </div>
  )
}
