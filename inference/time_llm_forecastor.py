# model_upload/code/inference.py

import torch
from time_llm.models.TimeLLM import Model as TimeLLMModel

class Config:
    def __init__(self):
        self.task_name = "long_term_forecast"
        self.pred_len = 12
        self.seq_len = 48
        self.d_ff = 256
        self.llm_model = "GPT2"
        self.llm_dim = 768
        self.llm_layers = 6
        self.d_model = 512
        self.n_heads = 8
        self.patch_len = 16
        self.stride = 8
        self.dropout = 0.1
        self.enc_in = 1
        self.prompt_domain = False
        self.content = ""

class TimeLLMForecastor:
    def __init__(self):
        self.config = Config()
        self.model = TimeLLMModel(self.config)
        self.model.load_state_dict(torch.load("model_upload/code/pytorch_model.pt", map_location="cpu"))
        self.model.eval()

    def predict(self, series):
        # Stubbed mock forecast
        return [float(x) * 1.1 for x in series[-self.config.pred_len:]]