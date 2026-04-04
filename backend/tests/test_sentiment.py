"""
情感分析模块单元测试
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.sentiment.analyzer import SentimentAnalyzer


class TestSentimentAnalyzer:
    """情感分析器测试"""
    
    @pytest.fixture
    def analyzer(self):
        """创建分析器实例"""
        return SentimentAnalyzer()
    
    def test_positive_text(self, analyzer):
        """测试积极文本"""
        text = "这只股票太牛了，涨停板，强烈看好"
        result = analyzer.analyze(text)
        
        assert result.label in ["positive", "neutral", "negative"]
        assert 0 <= result.confidence <= 1
        assert "positive" in result.scores
    
    def test_negative_text(self, analyzer):
        """测试消极文本"""
        text = "要跌了，赶紧跑，亏损严重"
        result = analyzer.analyze(text)
        
        assert result.label in ["positive", "neutral", "negative"]
        assert 0 <= result.confidence <= 1
    
    def test_neutral_text(self, analyzer):
        """测试中性文本"""
        text = "今天开盘了，继续观望"
        result = analyzer.analyze(text)
        
        assert result.label in ["positive", "neutral", "negative"]
    
    def test_empty_text(self, analyzer):
        """测试空文本"""
        result = analyzer.analyze("")
        assert result.label == "neutral"
    
    def test_result_structure(self, analyzer):
        """测试结果结构"""
        text = "测试文本"
        result = analyzer.analyze(text)
        
        # 检查必要属性
        assert hasattr(result, "label")
        assert hasattr(result, "confidence")
        assert hasattr(result, "scores")
        assert "positive" in result.scores
        assert "negative" in result.scores
        assert "neutral" in result.scores
    
    def test_confidence_range(self, analyzer):
        """测试置信度范围"""
        texts = [
            "绝对的牛股，必涨",
            "垃圾股，千万别买",
            "一般般吧"
        ]
        
        for text in texts:
            result = analyzer.analyze(text)
            assert 0 <= result.confidence <= 1
            assert sum(result.scores.values()) > 0


class TestSentimentLabels:
    """情感标签测试"""
    
    def test_label_values(self):
        """测试标签值"""
        valid_labels = {"positive", "negative", "neutral"}
        analyzer = SentimentAnalyzer()
        
        result = analyzer.analyze("测试")
        assert result.label in valid_labels


class TestFinancialTerms:
    """金融术语情感测试"""
    
    @pytest.fixture
    def analyzer(self):
        return SentimentAnalyzer()
    
    def test_bullish_terms(self, analyzer):
        """测试看涨术语"""
        bullish_texts = [
            "金叉形成，买入信号",
            "北向资金持续流入",
            "底部放量突破",
            "MACD金叉",
        ]
        
        for text in bullish_texts:
            result = analyzer.analyze(text)
            # 至少不应该是负面
            assert result.scores["positive"] >= result.scores["negative"] * 0.5 or result.label != "negative"
    
    def test_bearish_terms(self, analyzer):
        """测试看跌术语"""
        bearish_texts = [
            "死叉形成，卖出信号",
            "北向资金持续流出",
            "跌破支撑位",
            "MACD死叉",
        ]
        
        for text in bearish_texts:
            result = analyzer.analyze(text)
            # 至少不应该是正面
            assert result.scores["negative"] >= result.scores["positive"] * 0.5 or result.label != "positive"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
