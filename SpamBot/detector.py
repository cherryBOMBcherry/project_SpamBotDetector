import os
import warnings
import asyncio
import numpy as np
import torch
import xgboost as xgb
from transformers import AutoModel, AutoTokenizer

warnings.filterwarnings("ignore")

class SpamDetector:
    def __init__(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        xgb_path = os.path.join(base_dir, "best_model", "spam_xgb_model.json")
        tokenizer_dir = os.path.join(base_dir, "best_model", "bert_tokenizer")
        model_dir = os.path.join(base_dir, "best_model", "bert_model")
        
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        self.xgb_model = xgb.Booster()
        self.xgb_model.load_model(xgb_path)
        
        self.tokenizer = AutoTokenizer.from_pretrained(tokenizer_dir)
        self.bert_model = AutoModel.from_pretrained(model_dir).to(self.device)
        self.bert_model.eval()
        
        self.max_len = 128
       
        self.lock = asyncio.Lock()
        print("модель ruModernBERT + XGBoost загружена")

    def _extract_embeddings(self, texts: list) -> np.ndarray:
        inputs = self.tokenizer(
            texts, 
            padding=True, 
            truncation=True, 
            max_length=self.max_len, 
            return_tensors="pt"
        ).to(self.device)
        
        with torch.inference_mode():
            outputs = self.bert_model(**inputs)
            
        return outputs.last_hidden_state[:, 0, :].cpu().numpy()

    def _sync_predict(self, message_text: str) -> float:
        
        if not message_text or not str(message_text).strip():
            return 0.0

        raw_text = str(message_text)
        embs = self._extract_embeddings([raw_text])
        
        dtrain = xgb.DMatrix(embs)
        prob = self.xgb_model.predict(dtrain)[0]
        
        print(f"[XGBoost] текст: '{raw_text[:50]}' -> вероятность спама: {prob:.4f}")
        return float(prob)

    async def is_spam_async(self, message_text: str) -> bool:
        
        async with self.lock:
            prob = await asyncio.to_thread(self._sync_predict, message_text)
        
        return prob >= 0.561