from PIL import Image
import os
import shutil
import torch
import timm
from typing import Tuple, List, Dict
import logging

logging.basicConfig(level=logging.INFO)

class ContentDetector:
    def __init__(self, quarantine_dir: str = "quarantine", confidence_threshold: float = 0.5):
        # Dictionary to track original path to quarantined path mapping
        self.quarantine_map = {}
        """Initialize the content detector with quarantine directory."""
        self.quarantine_dir = quarantine_dir
        self.confidence_threshold = confidence_threshold
        self._ensure_quarantine_dir()
        
        try:
            # Initialize the NSFW detection model
            logging.info("Loading NSFW detection model...")
            self.nsfw_model = timm.create_model("hf_hub:Marqo/nsfw-image-detection-384", pretrained=True)
            self.nsfw_model.eval()
            self.nsfw_data_config = timm.data.resolve_model_data_config(self.nsfw_model)
            self.nsfw_transforms = timm.data.create_transform(**self.nsfw_data_config, is_training=False)
            
            # Get NSFW class names and verify model configuration
            nsfw_cfg = self.nsfw_model.pretrained_cfg
            self.nsfw_class_names = nsfw_cfg.get("label_names", [])
            
            if not self.nsfw_class_names:
                raise ValueError("NSFW model does not provide class names")
                
            # Verify we have NSFW and SFW classes
            if 'NSFW' not in self.nsfw_class_names or 'SFW' not in self.nsfw_class_names:
                raise ValueError(f"NSFW model must have NSFW and SFW classes. Found: {self.nsfw_class_names}")
            
            # Get class indices
            self.nsfw_idx = self.nsfw_class_names.index('NSFW')
            self.sfw_idx = self.nsfw_class_names.index('SFW')
            
            logging.info(f"NSFW model loaded with classes: {self.nsfw_class_names}")
            logging.info("NSFW detection initialized successfully")
            
        except Exception as e:
            logging.error(f"Error initializing content detection models: {e}")
            raise
    

    
    def _ensure_quarantine_dir(self):
        """Ensure quarantine directory exists."""
        if not os.path.exists(self.quarantine_dir):
            os.makedirs(self.quarantine_dir)
    



    
    def analyze_image_content(self, image_path: str) -> Tuple[bool, float, List[str]]:
        """Analyze image content using NSFW detection model."""
        try:
            # Run NSFW detection
            img = Image.open(image_path).convert('RGB')
            img_tensor = self.nsfw_transforms(img).unsqueeze(0)
            
            with torch.no_grad():
                output = self.nsfw_model(img_tensor).softmax(dim=-1).cpu()
            
            # Get NSFW probabilities
            probabilities = output[0].numpy()
            nsfw_prob = float(probabilities[self.nsfw_idx])
            sfw_prob = float(probabilities[self.sfw_idx])
            
            # Log NSFW detection results
            logging.info(f"NSFW analysis for {image_path}:")
            logging.info(f"NSFW probability: {nsfw_prob:.3f}")
            logging.info(f"SFW probability: {sfw_prob:.3f}")
            
            # Determine if content should be quarantined
            is_inappropriate = nsfw_prob >= self.confidence_threshold
            max_prob = nsfw_prob
            
            # Prepare reasons
            reasons = []
            
            if nsfw_prob >= self.confidence_threshold:
                reasons.append(f'NSFW content detected ({nsfw_prob:.1%} confidence)')
                reasons.append(f'- NSFW: {nsfw_prob:.1%}')
                reasons.append(f'- SFW: {sfw_prob:.1%}')
            
            return is_inappropriate, max_prob, reasons
            
        except Exception as e:
            logging.error(f"Error analyzing image {image_path}: {e}")
            return False, 0.0, [f'Error analyzing image: {e}']
    
    def quarantine_file(self, file_path: str) -> Tuple[bool, str]:
        """
        Move a file to quarantine directory.
        Returns: (success, message)
        """
        try:
            filename = os.path.basename(file_path)
            dest_path = os.path.join(self.quarantine_dir, filename)
            
            # If file with same name exists, add number suffix
            counter = 1
            while os.path.exists(dest_path):
                name, ext = os.path.splitext(filename)
                dest_path = os.path.join(self.quarantine_dir, f"{name}_{counter}{ext}")
                counter += 1
            
            shutil.move(file_path, dest_path)
            # Track the mapping from original to quarantined path
            self.quarantine_map[file_path] = dest_path
            return True, dest_path
            
        except Exception as e:
            return False, f"Failed to quarantine: {e}"
    
    def get_quarantine_path(self, original_path: str) -> str:
        """Returns the quarantine path for a given original path if it exists, or None."""
        return self.quarantine_map.get(original_path)
        
    def scan_file(self, file_path: str) -> Tuple[bool, List[str]]:
        """
        Scan a single file for NSFW or violent content.
        Returns: (is_flagged, reasons)
        """
        try:
            is_inappropriate, max_prob, reasons = self.analyze_image_content(file_path)
            
            if is_inappropriate:
                logging.warning(f"Inappropriate content detected in {file_path} with score {max_prob:.3f}")
            else:
                logging.info(f"File {file_path} is safe (max inappropriate score: {max_prob:.3f})")
            
            return is_inappropriate, reasons
            
        except Exception as e:
            logging.error(f"Error scanning file {file_path}: {e}")
            return False, [f"Error scanning file: {e}"]