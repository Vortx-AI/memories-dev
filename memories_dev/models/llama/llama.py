import torch
import subprocess
import threading
from unsloth import FastLanguageModel
import time
from django.core.cache import cache
import gc

#model_name = "unsloth/Meta-Llama-3.1-8B-bnb-4bit"
#cache_dir = "./models/llama-3.1-8b"

def clear_gpu_resources():
    """
    Clears cache and forces garbage collection to free GPU memory.
    """
    cache.clear()  # Clear any cached data from Django cache
    torch.cuda.empty_cache()  # Clear PyTorch GPU memory cache
    gc.collect()  # Force Python garbage collection

def get_gpu_usage():
    """
    Monitors GPU usage using nvidia-smi and prints the current memory usage.
    """
    try:
        result = subprocess.run(['nvidia-smi', '--query-gpu=memory.total,memory.used', '--format=csv,noheader,nounits'],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        vram_info = result.stdout.strip().split('\n')
        for gpu_idx, gpu_info in enumerate(vram_info):
            total_mem, used_mem = gpu_info.split(', ')
            print(f"GPU {gpu_idx}: Total VRAM: {total_mem} MiB, Used VRAM: {used_mem} MiB")
    except FileNotFoundError:
        print("nvidia-smi not found. Make sure the NVIDIA drivers are installed and nvidia-smi is available.")
    except Exception as e:
        print(f"Error retrieving GPU info: {e}")

def monitor_gpu_usage(interval=2, stop_event=None):
    """
    Monitors GPU usage every `interval` seconds in a separate thread.
    Terminates monitoring when stop_event is set.
    """
    while not stop_event.is_set():
        get_gpu_usage()
        time.sleep(interval)

def load_and_run(instruction, input_text, cache_dir="venv", max_seq_length=2048, dtype=None, load_in_4bit=True):
    """
    Loads the model and tokenizer, runs the model with the given instruction and input, and returns the generated output.

    Args:
        instruction (str): The instruction to be included in the prompt.
        input_text (str): The input text for generating the output.
        cache_dir (str): The directory to cache the model.
        max_seq_length (int): The maximum sequence length for the model.
        dtype (torch.dtype): The data type to load the model with.
        load_in_4bit (bool): Whether to load the model in 4-bit precision.

    Returns:
        list[str]: The generated output as a list of strings.
    """

    # Set up a stop event to terminate the monitoring thread
    stop_event = threading.Event()

    # Start GPU usage monitoring in a separate thread
    gpu_monitor_thread = threading.Thread(target=monitor_gpu_usage, args=(2, stop_event), daemon=True)
    gpu_monitor_thread.start()

    try:
        # Check if CUDA is available
        device = "cuda" if torch.cuda.is_available() else "cpu"

        # Load the model and tokenizer
        model, tokenizer = FastLanguageModel.from_pretrained(
            model_name=model_name,
            cache_dir=cache_dir,
            max_seq_length=max_seq_length,
            dtype=dtype,
            load_in_4bit=load_in_4bit,
        )

        # Clear any potential leftover GPU resources
        clear_gpu_resources()

        # Enable faster inference
        model = FastLanguageModel.for_inference(model)

        # Create the prompt
        alpaca_prompt = "{}: {}"
        prompt = alpaca_prompt.format(instruction, input_text)

        # Tokenize the input
        inputs = tokenizer([prompt], return_tensors="pt").to(device)

        # Generate the output sequence
        outputs = model.generate(**inputs, max_new_tokens=64, use_cache=True)

        # Decode the generated tokens to text
        decoded_outputs = tokenizer.batch_decode(outputs, skip_special_tokens=True)

        # Clear GPU resources after inference
        clear_gpu_resources()

        return decoded_outputs

    finally:
        # Stop GPU monitoring
        stop_event.set()
        gpu_monitor_thread.join()

        # Ensure GPU memory is cleared
        clear_gpu_resources()

def get_embedding(text, model_name="Llama-3.1"):
    """
    Generates an embedding for the given text using the specified Llama model.

    Args:
        text (str): The input text for which to generate an embedding.
        model_name (str): The name of the Llama model to use for generating the embedding.

    Returns:
        numpy.ndarray: The embedding vector for the input text.
    """
    # Initialize the Llama model using Unsloth
    llama_model = FastLanguageModel.from_pretrained(model_name=model_name)

    # Generate and return the embedding
    embedding_vector = llama_model.get_embedding(text)
    return embedding_vector
