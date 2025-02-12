import subprocess
import torch

def check_gpu_memory():
    """
    Check the total and available GPU memory and current utilization.
    Uses `nvidia-smi` for detailed monitoring if available, 
    otherwise falls back to PyTorch's `torch.cuda` API.
    """
    try:
        # Use `torch.cuda` API for memory stats
        total_memory = torch.cuda.get_device_properties(0).total_memory / 1e9  # Convert to GB
        reserved_memory = torch.cuda.memory_reserved(0) / 1e9  # Reserved by PyTorch
        allocated_memory = torch.cuda.memory_allocated(0) / 1e9  # Allocated by PyTorch
        free_memory = reserved_memory - allocated_memory

        print(f"Using PyTorch GPU Stats:")
        print(f"Total GPU Memory: {total_memory:.2f} GB")
        print(f"Allocated GPU Memory: {allocated_memory:.2f} GB")
        print(f"Reserved GPU Memory: {reserved_memory:.2f} GB")
        print(f"Free GPU Memory: {free_memory:.2f} GB\n")

        # Use `nvidia-smi` for detailed stats if available
        try:
            nvidia_smi_output = subprocess.check_output(["nvidia-smi"], text=True)
            print(f"nvidia-smi output:\n{nvidia_smi_output}")
        except FileNotFoundError:
            print("nvidia-smi not available. Install NVIDIA tools for detailed stats.")
    except Exception as e:
        print(f"Error while checking GPU memory: {e}")

if __name__ == "__main__":
    print("Checking GPU memory before running the script...\n")
    check_gpu_memory()

    # Example usage
    image_path = "/path/to/image.jpg"
    prompt = "Describe this image"
    result = llama_vision_extraction(image_path, prompt)
    print(f"Generated Description: {result}")
