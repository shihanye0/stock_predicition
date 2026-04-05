/**
 * ECharts深色主题配置工具
 * 所有图表共享同一套暗色风格
 */

// 深色主题公共配置
export const darkChartTheme = {
  backgroundColor: 'transparent',
  textStyle: {
    color: '#8b95a5'
  },
  title: {
    textStyle: { color: '#e8ecf1' },
    subtextStyle: { color: '#8b95a5' }
  },
  legend: {
    textStyle: { color: '#8b95a5' }
  },
  tooltip: {
    backgroundColor: 'rgba(26, 35, 50, 0.95)',
    borderColor: 'rgba(0, 212, 255, 0.2)',
    borderWidth: 1,
    textStyle: { color: '#e8ecf1' },
    extraCssText: 'box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4); border-radius: 8px; backdrop-filter: blur(8px);'
  },
  grid: {
    left: '3%',
    right: '4%',
    bottom: '3%',
    containLabel: true
  }
}

// 坐标轴公共配置
export const darkAxisStyle = {
  axisLine: { lineStyle: { color: 'rgba(255, 255, 255, 0.08)' } },
  axisTick: { lineStyle: { color: 'rgba(255, 255, 255, 0.08)' } },
  axisLabel: { color: '#8b95a5' },
  splitLine: { lineStyle: { color: 'rgba(255, 255, 255, 0.04)' } }
}

// 色板
export const chartColors = {
  bull: '#00e676',
  bear: '#ff5252',
  accent: '#00d4ff',
  neutral: '#ffab40',
  purple: '#ab47bc',
  teal: '#26c6da',
  pink: '#ec407a'
}

// 面积渐变生成器 (需要在组件中传入echarts实例)
export function makeAreaGradient(color, opacity1 = 0.25, opacity2 = 0.02) {
  return {
    type: 'linear',
    x: 0, y: 0, x2: 0, y2: 1,
    colorStops: [
      { offset: 0, color: color.replace(')', `, ${opacity1})`).replace('rgb', 'rgba').replace('#', '') },
      { offset: 1, color: color.replace(')', `, ${opacity2})`).replace('rgb', 'rgba').replace('#', '') }
    ]
  }
}

// 构建折线图系列
export function buildLineSeries(name, color, data, options = {}) {
  return {
    name,
    type: 'line',
    smooth: true,
    symbol: 'circle',
    symbolSize: 4,
    showSymbol: false,
    itemStyle: { color },
    lineStyle: { width: 2, color },
    areaStyle: options.area ? {
      color: {
        type: 'linear',
        x: 0, y: 0, x2: 0, y2: 1,
        colorStops: [
          { offset: 0, color: hexToRgba(color, 0.25) },
          { offset: 1, color: hexToRgba(color, 0.02) }
        ]
      }
    } : undefined,
    data,
    ...options
  }
}

// HEX转RGBA
function hexToRgba(hex, alpha) {
  const r = parseInt(hex.slice(1, 3), 16)
  const g = parseInt(hex.slice(3, 5), 16)
  const b = parseInt(hex.slice(5, 7), 16)
  return `rgba(${r}, ${g}, ${b}, ${alpha})`
}

// 饼图公共配置
export function buildPieOption(data, title) {
  return {
    ...darkChartTheme,
    tooltip: {
      ...darkChartTheme.tooltip,
      trigger: 'item',
      formatter: '{b}: {c} ({d}%)'
    },
    legend: {
      ...darkChartTheme.legend,
      bottom: '5%'
    },
    series: [{
      type: 'pie',
      radius: ['42%', '68%'],
      avoidLabelOverlap: false,
      itemStyle: {
        borderRadius: 6,
        borderColor: '#1a2332',
        borderWidth: 2
      },
      label: { show: false },
      data
    }]
  }
}

// 雷达图公共配置
export const darkRadarStyle = {
  axisName: { color: '#8b95a5' },
  splitArea: {
    areaStyle: {
      color: ['rgba(0, 212, 255, 0.02)', 'rgba(0, 212, 255, 0.04)']
    }
  },
  splitLine: {
    lineStyle: { color: 'rgba(255, 255, 255, 0.06)' }
  },
  axisLine: {
    lineStyle: { color: 'rgba(255, 255, 255, 0.08)' }
  }
}
