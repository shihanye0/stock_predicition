import request from './request'

// 股票相关API
export const stockApi = {
  // 获取股票列表
  getStocks(params) {
    return request.get('/v1/stocks', { params })
  },
  
  // 获取股票详情
  getStock(code) {
    return request.get(`/v1/stocks/${code}`)
  },
  
  // 获取股票评论
  getStockComments(code, params) {
    return request.get(`/v1/stocks/${code}/comments`, { params })
  },
  
  // 获取股票行情
  getStockQuotes(code, params) {
    return request.get(`/v1/stocks/${code}/quotes`, { params })
  },
  
  // 获取股票情绪
  getStockEmotion(code, params) {
    return request.get(`/v1/stocks/${code}/emotion`, { params })
  },
  
  // 获取股票方面级情感分析
  getStockAspects(code, params) {
    return request.get(`/v1/stocks/${code}/aspects`, { params })
  },
  
  // 获取股票情绪画像
  getStockProfile(code, params) {
    return request.get(`/v1/stocks/${code}/profile`, { params })
  }
}

// 情绪指标API
export const emotionApi = {
  // 获取市场情绪概览
  getOverview() {
    return request.get('/v1/emotion/overview')
  },
  
  // 获取情绪趋势
  getTrend(params) {
    return request.get('/v1/emotion/trend', { params })
  },
  
  // 获取情绪排行榜
  getRanking(params) {
    return request.get('/v1/emotion/ranking', { params })
  }
}

// 情感分析API
export const sentimentApi = {
  // 分析单条文本
  analyze(text) {
    return request.post('/v1/sentiment/analyze', { text })
  },
  
  // 批量分析
  batchAnalyze(texts) {
    return request.post('/v1/sentiment/batch', { texts })
  },
  
  // 获取分析统计
  getStats() {
    return request.get('/v1/sentiment/stats')
  }
}

// 市场验证API
export const validationApi = {
  // 获取相关性分析
  getCorrelation(params) {
    return request.get('/v1/validation/correlation', { params })
  },
  
  // 获取准确率分析
  getAccuracy(params) {
    return request.get('/v1/validation/accuracy', { params })
  },
  
  // 获取验证报告
  getReport(stockCode, params) {
    return request.get('/v1/validation/report', { params: { stock_code: stockCode, ...params } })
  }
}

// 爬虫管理API
export const crawlerApi = {
  // 启动爬虫
  start(data) {
    return request.post('/v1/crawler/start', data)
  },
  
  // 停止爬虫
  stop(platform) {
    return request.post('/v1/crawler/stop', null, { params: { platform } })
  },
  
  // 获取爬虫状态
  getStatus(platform) {
    return request.get('/v1/crawler/status', { params: { platform } })
  },
  
  // 获取爬虫统计
  getStats() {
    return request.get('/v1/crawler/stats')
  }
}

// 实验对比API
export const experimentApi = {
  // 多模型对比分析
  compare(text) {
    return request.post('/v1/experiment/compare', { text })
  },
  
  // 运行基准测试
  benchmark(data) {
    return request.post('/v1/experiment/benchmark', data)
  },
  
  // 获取历史实验结果
  getResults(params) {
    return request.get('/v1/experiment/results', { params })
  },
  
  // 获取模型性能指标
  getMetrics() {
    return request.get('/v1/experiment/metrics')
  },
  
  // 获取可用模型列表
  getModels() {
    return request.get('/v1/experiment/models')
  }
}

// 情绪预警API
export const alertApi = {
  // 获取预警列表
  getAlerts(params) {
    return request.get('/v1/alerts', { params })
  },

  // 标记已读
  markRead(alertId) {
    return request.put(`/v1/alerts/${alertId}/read`)
  },

  // 全部标记已读
  markAllRead(params) {
    return request.put('/v1/alerts/read-all', null, { params })
  },

  // 触发扫描
  scan(params) {
    return request.post('/v1/alerts/scan', null, { params })
  },

  // 预警统计
  getStats(params) {
    return request.get('/v1/alerts/stats', { params })
  }
}

// 管理员API
export const adminApi = {
  // 初始化演示数据
  initDemo() {
    return request.post('/v1/admin/init-demo')
  },

  // 获取数据状态
  getDataStatus() {
    return request.get('/v1/admin/data-status')
  },

  // 启动爬虫采集真实数据
  startCrawl(data) {
    return request.post('/v1/crawler/start', data)
  }
}
