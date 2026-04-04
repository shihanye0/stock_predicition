"""
方面级情感分析器

基于关键词规则提取评论中讨论的具体方面（业绩、政策、技术面、资金面、行业），
并对每个方面独立计算情感得分。
"""
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from loguru import logger

from app.services.sentiment.lexicon import get_lexicon
from app.services.processor.text_processor import get_processor


# 方面关键词词典
ASPECT_KEYWORDS = {
    "业绩": {
        "keywords": [
            "营收", "利润", "净利", "毛利", "业绩", "财报", "年报", "季报", "中报",
            "盈利", "亏损", "营业收入", "增收", "同比", "环比", "归母净利", "扣非",
            "ROE", "ROA", "EPS", "每股收益", "分红", "派息", "股息", "现金流",
            "市盈率", "PE", "PB", "估值", "收入增长", "利润率"
        ],
        "positive_keywords": ["增长", "超预期", "盈利", "增收增利", "扭亏", "新高", "翻倍"],
        "negative_keywords": ["下滑", "亏损", "不及预期", "下降", "缩水", "暴跌", "腰斩"]
    },
    "政策": {
        "keywords": [
            "政策", "监管", "央行", "降准", "降息", "加息", "MLF", "LPR", "利率",
            "证监会", "银保监", "国资委", "发改委", "财政部", "国务院", "两会",
            "改革", "补贴", "税收", "关税", "制裁", "反垄断", "IPO", "注册制",
            "减持", "增持", "回购", "限售", "解禁", "融资", "再融资"
        ],
        "positive_keywords": ["利好", "支持", "扶持", "放开", "降息", "降准", "补贴", "鼓励"],
        "negative_keywords": ["利空", "限制", "收紧", "加息", "制裁", "处罚", "叫停", "约谈"]
    },
    "技术面": {
        "keywords": [
            "均线", "MACD", "KDJ", "RSI", "布林", "支撑", "压力", "阻力",
            "突破", "跌破", "金叉", "死叉", "放量", "缩量", "十字星", "长阳",
            "长阴", "头肩", "双底", "双顶", "三角形", "箱体", "缺口", "回调",
            "反弹", "趋势", "K线", "技术指标", "量价", "背离", "超买", "超卖"
        ],
        "positive_keywords": ["突破", "金叉", "放量", "反弹", "企稳", "长阳", "支撑"],
        "negative_keywords": ["跌破", "死叉", "缩量", "回调", "长阴", "破位", "背离"]
    },
    "资金面": {
        "keywords": [
            "主力", "庄家", "大单", "资金流", "北向", "外资", "融资", "融券",
            "大宗交易", "换手", "换手率", "成交量", "成交额", "净买入", "净卖出",
            "龙虎榜", "游资", "机构", "社保", "基金", "QFII", "筹码", "集中度",
            "抄底", "出货", "吸筹", "洗盘", "拉升", "套牢", "解套"
        ],
        "positive_keywords": ["流入", "净买入", "抄底", "加仓", "增持", "吸筹", "拉升"],
        "negative_keywords": ["流出", "净卖出", "出货", "减持", "套牢", "割肉", "清仓"]
    },
    "行业": {
        "keywords": [
            "行业", "板块", "赛道", "产业", "龙头", "竞争", "市场份额", "景气度",
            "新能源", "半导体", "芯片", "AI", "人工智能", "消费", "医药", "白酒",
            "银行", "房地产", "互联网", "电商", "5G", "物联网", "碳中和", "光伏",
            "储能", "锂电", "新基建", "元宇宙", "数字经济", "智能制造"
        ],
        "positive_keywords": ["景气", "高增", "蓝海", "风口", "爆发", "龙头", "领先"],
        "negative_keywords": ["内卷", "红海", "萎缩", "过剩", "衰退", "淘汰", "下行"]
    }
}


@dataclass
class AspectResult:
    """单个方面的分析结果"""
    aspect: str
    sentiment_label: str  # positive/neutral/negative
    confidence: float
    keywords: List[str] = field(default_factory=list)
    score: float = 0.0


@dataclass 
class AspectAnalysisResult:
    """完整的方面分析结果"""
    text: str
    aspects: List[AspectResult] = field(default_factory=list)
    dominant_aspect: Optional[str] = None  # 最突出的方面


class AspectSentimentAnalyzer:
    """
    方面级情感分析器
    
    分析流程：
    1. 分词
    2. 关键词匹配识别讨论方面
    3. 针对每个方面提取上下文
    4. 计算方面级情感得分
    """
    
    def __init__(self):
        self.processor = get_processor()
        self.lexicon = get_lexicon()
        self.aspect_keywords = ASPECT_KEYWORDS
    
    def analyze(self, text: str) -> AspectAnalysisResult:
        """
        分析单条文本的方面级情感
        
        Args:
            text: 输入文本
            
        Returns:
            AspectAnalysisResult
        """
        if not text or len(text.strip()) < 2:
            return AspectAnalysisResult(text=text)
        
        cleaned = self.processor.clean(text)
        words = self.processor.tokenize(cleaned)
        
        aspects = []
        max_score = 0
        dominant = None
        
        for aspect_name, config in self.aspect_keywords.items():
            matched_keywords = []
            
            # 检查通用关键词
            for kw in config["keywords"]:
                if kw in cleaned:
                    matched_keywords.append(kw)
            
            if not matched_keywords:
                continue
            
            # 计算方面级情感
            pos_hits = 0
            neg_hits = 0
            pos_kw = []
            neg_kw = []
            
            for kw in config.get("positive_keywords", []):
                if kw in cleaned:
                    pos_hits += 1
                    pos_kw.append(kw)
            
            for kw in config.get("negative_keywords", []):
                if kw in cleaned:
                    neg_hits += 1
                    neg_kw.append(kw)
            
            # 结合词典分析
            lexicon_result = self.lexicon.analyze_text(words)
            lexicon_score = lexicon_result['score']
            
            # 综合打分
            aspect_score = (pos_hits - neg_hits) * 0.6 + lexicon_score * 0.4
            
            if aspect_score > 0.3:
                label = "positive"
                confidence = min(0.5 + pos_hits * 0.1 + abs(aspect_score) * 0.1, 0.95)
            elif aspect_score < -0.3:
                label = "negative"
                confidence = min(0.5 + neg_hits * 0.1 + abs(aspect_score) * 0.1, 0.95)
            else:
                label = "neutral"
                confidence = max(0.4, 0.7 - abs(aspect_score) * 0.2)
            
            all_keywords = matched_keywords + pos_kw + neg_kw
            unique_keywords = list(dict.fromkeys(all_keywords))[:10]
            
            aspect_result = AspectResult(
                aspect=aspect_name,
                sentiment_label=label,
                confidence=round(confidence, 4),
                keywords=unique_keywords,
                score=round(aspect_score, 4)
            )
            aspects.append(aspect_result)
            
            relevance = len(matched_keywords) + pos_hits + neg_hits
            if relevance > max_score:
                max_score = relevance
                dominant = aspect_name
        
        return AspectAnalysisResult(
            text=text,
            aspects=aspects,
            dominant_aspect=dominant
        )
    
    def analyze_batch(self, texts: List[str]) -> List[AspectAnalysisResult]:
        """批量分析"""
        return [self.analyze(t) for t in texts]
    
    def get_stock_aspect_summary(self, aspect_results: List[AspectAnalysisResult]) -> Dict:
        """
        汇总多条评论的方面级情感
        
        Args:
            aspect_results: 多条评论的方面分析结果
            
        Returns:
            按方面汇总的情感分布
        """
        summary = {}
        
        for result in aspect_results:
            for asp in result.aspects:
                name = asp.aspect
                if name not in summary:
                    summary[name] = {
                        "aspect": name,
                        "total": 0,
                        "positive": 0,
                        "neutral": 0,
                        "negative": 0,
                        "avg_score": 0.0,
                        "scores": [],
                        "top_keywords": {}
                    }
                
                summary[name]["total"] += 1
                summary[name][asp.sentiment_label] += 1
                summary[name]["scores"].append(asp.score)
                
                for kw in asp.keywords:
                    summary[name]["top_keywords"][kw] = summary[name]["top_keywords"].get(kw, 0) + 1
        
        # 计算平均得分和排序关键词
        for name, data in summary.items():
            if data["scores"]:
                data["avg_score"] = round(sum(data["scores"]) / len(data["scores"]), 4)
            del data["scores"]
            
            # 取top5关键词
            sorted_kw = sorted(data["top_keywords"].items(), key=lambda x: x[1], reverse=True)[:5]
            data["top_keywords"] = [{"keyword": k, "count": v} for k, v in sorted_kw]
            
            # 计算情感倾向
            total = data["total"]
            if total > 0:
                data["positive_ratio"] = round(data["positive"] / total, 4)
                data["negative_ratio"] = round(data["negative"] / total, 4)
        
        return summary


# 全局单例
_aspect_analyzer: Optional[AspectSentimentAnalyzer] = None


def get_aspect_analyzer() -> AspectSentimentAnalyzer:
    """获取方面级情感分析器单例"""
    global _aspect_analyzer
    if _aspect_analyzer is None:
        _aspect_analyzer = AspectSentimentAnalyzer()
    return _aspect_analyzer
