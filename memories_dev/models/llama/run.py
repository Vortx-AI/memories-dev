from unsloth import FastLanguageModel
import torch

# Configuration parameters
max_seq_length = 2048  # Maximum sequence length
dtype = None  # Automatically detect the best dtype based on GPU
load_in_4bit = True  # Enable 4-bit quantization to reduce memory usage

# Specify the pre-quantized model to use and local cache directory
model_name = "unsloth/Meta-Llama-3.1-8B-bnb-4bit"
model_cache_dir = "./models/llama-3.1-8b"  # Local directory to cache the model

# Load the model and tokenizer
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name=model_name,
    cache_dir=model_cache_dir,  # Specify a local cache directory
    max_seq_length=max_seq_length,
    dtype=dtype,
    load_in_4bit=load_in_4bit,
)

# Enable faster inference
FastLanguageModel.for_inference(model)

# Function to run inference
def run_inference(instruction, input_text):
    alpaca_prompt = (
        "Create a scene that can be used with stable diffusion: "
    )

    prompt = alpaca_prompt.format(instruction, input_text, "")
    inputs = tokenizer([prompt], return_tensors="pt").to("cuda")
    outputs = model.generate(**inputs, max_new_tokens=64, use_cache=True)
    decoded_outputs = tokenizer.batch_decode(outputs, skip_special_tokens=True)
    return decoded_outputs

# Example usage
instruction = "Create a scene that can be used with stable diffusion"
input_text = ""
result = run_inference(instruction, input_text)
print(result)
