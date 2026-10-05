import {
  BarElement, CategoryScale, Chart, Filler, Legend, LinearScale, LineElement, PointElement, Tooltip,
} from 'chart.js'
import { cssVar, fmtDate } from '../utils/format'

Chart.register(CategoryScale, LinearScale, LineElement, PointElement, BarElement, Filler, Tooltip, Legend)

/** Shared, recessive chart styling read from the CSS theme tokens. */
export function baseOptions({ yFormat = (v) => v, legend = false } = {}) {
  const ink2 = cssVar('--ink-2')
  const ink3 = cssVar('--ink-3')
  const grid = cssVar('--border')
  Chart.defaults.font.family = 'Inter, ui-sans-serif, system-ui, sans-serif'
  return {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    interaction: { mode: 'index', intersect: false },
    plugins: {
      legend: legend
        ? { position: 'top', align: 'start', labels: { color: ink2, boxWidth: 12, boxHeight: 2, font: { size: 11 } } }
        : { display: false },
      tooltip: {
        backgroundColor: cssVar('--surface'),
        titleColor: cssVar('--ink'),
        bodyColor: ink2,
        borderColor: grid,
        borderWidth: 1,
        padding: 8,
        callbacks: { title: (items) => fmtDate(items[0].label, { weekday: 'short', day: 'numeric', month: 'short', year: 'numeric' }) },
      },
    },
    scales: {
      x: {
        grid: { display: false },
        border: { color: grid },
        ticks: {
          color: ink3, maxRotation: 0, autoSkip: true, maxTicksLimit: 5, font: { size: 10 },
          callback(value) { return fmtDate(this.getLabelForValue(value), { day: 'numeric', month: 'short' }) },
        },
      },
      y: {
        grid: { color: grid, drawTicks: false },
        border: { display: false },
        ticks: { color: ink3, font: { size: 10 }, padding: 6, maxTicksLimit: 5, callback: yFormat },
      },
    },
  }
}
