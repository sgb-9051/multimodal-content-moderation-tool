import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch.nn.functional as F


class HateSpeechDetector:
    def __init__(self, model_name="Hate-speech-CNERG/dehatebert-mono-english", threshold=0.5):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_name)
        self.model.eval()
        self.threshold = threshold
        self.label_map = {0: "non-hate", 1: "hate"}

    def is_hate_speech(self, text):
        inputs = self.tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
        with torch.no_grad():
            outputs = self.model(**inputs)
            probs = F.softmax(outputs.logits, dim=-1)
            hate_prob = probs[0, 1].item()
            is_hate = hate_prob >= self.threshold
        return is_hate, hate_prob 