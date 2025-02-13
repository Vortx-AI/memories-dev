import sys
import cv2
import numpy as np
from models.segment_anything import sam_model_registry, SamAutomaticMaskGenerator
from google.cloud import storage

# Function to generate masks, convert to contours, calculate dimensions, and upload image
def generate_contours(image, sam_checkpoint, model_type, bucket_name, output_image_name, device="cuda"):
    # Add the segment anything path
    sys.path.append("..")
    
    # Load the SAM model
    sam = sam_model_registry[model_type](checkpoint=sam_checkpoint)
    sam.to(device=device)
    
    # Generate masks
    mask_generator = SamAutomaticMaskGenerator(sam)
    masks = mask_generator.generate(image)
    
    # Initialize an empty list to store contours
    contours_list = []
    lengths = []
    widths = []
    
    # Convert masks to contours
    for mask in masks:
        # Get binary mask
        binary_mask = mask['segmentation'].astype(np.uint8)
        
        # Find contours
        contours, _ = cv2.findContours(binary_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            # Fit an ellipse to each contour
            if len(contour) >= 5:  # FitEllipse requires at least 5 points
                ellipse = cv2.fitEllipse(contour)
                (x, y), (major_axis, minor_axis), angle = ellipse
                
                # Major axis as length, Minor axis as width
                lengths.append(major_axis)
                widths.append(minor_axis)
        
        # Draw contours on the image
        cv2.drawContours(image, contours, -1, (0, 255, 0), 2)  # Drawing with green color
        
        # Store contours
        contours_list.append(contours)
    
    # Calculate average length and width
    average_length = np.mean(lengths) if lengths else 0
    average_width = np.mean(widths) if widths else 0
    
    # Convert image to RGB if it's in BGR format (OpenCV default)
    if len(image.shape) == 3 and image.shape[2] == 3:
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    # Upload the image with contours to Google Cloud Storage
    output_image_url = upload_image_to_gcs(image, bucket_name, output_image_name)
    
    return contours_list, average_length, average_width, output_image_url
    

# Helper function to upload image to Google Cloud Storage
def upload_image_to_gcs(image, bucket_name, output_image_name):
    # Initialize the Google Cloud Storage client
    client = storage.Client()
    bucket = client.get_bucket(bucket_name)
    
    # Encode image as JPEG
    _, encoded_image = cv2.imencode('.jpg', image)
    
    # Create a blob and upload the image
    blob = bucket.blob(output_image_name)
    blob.upload_from_string(encoded_image.tobytes(), content_type='image/jpeg')
    
    # Make the blob publicly accessible and get the URL
    blob.make_public()
    return blob.public_url
