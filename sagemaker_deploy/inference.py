# sagemaker_deploy/inference.py

import torch
from time_llm.models.TimeLLM import Model as TimeLLMModel
import json

# Configuration (same as training)
CONFIG = {
    "task_name": "long_term_forecast",
    "pred_len": 12,
    "seq_len": 48,
    "d_ff": 256,
    "llm_model": "GPT2",
    "llm_dim": 768,
    "llm_layers": 6,
    "d_model": 512,
    "n_heads": 8,
    "patch_len": 16,
    "stride": 8,
    "dropout": 0.1,
    "enc_in": 1,
    "prompt_domain": False,
    "content": ""
}

def model_fn(model_dir):
    model = TimeLLMModel(CONFIG)
    model_path = f"{model_dir}/pytorch_model.pt"
    model.load_state_dict(torch.load(model_path, map_location="cpu"))
    model.eval()
    return model

def input_fn(request_body, request_content_type):
    if request_content_type == "application/json":
        data = json.loads(request_body)
        return torch.tensor(data["sales_history"]).float().reshape(1, 48, 1)
    else:
        raise ValueError("Unsupported content type: " + request_content_type)

def predict_fn(input_data, model):
    dummy_mark = torch.zeros((1, 48, 1))  # No date info
    with torch.no_grad():
        output = model(input_data, dummy_mark, None, None)
    return {"forecast": output.cpu().numpy().flatten().tolist()}