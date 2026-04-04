"""
基于BERT的情感分析器
"""
import os
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from loguru import logger

# 延迟导入torch和transformers
torch = None
F = None
AutoTokenizer = None
AutoModelForSequenceClassification = None

def _load_ml_libs():
    global torch, F, AutoTokenizer, AutoModelForSequenceClassification
    if torch is None:
        try:
            import torch as _torch
            import torch.nn.functional as _F
            from transformers import AutoTokenizer as _AutoTokenizer
            from transformers import AutoModelForSequenceClassification as _AutoModel
            torch = _torch
            F = _F
            AutoTokenizer = _AutoTokenizer
            AutoModelForSequenceClassification = _AutoModel
            return True
        except ImportError as e:
            logger.warning(f"ML libraries not available: {e}")
            return False
    return True

from app.core.config import settings
from app.models.schemas import SentimentResult
from app.services.processor.text_processor import get_processor


@dataclass
class SentimentConfig:
    """情感分析配置"""
    model_name: str = "hfl/chinese-bert-wwm-ext"
    max_length: int = 128
    num_labels: int = 3
    label_map: Dict[int, str] = None
    device: str = "cpu"
    
    def __post_init__(self):
        if self.label_map is None:
            self.label_map = {
                0: "negative",
                1: "neutral", 
                2: "positive"
            }
        # 检测设备
        if _load_ml_libs() and torch is not None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"


class SentimentAnalyzer:
    """
    基于BERT的情感分析器
    
    支持三分类：积极(positive)、中性(neutral)、消极(negative)
    """
    
    def __init__(self, config: Optional[SentimentConfig] = None):
        self.config = config or SentimentConfig(
            model_name=settings.MODEL_NAME,
            max_length=settings.MODEL_MAX_LENGTH
        )
        
        self.tokenizer = None
        self.model = None
        self.is_loaded = False
        self.total_analyzed = 0
        
        # 文本处理器
        self.text_processor = get_processor()
        
        # 加载模型
        self._load_model()
    
    @property
    def model_name(self) -> str:
        return self.config.model_name
    
    def _load_model(self):
        """加载预训练模型"""
        # 检查是否可以导入必要的库
        if not _load_ml_libs():
            logger.warning("ML libraries not available, using mock model")
            self.is_loaded = False
            return
        
        try:
            logger.info(f"Loading model: {self.config.model_name}")
            
            # 检查多个可能的本地模型路径
            possible_paths = [
                os.path.join(settings.MODEL_CACHE_DIR, "sentiment_model"),
                os.path.join(os.path.dirname(__file__), "../../data/models/sentiment_model"),
                "./backend/data/models/sentiment_model",
                "./data/models/sentiment_model",
            ]
            
            local_model_path = None
            for path in possible_paths:
                abs_path = os.path.abspath(path)
                if os.path.exists(abs_path) and os.path.isdir(abs_path):
                    # 检查是否包含模型文件
                    if os.path.exists(os.path.join(abs_path, "config.json")):
                        local_model_path = abs_path
                        break
            
            if local_model_path:
                logger.info(f"Loading local fine-tuned model from {local_model_path}")
                self.tokenizer = AutoTokenizer.from_pretrained(local_model_path, local_files_only=True)
                self.model = AutoModelForSequenceClassification.from_pretrained(local_model_path, local_files_only=True)
            else:
                # 加载预训练模型（需要网络）
                logger.info(f"Loading pre-trained model: {self.config.model_name}")
                self.tokenizer = AutoTokenizer.from_pretrained(self.config.model_name)
                self.model = AutoModelForSequenceClassification.from_pretrained(
                    self.config.model_name,
                    num_labels=self.config.num_labels
                )
            
            # 移动到指定设备
            self.model.to(self.config.device)
            self.model.eval()
            
            self.is_loaded = True
            logger.info(f"Model loaded successfully on {self.config.device}")
            
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            self.is_loaded = False
    
    def _preprocess(self, text: str) -> str:
        """预处理文本"""
        # 使用文本处理器清洗
        cleaned = self.text_processor.clean(text)
        
        # 截断过长文本
        if len(cleaned) > self.config.max_length * 2:
            cleaned = cleaned[:self.config.max_length * 2]
        
        return cleaned
    
    def _predict(self, texts: List[str]) -> List[Tuple[int, float, Dict[str, float]]]:
        """
        批量预测
        
        Returns:
            List of (label_id, confidence, scores_dict)
        """
        if not self.is_loaded:
            # 如果模型未加载，返回模拟结果
            results = []
            for text in texts:
                # 简单的模拟逻辑：根据文本内容决定情感
                import random
                text_lower = text.lower()
                if any(w in text_lower for w in ['涨', '涨停', '利好', '买', '看涨', '大涨', '突破', '强势']):
                    label_id = 2  # positive
                    confidence = random.uniform(0.6, 0.9)
                elif any(w in text_lower for w in ['跌', '跌停', '利空', '卖', '看跌', '大跌', '破位', '弱势']):
                    label_id = 0  # negative
                    confidence = random.uniform(0.6, 0.9)
                else:
                    label_id = 1  # neutral
                    confidence = random.uniform(0.5, 0.7)
                
                scores = {
                    self.config.label_map[0]: 0.1 if label_id != 0 else confidence,
                    self.config.label_map[1]: 0.1 if label_id != 1 else confidence,
                    self.config.label_map[2]: 0.1 if label_id != 2 else confidence,
                }
                results.append((label_id, confidence, scores))
            return results
        
        results = []
        
        # 编码
        encodings = self.tokenizer(
            texts,
            padding=True,
            truncation=True,
            max_length=self.config.max_length,
            return_tensors="pt"
        )
        
        # 移动到设备
        input_ids = encodings["input_ids"].to(self.config.device)
        attention_mask = encodings["attention_mask"].to(self.config.device)
        
        # 推理
        with torch.no_grad():
            outputs = self.model(input_ids=input_ids, attention_mask=attention_mask)
            logits = outputs.logits
            
            # 计算概率
            probs = F.softmax(logits, dim=-1)
            
            for i in range(len(texts)):
                prob = probs[i].cpu().numpy()
                label_id = int(prob.argmax())
                confidence = float(prob.max())
                
                scores = {
                    self.config.label_map[j]: float(prob[j])
                    for j in range(len(prob))
                }
                
                results.append((label_id, confidence, scores))
        
        return results
    
    def analyze(self, text: str) -> SentimentResult:
        """
        分析单条文本的情感
        
        Args:
            text: 输入文本
            
        Returns:
            SentimentResult对象
        """
        if not text:
            return SentimentResult(
                text=text,
                label="neutral",
                confidence=1.0,
                scores={"positive": 0.0, "neutral": 1.0, "negative": 0.0}
            )
        
        # 预处理
        cleaned_text = self._preprocess(text)
        
        if not cleaned_text:
            return SentimentResult(
                text=text,
                label="neutral",
                confidence=1.0,
                scores={"positive": 0.0, "neutral": 1.0, "negative": 0.0}
            )
        
        # 预测
        try:
            results = self._predict([cleaned_text])
            label_id, confidence, scores = results[0]
            label = self.config.label_map[label_id]
            
            self.total_analyzed += 1
            
            return SentimentResult(
                text=text,
                label=label,
                confidence=confidence,
                scores=scores
            )
            
        except Exception as e:
            logger.error(f"Sentiment analysis error: {e}")
            return SentimentResult(
                text=text,
                label="neutral",
                confidence=0.0,
                scores={"positive": 0.0, "neutral": 1.0, "negative": 0.0}
            )
    
    def analyze_batch(self, texts: List[str], batch_size: int = 32) -> List[SentimentResult]:
        """
        批量分析文本情感
        
        Args:
            texts: 文本列表
            batch_size: 批量大小
            
        Returns:
            SentimentResult对象列表
        """
        if not texts:
            return []
        
        results = []
        
        # 预处理所有文本
        cleaned_texts = [self._preprocess(t) for t in texts]
        
        # 分批处理
        for i in range(0, len(cleaned_texts), batch_size):
            batch_texts = cleaned_texts[i:i + batch_size]
            original_texts = texts[i:i + batch_size]
            
            # 过滤空文本
            valid_indices = [j for j, t in enumerate(batch_texts) if t]
            valid_texts = [batch_texts[j] for j in valid_indices]
            
            if valid_texts:
                try:
                    predictions = self._predict(valid_texts)
                    
                    # 构建结果
                    pred_idx = 0
                    for j in range(len(batch_texts)):
                        if j in valid_indices:
                            label_id, confidence, scores = predictions[pred_idx]
                            label = self.config.label_map[label_id]
                            pred_idx += 1
                        else:
                            label = "neutral"
                            confidence = 1.0
                            scores = {"positive": 0.0, "neutral": 1.0, "negative": 0.0}
                        
                        results.append(SentimentResult(
                            text=original_texts[j],
                            label=label,
                            confidence=confidence,
                            scores=scores
                        ))
                        
                except Exception as e:
                    logger.error(f"Batch analysis error: {e}")
                    for j in range(len(batch_texts)):
                        results.append(SentimentResult(
                            text=original_texts[j],
                            label="neutral",
                            confidence=0.0,
                            scores={"positive": 0.0, "neutral": 1.0, "negative": 0.0}
                        ))
            else:
                for j in range(len(batch_texts)):
                    results.append(SentimentResult(
                        text=original_texts[j],
                        label="neutral",
                        confidence=1.0,
                        scores={"positive": 0.0, "neutral": 1.0, "negative": 0.0}
                    ))
        
        self.total_analyzed += len(texts)
        return results
    
    def save_model(self, path: str):
        """保存模型"""
        if self.model and self.tokenizer:
            os.makedirs(path, exist_ok=True)
            self.model.save_pretrained(path)
            self.tokenizer.save_pretrained(path)
            logger.info(f"Model saved to {path}")


# 全局分析器实例
_analyzer: Optional[SentimentAnalyzer] = None


def get_analyzer() -> SentimentAnalyzer:
    """获取情感分析器单例"""
    global _analyzer
    if _analyzer is None:
        _analyzer = SentimentAnalyzer()
    return _analyzer
