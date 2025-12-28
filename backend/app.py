import modal
import os
import sys 
import numpy as np
import cv2
import torch
import requests
import tempfile
from typing import Tuple

# ==============================================================================
# CONFIGURATION
# Users: Replace these values with your specific URLs or File Paths
# ==============================================================================
APP_NAME = "echonet-serverless-edu"
WEIGHTS_URL = "INSERT_LINK_TO_YOUR_MODEL_WEIGHTS_HERE"  # e.g., "https://your-bucket.com/echonet.pt"
GPU_CONFIG = "T4"  # Options: "T4", "A10G", "A100"

# ==============================================================================
# 1. DEFINE IMAGE & DEPENDENCIES
# This ensures the environment is strictly reproducible for any user.
# ==============================================================================
image = (
    modal.Image.debian_slim(python_version="3.12")
    .apt_install("ffmpeg", "libsm6", "libxext6")  # Required for OpenCV
    .pip_install(
        "torch",
        "torchvision",
        "opencv-python-headless",
        "numpy",
        "requests",
        "pillow"
    )
)

# ==============================================================================
# 2. BUILD STEP: WEIGHT DOWNLOAD
# This runs once during deployment to bake the model weights into the image.
# ==============================================================================
def download_weights():
    # Validation check to prevent build errors with placeholder links
    if "INSERT_LINK" in WEIGHTS_URL:
        print("⚠️  Warning: No valid weight URL provided. Skipping download during build.")
        return

    print("Downloading model weights...")
    os.makedirs("/root/models", exist_ok=True)
    
    try:
        response = requests.get(WEIGHTS_URL, stream=True)
        response.raise_for_status()
        with open("/root/models/model_weights.pt", "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print("✅ Weights downloaded successfully.")
    except Exception as e:
        print(f"❌ Failed to download weights: {e}")

# Attach the build step to the image
image = image.run_function(download_weights)

# ==============================================================================
# 3. SERVERLESS APP DEFINITION
# ==============================================================================
app = modal.App(APP_NAME)

@app.cls(
    image=image,
    gpu=GPU_CONFIG,
    container_idle_timeout=300,  # Keep 'warm' for 5 minutes (Scale-to-Zero optimization)
    # Add your cloud secrets here (e.g., Supabase keys) via the Modal Dashboard
    secrets=[modal.Secret.from_name("my-app-secrets")] 
)
class ModelInference:
    def enter(self):
        """
        Cold Start Routine: Runs once when the GPU container starts.
        Loads the Model Architecture and Weights into VRAM.
        """
        print("🥶 Cold Start: Initializing CUDA Context...")
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # ----------------------------------------------------------------------
        # MODEL ARCHITECTURE DEFINITION
        # Note: In a production repo, import your specific model class here.
        # Below is a standard ResNet r2+1d placeholder typical for EchoNet.
        # ----------------------------------------------------------------------
        try:
            # Placeholder: Load standard architecture or your custom definition
            self.model = torch.hub.load("facebookresearch/pytorchvideo", "slow_r50", pretrained=False)
            
            # Load Weights (if present)
            weight_path = "/root/models/model_weights.pt"
            if os.path.exists(weight_path):
                checkpoint = torch.load(weight_path, map_location=self.device)
                self.model.load_state_dict(checkpoint, strict=False)
                print(f"✅ Loaded weights from {weight_path}")
            else:
                print("⚠️  No custom weights found. Using initialized random weights (TEST MODE).")
            
            self.model.to(self.device)
            self.model.eval()
            
        except Exception as e:
            print(f"❌ Critical Error loading model: {e}")
            raise e

    def preprocess_video(self, video_path: str) -> torch.Tensor:
        """
        Universal Transcoding Layer:
        Normalizes inputs (GIF/MP4/AVI) to the tensor shape required by the CNN.
        """
        cap = cv2.VideoCapture(video_path)
        frames = []
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            # Resize to model input dimensions (e.g., 112x112)
            frame = cv2.resize(frame, (112, 112))
            # Normalize pixel values
            frame = frame.astype(np.float32) / 255.0
            frames.append(frame)
        cap.release()

        if not frames:
            raise ValueError("Video file contained no readable frames.")

        # Convert to Channel-First Tensor: (Batch, Channels, Time, Height, Width)
        # Note: Adjust permute order based on your specific model training
        tensor = torch.FloatTensor(np.array(frames)).permute(3, 0, 1, 2)
        return tensor.unsqueeze(0).to(self.device)

    @modal.method()
    def predict(self, video_url: str) -> dict:
        """
        The Main Endpoint.
        1. Downloads video from URL (Source Agnostic).
        2. Preprocesses (Format Agnostic).
        3. Runs Inference.
        4. Purges data (Privacy Preserving).
        """
        print(f"📥 Processing: {video_url}")
        
        # Create a temporary file that auto-deletes when closed
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=True) as temp_vid:
            # Download
            try:
                r = requests.get(video_url, timeout=30)
                r.raise_for_status()
                temp_vid.write(r.content)
                temp_vid.flush()
            except Exception as e:
                return {"error": f"Download failed: {str(e)}"}
            
            # Inference
            try:
                with torch.no_grad():
                    input_tensor = self.preprocess_video(temp_vid.name)
                    output = self.model(input_tensor)
                    
                    # Convert tensor to python float (LVEF)
                    # Logic depends on model head (Regression vs Classification)
                    prediction_value = output.item() 
                    
                return {
                    "status": "success",
                    "lvef": prediction_value,
                    "units": "%"
                }
            except Exception as e:
                print(f"Inference Error: {e}")
                return {"error": "Inference failed during processing."}

# ==============================================================================
# 4. LOCAL TESTING ENTRYPOINT
# Run this via terminal: `modal run backend/app.py`
# ==============================================================================
@app.local_entrypoint()
def test_run():
    # ---------------------------------------------------------
    # ACTION REQUIRED: Insert a valid video URL below to test.
    # ---------------------------------------------------------
    TEST_VIDEO_URL = "INSERT_YOUR_TEST_VIDEO_URL_HERE"
    
    if "INSERT" in TEST_VIDEO_URL:
        print("\n⛔  ERROR: You must provide a valid video URL in 'test_run' to test.")
        print("    Edit the 'TEST_VIDEO_URL' variable in app.py and try again.\n")
        return

    print(f"🚀 Starting Test Run on: {TEST_VIDEO_URL}")
    model = ModelInference()
    
    # Remote Call
    result = model.predict.remote(TEST_VIDEO_URL)
    
    print("\n" + "="*40)
    print("RESULTS:")
    print(result)
    print("="*40 + "\n")
