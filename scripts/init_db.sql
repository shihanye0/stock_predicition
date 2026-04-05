-- 基于Transformer的股票情绪预测系统 - 数据库初始化脚本
-- MySQL 8.0+

-- 创建数据库
CREATE DATABASE IF NOT EXISTS stock_sentiment
DEFAULT CHARACTER SET utf8mb4
DEFAULT COLLATE utf8mb4_unicode_ci;

USE stock_sentiment;

-- 股票信息表
CREATE TABLE IF NOT EXISTS stocks (
    stock_code VARCHAR(10) PRIMARY KEY COMMENT '股票代码',
    stock_name VARCHAR(50) NOT NULL COMMENT '股票名称',
    industry VARCHAR(50) COMMENT '所属行业',
    market VARCHAR(10) COMMENT '市场(SH/SZ)',
    list_date DATE COMMENT '上市日期',
    status TINYINT DEFAULT 1 COMMENT '状态:1正常0退市',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_industry (industry),
    INDEX idx_market (market)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='股票信息表';

-- 评论数据表
CREATE TABLE IF NOT EXISTS comments (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    comment_id VARCHAR(64) UNIQUE NOT NULL COMMENT '评论唯一ID',
    platform VARCHAR(20) NOT NULL COMMENT '来源平台',
    stock_code VARCHAR(10) NOT NULL COMMENT '股票代码',
    content TEXT NOT NULL COMMENT '评论内容',
    content_clean TEXT COMMENT '清洗后内容',
    author VARCHAR(100) COMMENT '作者',
    publish_time DATETIME NOT NULL COMMENT '发布时间',
    likes INT DEFAULT 0 COMMENT '点赞数',
    replies INT DEFAULT 0 COMMENT '回复数',
    crawl_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '采集时间',
    is_processed TINYINT DEFAULT 0 COMMENT '是否已处理',
    INDEX idx_stock_code (stock_code),
    INDEX idx_platform (platform),
    INDEX idx_publish_time (publish_time),
    INDEX idx_is_processed (is_processed),
    FOREIGN KEY (stock_code) REFERENCES stocks(stock_code) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='评论数据表';

-- 情感分析结果表
CREATE TABLE IF NOT EXISTS sentiments (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    comment_id VARCHAR(64) UNIQUE NOT NULL COMMENT '评论ID',
    label VARCHAR(20) NOT NULL COMMENT '情感标签',
    confidence DECIMAL(5,4) NOT NULL COMMENT '置信度',
    positive_score DECIMAL(5,4) COMMENT '积极得分',
    neutral_score DECIMAL(5,4) COMMENT '中性得分',
    negative_score DECIMAL(5,4) COMMENT '消极得分',
    model_version VARCHAR(50) COMMENT '模型版本',
    analyzed_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '分析时间',
    INDEX idx_label (label),
    INDEX idx_analyzed_at (analyzed_at),
    FOREIGN KEY (comment_id) REFERENCES comments(comment_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='情感分析结果表';

-- 情绪指标表
CREATE TABLE IF NOT EXISTS emotions (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    stock_code VARCHAR(10) NOT NULL COMMENT '股票代码',
    stat_date DATE NOT NULL COMMENT '统计日期',
    stat_hour TINYINT COMMENT '统计小时(0-23,NULL表示日级)',
    total_count INT DEFAULT 0 COMMENT '总评论数',
    positive_count INT DEFAULT 0 COMMENT '积极评论数',
    neutral_count INT DEFAULT 0 COMMENT '中性评论数',
    negative_count INT DEFAULT 0 COMMENT '消极评论数',
    bull_index DECIMAL(5,2) COMMENT '看涨指数',
    bear_index DECIMAL(5,2) COMMENT '看跌指数',
    intensity DECIMAL(5,4) COMMENT '情绪强度',
    temperature DECIMAL(5,2) COMMENT '情绪温度',
    volatility DECIMAL(5,4) COMMENT '情绪波动',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_stock_date_hour (stock_code, stat_date, stat_hour),
    INDEX idx_stat_date (stat_date),
    FOREIGN KEY (stock_code) REFERENCES stocks(stock_code) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='情绪指标表';

-- 股票行情表
CREATE TABLE IF NOT EXISTS quotes (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    stock_code VARCHAR(10) NOT NULL COMMENT '股票代码',
    trade_date DATE NOT NULL COMMENT '交易日期',
    open_price DECIMAL(10,2) COMMENT '开盘价',
    close_price DECIMAL(10,2) COMMENT '收盘价',
    high_price DECIMAL(10,2) COMMENT '最高价',
    low_price DECIMAL(10,2) COMMENT '最低价',
    pre_close DECIMAL(10,2) COMMENT '昨收价',
    change_amount DECIMAL(10,2) COMMENT '涨跌额',
    change_pct DECIMAL(8,4) COMMENT '涨跌幅(%)',
    volume BIGINT COMMENT '成交量(手)',
    amount DECIMAL(18,2) COMMENT '成交额(元)',
    turnover_rate DECIMAL(8,4) COMMENT '换手率(%)',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_stock_date (stock_code, trade_date),
    INDEX idx_trade_date (trade_date),
    FOREIGN KEY (stock_code) REFERENCES stocks(stock_code) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='股票行情表';

-- 用户表
CREATE TABLE IF NOT EXISTS users (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL COMMENT '用户名',
    email VARCHAR(100) UNIQUE COMMENT '邮箱',
    hashed_password VARCHAR(255) NOT NULL COMMENT '密码哈希',
    nickname VARCHAR(50) COMMENT '昵称',
    avatar VARCHAR(255) COMMENT '头像URL',
    role VARCHAR(20) DEFAULT 'user' COMMENT '角色:admin/user',
    is_active TINYINT DEFAULT 1 COMMENT '是否激活',
    last_login DATETIME COMMENT '最后登录时间',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_email (email),
    INDEX idx_role (role)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';

-- 用户关注股票表
CREATE TABLE IF NOT EXISTS user_watchlist (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL COMMENT '用户ID',
    stock_code VARCHAR(10) NOT NULL COMMENT '股票代码',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_user_stock (user_id, stock_code),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (stock_code) REFERENCES stocks(stock_code) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户关注股票表';

-- 实验结果表
CREATE TABLE IF NOT EXISTS experiment_results (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    model_name VARCHAR(100) NOT NULL COMMENT '模型名称',
    dataset_name VARCHAR(100) NOT NULL COMMENT '数据集名称',
    accuracy FLOAT COMMENT '准确率',
    f1_score FLOAT COMMENT 'F1分数',
    precision_score FLOAT COMMENT '精确率',
    recall_score FLOAT COMMENT '召回率',
    confusion_matrix JSON COMMENT '混淆矩阵',
    classification_report JSON COMMENT '分类报告',
    run_time FLOAT COMMENT '运行耗时(秒)',
    sample_count INT COMMENT '样本数量',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_model_name (model_name),
    INDEX idx_created_at_exp (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='实验结果表';

-- 方面级情感分析表
CREATE TABLE IF NOT EXISTS aspect_sentiments (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    comment_id VARCHAR(64) NOT NULL COMMENT '评论ID',
    aspect VARCHAR(30) NOT NULL COMMENT '方面类别',
    sentiment_label VARCHAR(20) NOT NULL COMMENT '情感标签',
    confidence DECIMAL(5,4) COMMENT '置信度',
    keywords VARCHAR(500) COMMENT '匹配关键词',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_comment_aspect (comment_id, aspect),
    INDEX idx_aspect (aspect),
    FOREIGN KEY (comment_id) REFERENCES comments(comment_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='方面级情感分析表';

-- 情绪预警表
CREATE TABLE IF NOT EXISTS alerts (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    stock_code VARCHAR(10) NOT NULL COMMENT '股票代码',
    alert_type VARCHAR(50) NOT NULL COMMENT '预警类型',
    severity VARCHAR(10) NOT NULL COMMENT '严重程度:high/medium/low',
    title VARCHAR(200) NOT NULL COMMENT '预警标题',
    message TEXT COMMENT '预警详情',
    metric_value FLOAT COMMENT '触发指标值',
    threshold FLOAT COMMENT '阈值',
    triggered_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '触发时间',
    is_read TINYINT DEFAULT 0 COMMENT '是否已读',
    INDEX idx_stock_alert (stock_code),
    INDEX idx_severity (severity),
    INDEX idx_is_read (is_read),
    INDEX idx_triggered_at (triggered_at),
    FOREIGN KEY (stock_code) REFERENCES stocks(stock_code) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='情绪预警表';

-- 插入示例股票数据
INSERT INTO stocks (stock_code, stock_name, market, industry) VALUES
('000001', '平安银行', 'SZ', '银行'),
('000002', '万科A', 'SZ', '房地产'),
('600036', '招商银行', 'SH', '银行'),
('600519', '贵州茅台', 'SH', '白酒'),
('000651', '格力电器', 'SZ', '家电'),
('300750', '宁德时代', 'SZ', '新能源'),
('002475', '立讯精密', 'SZ', '电子'),
('600276', '恒瑞医药', 'SH', '医药'),
('601318', '中国平安', 'SH', '保险'),
('000858', '五粮液', 'SZ', '白酒')
ON DUPLICATE KEY UPDATE stock_name = VALUES(stock_name);

SELECT 'Database initialized successfully!' AS message;
