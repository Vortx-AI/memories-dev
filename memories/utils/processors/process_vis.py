import os
import torch
import logging
from PIL import Image
from transformers import BlipProcessor, BlipForConditionalGeneration
import segmentation_models_pytorch as smp


# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Global references for preloaded processor and model
caption_processor = None
caption_model = None
# Global reference for segmentation model
segmentation_model = None

def load_segmentation_model():
    """
    Load a transformer-based segmentation model.
    """
    global segmentation_model
    if segmentation_model is not None:
        logger.info("Segmentation model already loaded.")
        return segmentation_model

    logger.info("Loading segmentation model...")
    segmentation_model = smp.Unet(
        encoder_name='mit_b0',        # 'mit_b0' is a transformer encoder in smp
        encoder_weights=None,         # Use None if pre-trained weights are not available
        in_channels=3,                # Adjusted to 3 channels as required by the encoder
        classes=1,                    # Single output channel
    )
    # Move model to GPU
    segmentation_model = segmentation_model.cuda()
    segmentation_model.eval()
    logger.info("Segmentation model loaded successfully.")
    return segmentation_model

def unload_segmentation_model():
    """
    Unload the transformer-based segmentation model and clear GPU cache.
    """
    global segmentation_model
    if segmentation_model is not None:
        logger.info("Unloading segmentation model...")
        del segmentation_model
        segmentation_model = None
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        logger.info("Segmentation model unloaded and GPU cache cleared.")
    else:
        logger.info("Segmentation model is not loaded; nothing to unload.")

# Load the transformer-based model once at startup
#segmentation_model = load_transformer_model()
def unload_transformer_model():
    """
    Unload the transformer-based segmentation model and clear GPU cache.
    """
    global segmentation_model
    if segmentation_model is not None:
        logger.info("Unloading segmentation model...")
        del segmentation_model
        segmentation_model = None
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        logger.info("Segmentation model unloaded and GPU cache cleared.")
    else:
        logger.info("Segmentation model is not loaded; nothing to unload.")

def load_blip_model():
    """Loads the BLIP model and processor into global variables if not already loaded.
    This function ensures the model is loaded lazily and only once.
    """
    global caption_processor, caption_model

    # Check if the model is already loaded
    if caption_processor and caption_model:
        logger.info("BLIP model is already loaded.")
        return

    # Load the BLIP model
    hf_cache_dir = os.getenv("CACHE_DIR", ".cache/huggingface")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    logger.info(f"Using device: {device}")

    try:
        logger.info("Loading BLIP model for image captioning...")
        caption_processor = BlipProcessor.from_pretrained(
            "Salesforce/blip-image-captioning-base",
            cache_dir=hf_cache_dir
        )
        caption_model = BlipForConditionalGeneration.from_pretrained(
            "Salesforce/blip-image-captioning-base",
            cache_dir=hf_cache_dir
        ).to(device)
        logger.info("BLIP model loaded successfully.")
    except Exception as e:
        logger.error(f"Failed to load BLIP model: {e}")
        raise RuntimeError("Failed to load BLIP model. Ensure proper environment setup and internet connection.") from e


def unload_blip_model():
    """
    Unloads the BLIP model and clears GPU cache if applicable.
    """
    global caption_processor, caption_model

    if caption_model or caption_processor:
        logger.info("Unloading BLIP model...")
        del caption_model
        del caption_processor
        caption_model = None
        caption_processor = None
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        logger.info("BLIP model unloaded and GPU cache cleared.")
    else:
        logger.info("BLIP model was not loaded; nothing to unload.")

blip_model = None

def get_blip_model():
    global blip_model
    if blip_model is None:
        # Load the BLIP model when needed
        from processors.process_vis import load_blip_model  # Import function to load BLIP model
        blip_model = load_blip_model()
    return blip_model

def extract_image_details(image_path: str) -> str:
    """
    Generate a descriptive caption for an image using the BLIP model.
 
    Args:
        image_path (str): Path to the image file.
 
    Returns:
        str: A descriptive caption for the image.
    """
    if caption_model is None or caption_processor is None:
        logger.error("BLIP model not loaded. Call load_blip_model() first.")
        raise RuntimeError("BLIP model is not loaded. Please call load_blip_model() during application startup.")


    try:
        load_blip_model()
        # Load the image
        image = Image.open(image_path).convert("RGB")
        logger.info(f"Loaded image from {image_path}")

        # Prepare the image for the BLIP model
        caption_inputs = caption_processor(images=image, return_tensors="pt").to(caption_model.device)

        # Generate the caption
        logger.info("Generating caption for the image...")
        with torch.no_grad():
            caption_outputs = caption_model.generate(**caption_inputs)
        caption = caption_processor.decode(caption_outputs[0], skip_special_tokens=True)
        logger.info(f"Generated caption: {caption}")
        return caption

    except FileNotFoundError:
        logger.error(f"File not found: {image_path}")
        return "File not found."

    except Exception as e:
        logger.error(f"Error generating caption for image {image_path}: {e}")
        return "Failed to generate caption."

def extract_image_details_avijeet(image_path: str) -> str:
    """
    Generate a descriptive caption for an image using the BLIP model.
 
    Args:
        image_path (str): Path to the image file.
 
    Returns:
        str: A descriptive caption for the image.
    """
    load_blip_model()
    if caption_model is None or caption_processor is None:
        logger.error("BLIP model not loaded. Call load_blip_model() first.")
        raise RuntimeError("BLIP model is not loaded. Please call load_blip_model() during application startup.")

    try:
        # Load the image
        image = Image.open(image_path).convert("RGB")
        logger.info(f"Loaded image from {image_path}")

        # Prepare the image for the BLIP model
        caption_inputs = caption_processor(images=image, return_tensors="pt").to(caption_model.device)

        # Generate the caption
        logger.info("Generating caption for the image...")
        with torch.no_grad():
            caption_outputs = caption_model.generate(**caption_inputs)
        caption = caption_processor.decode(caption_outputs[0], skip_special_tokens=True)
        logger.info(f"Generated caption: {caption}")
        return caption

    except FileNotFoundError:
        logger.error(f"File not found: {image_path}")
        return "File not found."

    except Exception as e:
        logger.error(f"Error generating caption for image {image_path}: {e}")
        return "Failed to generate caption."

def extract_image_details_avijeet_with_input_prompt(image_path: str, additional_context: str = "", prompt_template: str = None) -> str:
    """
    Generate a descriptive caption for an image using the BLIP model with dynamic prompt support.
 
    Args:
        image_path (str): Path to the image file.
        additional_context (str): Additional context or description to enhance the generated caption.
                  prompt_template (str): Optional custom prompt template for generating captions dynamically.
            Use {caption} and {context} as placeholders in the template.
 
    Returns:
        str: A descriptive caption for the image, optionally enriched with context or a custom prompt.
    """
    load_blip_model()
    if caption_model is None or caption_processor is None:
        logger.error("BLIP model not loaded. Call load_blip_model() first.")
        raise RuntimeError("BLIP model is not loaded. Please call load_blip_model() during application startup.")
    try:
        # Load the image
        image = Image.open(image_path).convert("RGB")
        logger.info(f"Loaded image from {image_path}")

        # Prepare the image for the BLIP model
        caption_inputs = caption_processor(images=image, return_tensors="pt").to(caption_model.device)

        # Generate the caption
        logger.info("Generating caption for the image...")
        with torch.no_grad():
            caption_outputs = caption_model.generate(**caption_inputs)
        base_caption = caption_processor.decode(caption_outputs[0], skip_special_tokens=True)
        logger.info(f"Generated base caption: {base_caption}")
        # Apply additional context or custom prompt template
        if prompt_template:
            caption = prompt_template.format(caption=base_caption, context=additional_context)
        else:
            caption = f"{base_caption}. {additional_context}" if additional_context else base_caption

        logger.info(f"Enhanced caption: {caption}")
        return caption

    except FileNotFoundError:
        logger.error(f"File not found: {image_path}")
        return "File not found."

    except Exception as e:
        logger.error(f"Error generating caption for image {image_path}: {e}")
        return "Failed to generate caption."
