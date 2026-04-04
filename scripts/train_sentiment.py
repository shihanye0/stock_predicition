"""
BERT金融情感分析模型微调脚本

使用chinese-bert-wwm-ext在金融情感数据上进行微调
"""
import os
import sys
import json
import random
from pathlib import Path

# 设置Hugging Face镜像
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from torch.optim import AdamW
from transformers import (
    AutoTokenizer, 
    AutoModelForSequenceClassification,
    get_linear_schedule_with_warmup
)
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from tqdm import tqdm

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from data.finance_sentiment_dataset import get_train_data, get_validation_data, get_label_map


class FinanceSentimentDataset(Dataset):
    """金融情感数据集"""
    
    def __init__(self, data, tokenizer, max_length=128):
        self.data = data
        self.tokenizer = tokenizer
        self.max_length = max_length
    
    def __len__(self):
        return len(self.data)
    
    def __getitem__(self, idx):
        text, label = self.data[idx]
        
        encoding = self.tokenizer(
            text,
            truncation=True,
            padding='max_length',
            max_length=self.max_length,
            return_tensors='pt'
        )
        
        return {
            'input_ids': encoding['input_ids'].squeeze(0),
            'attention_mask': encoding['attention_mask'].squeeze(0),
            'labels': torch.tensor(label, dtype=torch.long)
        }


class BertFineTuner:
    """BERT微调器"""
    
    def __init__(
        self,
        model_name: str = "hfl/chinese-bert-wwm-ext",
        num_labels: int = 3,
        max_length: int = 128,
        output_dir: str = "./output/sentiment_model"
    ):
        self.model_name = model_name
        self.num_labels = num_labels
        self.max_length = max_length
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"Using device: {self.device}")
        
        # 加载tokenizer和模型
        print(f"Loading model: {model_name}")
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(
            model_name,
            num_labels=num_labels
        )
        self.model.to(self.device)
        
        self.label_map = get_label_map()
        self.history = {"train_loss": [], "val_loss": [], "val_accuracy": []}
    
    def prepare_data(self, train_data, val_data, batch_size=16):
        """准备数据加载器"""
        # 数据增强：打乱训练数据
        train_data = list(train_data)
        random.shuffle(train_data)
        
        train_dataset = FinanceSentimentDataset(train_data, self.tokenizer, self.max_length)
        val_dataset = FinanceSentimentDataset(val_data, self.tokenizer, self.max_length)
        
        self.train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
        self.val_loader = DataLoader(val_dataset, batch_size=batch_size)
        
        print(f"Train samples: {len(train_dataset)}")
        print(f"Validation samples: {len(val_dataset)}")
    
    def train(
        self,
        epochs: int = 5,
        learning_rate: float = 2e-5,
        warmup_ratio: float = 0.1,
        weight_decay: float = 0.01
    ):
        """训练模型"""
        # 优化器
        optimizer = AdamW(
            self.model.parameters(),
            lr=learning_rate,
            weight_decay=weight_decay
        )
        
        # 学习率调度器
        total_steps = len(self.train_loader) * epochs
        warmup_steps = int(total_steps * warmup_ratio)
        scheduler = get_linear_schedule_with_warmup(
            optimizer,
            num_warmup_steps=warmup_steps,
            num_training_steps=total_steps
        )
        
        best_accuracy = 0
        
        for epoch in range(epochs):
            print(f"\n{'='*50}")
            print(f"Epoch {epoch + 1}/{epochs}")
            print(f"{'='*50}")
            
            # 训练阶段
            self.model.train()
            total_loss = 0
            
            progress_bar = tqdm(self.train_loader, desc="Training")
            for batch in progress_bar:
                optimizer.zero_grad()
                
                input_ids = batch['input_ids'].to(self.device)
                attention_mask = batch['attention_mask'].to(self.device)
                labels = batch['labels'].to(self.device)
                
                outputs = self.model(
                    input_ids=input_ids,
                    attention_mask=attention_mask,
                    labels=labels
                )
                
                loss = outputs.loss
                total_loss += loss.item()
                
                loss.backward()
                torch.nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)
                optimizer.step()
                scheduler.step()
                
                progress_bar.set_postfix({'loss': f'{loss.item():.4f}'})
            
            avg_train_loss = total_loss / len(self.train_loader)
            self.history["train_loss"].append(avg_train_loss)
            print(f"Average training loss: {avg_train_loss:.4f}")
            
            # 验证阶段
            val_loss, val_accuracy = self.evaluate()
            self.history["val_loss"].append(val_loss)
            self.history["val_accuracy"].append(val_accuracy)
            
            print(f"Validation loss: {val_loss:.4f}")
            print(f"Validation accuracy: {val_accuracy:.4f}")
            
            # 保存最佳模型
            if val_accuracy > best_accuracy:
                best_accuracy = val_accuracy
                self.save_model()
                print(f"New best model saved! Accuracy: {best_accuracy:.4f}")
        
        print(f"\n{'='*50}")
        print(f"Training completed! Best accuracy: {best_accuracy:.4f}")
        print(f"{'='*50}")
        
        return self.history
    
    def evaluate(self):
        """评估模型"""
        self.model.eval()
        total_loss = 0
        all_preds = []
        all_labels = []
        
        with torch.no_grad():
            for batch in self.val_loader:
                input_ids = batch['input_ids'].to(self.device)
                attention_mask = batch['attention_mask'].to(self.device)
                labels = batch['labels'].to(self.device)
                
                outputs = self.model(
                    input_ids=input_ids,
                    attention_mask=attention_mask,
                    labels=labels
                )
                
                total_loss += outputs.loss.item()
                
                preds = torch.argmax(outputs.logits, dim=1)
                all_preds.extend(preds.cpu().numpy())
                all_labels.extend(labels.cpu().numpy())
        
        avg_loss = total_loss / len(self.val_loader)
        accuracy = accuracy_score(all_labels, all_preds)
        
        return avg_loss, accuracy
    
    def detailed_evaluation(self):
        """详细评估"""
        self.model.eval()
        all_preds = []
        all_labels = []
        
        with torch.no_grad():
            for batch in self.val_loader:
                input_ids = batch['input_ids'].to(self.device)
                attention_mask = batch['attention_mask'].to(self.device)
                labels = batch['labels'].to(self.device)
                
                outputs = self.model(input_ids=input_ids, attention_mask=attention_mask)
                preds = torch.argmax(outputs.logits, dim=1)
                
                all_preds.extend(preds.cpu().numpy())
                all_labels.extend(labels.cpu().numpy())
        
        # 分类报告
        target_names = [self.label_map[i] for i in range(self.num_labels)]
        report = classification_report(all_labels, all_preds, target_names=target_names)
        
        # 混淆矩阵
        cm = confusion_matrix(all_labels, all_preds)
        
        print("\n分类报告:")
        print(report)
        print("\n混淆矩阵:")
        print(cm)
        
        return report, cm
    
    def save_model(self):
        """保存模型"""
        self.model.save_pretrained(self.output_dir)
        self.tokenizer.save_pretrained(self.output_dir)
        
        # 保存配置
        config = {
            "model_name": self.model_name,
            "num_labels": self.num_labels,
            "max_length": self.max_length,
            "label_map": self.label_map
        }
        with open(self.output_dir / "config.json", "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    
    def predict(self, texts):
        """预测"""
        self.model.eval()
        results = []
        
        for text in texts:
            encoding = self.tokenizer(
                text,
                truncation=True,
                padding='max_length',
                max_length=self.max_length,
                return_tensors='pt'
            )
            
            input_ids = encoding['input_ids'].to(self.device)
            attention_mask = encoding['attention_mask'].to(self.device)
            
            with torch.no_grad():
                outputs = self.model(input_ids=input_ids, attention_mask=attention_mask)
                probs = torch.softmax(outputs.logits, dim=1)
                pred = torch.argmax(probs, dim=1).item()
                confidence = probs[0][pred].item()
            
            results.append({
                "text": text,
                "label": self.label_map[pred],
                "confidence": confidence,
                "scores": {
                    self.label_map[i]: probs[0][i].item() 
                    for i in range(self.num_labels)
                }
            })
        
        return results


def main():
    """主函数"""
    print("="*60)
    print("BERT金融情感分析模型微调")
    print("="*60)
    
    # 配置
    MODEL_NAME = "hfl/chinese-bert-wwm-ext"
    OUTPUT_DIR = "./backend/data/models/sentiment_model"
    EPOCHS = 5
    BATCH_SIZE = 16
    LEARNING_RATE = 2e-5
    
    # 获取数据
    train_data = get_train_data()
    val_data = get_validation_data()
    
    print(f"\n数据集统计:")
    print(f"- 训练样本: {len(train_data)}")
    print(f"- 验证样本: {len(val_data)}")
    
    # 创建微调器
    tuner = BertFineTuner(
        model_name=MODEL_NAME,
        num_labels=3,
        max_length=128,
        output_dir=OUTPUT_DIR
    )
    
    # 准备数据
    tuner.prepare_data(train_data, val_data, batch_size=BATCH_SIZE)
    
    # 训练
    history = tuner.train(
        epochs=EPOCHS,
        learning_rate=LEARNING_RATE
    )
    
    # 详细评估
    tuner.detailed_evaluation()
    
    # 测试预测
    print("\n" + "="*60)
    print("测试预测")
    print("="*60)
    
    test_texts = [
        "这只股票太牛了，继续加仓",
        "业绩暴雷，赶紧跑",
        "继续观望，等信号",
        "涨停板封单很大",
        "跌破支撑位了"
    ]
    
    results = tuner.predict(test_texts)
    for r in results:
        print(f"\n文本: {r['text']}")
        print(f"预测: {r['label']} (置信度: {r['confidence']:.4f})")
    
    print(f"\n模型已保存到: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
