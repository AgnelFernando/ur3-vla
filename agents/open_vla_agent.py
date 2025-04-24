from transformers import AutoModelForVision2Seq, AutoProcessor
import torch
from pathlib import Path
import json
from PIL import Image

class OpenVla:
    def __init__(self, model_path, unnorm_key):
        self.processor = AutoProcessor.from_pretrained(model_path, trust_remote_code=True)
        self.model = AutoModelForVision2Seq.from_pretrained(
            model_path, 
            attn_implementation="flash_attention_2",  
            torch_dtype=torch.bfloat16, 
            low_cpu_mem_usage=True, 
            trust_remote_code=True
        ).to("cuda:0")
        # with open(Path(model_path) / "dataset_statistics.json", "r") as f:
        with open("logs/openvla-7b+ur3_vla+b4+lr-0.0005+lora-r32+dropout-0.0/dataset_statistics.json", "r") as f:
                self.model.norm_stats = json.load(f)
        self.unnorm_key = unnorm_key

    def predict(self, image, prompt):
        inputs = self.processor(prompt, image).to("cuda:0", dtype=torch.bfloat16)
        action = self.model.predict_action(**inputs, unnorm_key=self.unnorm_key, do_sample=False)
        return action
