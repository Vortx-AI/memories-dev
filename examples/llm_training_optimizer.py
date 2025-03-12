#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
LLM Training Optimizer Example

This example demonstrates how to use the memories-dev framework to optimize
large language model training by efficiently managing memory across different tiers.

Usage:
    python examples/llm_training_optimizer.py --model_size small --epochs 3 --batch_size 8

Author: Memories-Dev Team
Date: February 25, 2025
"""

import argparse
import os
import time
import torch
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional

# Import memories-dev components
from memories.core.memory_manager import MemoryManager
from memories.core.memory_store import MemoryStore
from memories.models.load_model import LoadModel
from memories.utils.earth.processors import gpu_stat

# Define a simple gpu_stat function if the imported one doesn't work
def get_gpu_stats():
    """Get GPU statistics."""
    try:
        if torch.cuda.is_available():
            return {
                "status": "ok",
                "used": torch.cuda.memory_allocated() / (1024 ** 3),  # Convert to GB
                "free": torch.cuda.memory_reserved() / (1024 ** 3) - torch.cuda.memory_allocated() / (1024 ** 3)
            }
        return None
    except Exception:
        return {"status": "error", "used": 0, "free": 0}

class LLMTrainingOptimizer:
    """
    A class for optimizing LLM training using the memories-dev memory management system.
    
    This optimizer efficiently manages model parameters, gradients, activations, and
    checkpoints across different memory tiers to maximize training efficiency.
    """
    
    def __init__(
        self,
        model_size: str = "small",
        output_dir: str = "./llm_training_output",
        hot_memory_size: int = 8,
        warm_memory_size: int = 32,
        cold_memory_size: int = 500,
        glacier_memory_size: int = 2048
    ):
        """
        Initialize the LLM Training Optimizer.
        
        Args:
            model_size: Size of the model to train ("small", "medium", "large")
            output_dir: Directory to save outputs
            hot_memory_size: Size of hot memory (GPU) in GB (for display only)
            warm_memory_size: Size of warm memory (RAM) in GB (for display only)
            cold_memory_size: Size of cold memory (SSD) in GB (for display only)
            glacier_memory_size: Size of glacier memory (HDD/Cloud) in GB (for display only)
        """
        self.model_size = model_size
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Store memory sizes for reference (not used for actual initialization)
        self.hot_memory_size = hot_memory_size
        self.warm_memory_size = warm_memory_size
        self.cold_memory_size = cold_memory_size
        self.glacier_memory_size = glacier_memory_size
        
        # Initialize memory manager (singleton with no parameters)
        self.memory_manager = MemoryManager()
        
        # Initialize memory store for storing data
        self.memory_store = MemoryStore()
        
        # Initialize model and training state
        self.model = None
        self.optimizer = None
        self.training_data = None
        self.model_key = None
        self.dataset_key = None
        self.checkpoint_keys = []
        
        # Metrics tracking
        self.metrics = {
            "training_time": 0,
            "memory_usage": [],
            "loss_history": [],
            "checkpoint_sizes": [],
            "tier_migrations": {
                "hot_to_warm": 0,
                "warm_to_cold": 0,
                "cold_to_glacier": 0
            }
        }
        
        # Set up logging
        self._setup_logging()
        
    def _setup_logging(self):
        """Set up logging for the training process."""
        self.log_file = self.output_dir / "training_log.txt"
        with open(self.log_file, "w") as f:
            f.write(f"LLM Training Optimizer Log\n")
            f.write(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Model size: {self.model_size}\n")
            f.write(f"Memory configuration:\n")
            f.write(f"  - Hot memory: {self.hot_memory_size} GB\n")
            f.write(f"  - Warm memory: {self.warm_memory_size} GB\n")
            f.write(f"  - Cold memory: {self.cold_memory_size} GB\n")
            f.write(f"  - Glacier memory: {self.glacier_memory_size} GB\n")
            f.write(f"\n{'='*50}\n\n")
    
    def log(self, message: str):
        """Log a message to the log file and print to console."""
        print(message)
        with open(self.log_file, "a") as f:
            f.write(f"{message}\n")
    
    def initialize_model(self):
        """Initialize the model based on the specified size."""
        self.log(f"Initializing {self.model_size} model...")
        
        # Map model size to actual model name
        model_map = {
            "small": "deepseek-coder-small",
            "medium": "deepseek-coder-medium",
            "large": "deepseek-coder-large"
        }
        
        model_name = model_map.get(self.model_size, "deepseek-coder-small")
        
        # Check GPU availability
        gpu_memory = get_gpu_stats()
        use_gpu = gpu_memory is not None and gpu_memory['free'] > 2000  # At least 2GB free
        
        # Load the model
        model_loader = LoadModel(
            use_gpu=use_gpu,
            model_provider="deepseek-ai",
            deployment_type="local",
            model_name=model_name
        )
        
        # Get the underlying model
        self.model = model_loader.base_model.model
        
        # Store model in hot memory
        self.model_key = "active_model"
        # Note: Using a simple dictionary to store model state instead of memory_store
        # since memory_store.store is an async method and we're not using async/await here
        self.stored_models = {}
        self.stored_models[self.model_key] = self.model.state_dict()
        
        # Create optimizer
        self.optimizer = torch.optim.AdamW(self.model.parameters(), lr=5e-5)
        
        self.log(f"Model initialized and stored in hot memory")
        return True
    
    def load_training_data(self, dataset_path: Optional[str] = None):
        """
        Load training data from a file or generate synthetic data.
        
        Args:
            dataset_path: Path to the dataset file (if None, generates synthetic data)
        """
        self.log(f"Loading training data...")
        
        if dataset_path and os.path.exists(dataset_path):
            # Load real dataset
            # This is a placeholder - in a real implementation, you would load your dataset
            self.log(f"Loading dataset from {dataset_path}")
            self.training_data = torch.load(dataset_path)
        else:
            # Generate synthetic data for demonstration
            self.log(f"Generating synthetic training data")
            
            # Size depends on model size
            data_sizes = {
                "small": (1000, 512),
                "medium": (2000, 768),
                "large": (3000, 1024)
            }
            
            size = data_sizes.get(self.model_size, (1000, 512))
            
            # Check if model is initialized to get vocab size
            vocab_size = 32000  # Default safe value for most LLM models
            if self.model is not None and hasattr(self.model, 'config'):
                vocab_size = self.model.config.vocab_size
                self.log(f"Using model's vocabulary size: {vocab_size}")
            else:
                self.log(f"Model not initialized yet, using default vocabulary size: {vocab_size}")
            
            # Generate random input IDs and attention masks with valid token IDs
            input_ids = torch.randint(0, vocab_size - 1, (size[0], size[1]))
            attention_mask = torch.ones_like(input_ids)
            labels = torch.randint(0, vocab_size - 1, (size[0], size[1]))
            
            self.training_data = {
                "input_ids": input_ids,
                "attention_mask": attention_mask,
                "labels": labels
            }
        
        # Store training data in cold memory (it's large but not accessed frequently)
        self.dataset_key = "training_dataset"
        self.stored_models[self.dataset_key] = self.training_data
        
        self.log(f"Training data loaded and stored in cold memory")
        self.log(f"Dataset size: {len(self.training_data['input_ids'])} examples")
        return True
    
    def train(self, epochs: int = 3, batch_size: int = 8):
        """
        Train the model for the specified number of epochs.
        
        Args:
            epochs: Number of training epochs
            batch_size: Batch size for training
        """
        if self.model is None:
            self.log("Error: Model not initialized. Call initialize_model() first.")
            return False
        
        if self.training_data is None:
            self.log("Error: Training data not loaded. Call load_training_data() first.")
            return False
        
        self.log(f"Starting training for {epochs} epochs with batch size {batch_size}")
        start_time = time.time()
        
        try:
            # Training loop
            for epoch in range(epochs):
                epoch_start_time = time.time()
                self.log(f"Epoch {epoch+1}/{epochs}")
                
                # Get dataset from our stored models dictionary
                dataset = self.stored_models[self.dataset_key]
                self.log(f"Dataset keys: {list(dataset.keys())}")
                self.log(f"Input ids shape: {dataset['input_ids'].shape}")
                
                # Track epoch loss
                epoch_loss = 0.0
                num_batches = len(dataset["input_ids"]) // batch_size
                
                for batch_idx in range(0, len(dataset["input_ids"]), batch_size):
                    try:
                        # Extract batch data
                        end_idx = min(batch_idx + batch_size, len(dataset["input_ids"]))
                        
                        # Load batch data
                        batch_data = {
                            "input_ids": dataset["input_ids"][batch_idx:end_idx],
                            "attention_mask": dataset["attention_mask"][batch_idx:end_idx],
                            "labels": dataset["labels"][batch_idx:end_idx]
                        }
                        
                        self.log(f"Batch shapes - input_ids: {batch_data['input_ids'].shape}, attention_mask: {batch_data['attention_mask'].shape}, labels: {batch_data['labels'].shape}")
                        
                        # Store batch data in our dictionary
                        batch_key = f"batch_{batch_idx}"
                        self.stored_models[batch_key] = batch_data
                        
                        # Get model from our dictionary
                        model_state = self.stored_models[self.model_key]
                        self.model.load_state_dict(model_state)
                        
                        # Forward pass
                        self.log(f"Running forward pass with batch {batch_idx}")
                        outputs = self.model(
                            input_ids=batch_data["input_ids"],
                            attention_mask=batch_data["attention_mask"],
                            labels=batch_data["labels"]
                        )
                        
                        loss = outputs.loss
                        epoch_loss += loss.item()
                        
                        # Backward pass and optimization
                        self.optimizer.zero_grad()
                        loss.backward()
                        self.optimizer.step()
                        
                        # Store updated model in our dictionary
                        self.stored_models[self.model_key] = self.model.state_dict()
                        
                        # Store intermediate results in our dictionary
                        intermediate_results = {
                            "batch_idx": batch_idx,
                            "loss": loss.item(),
                            "outputs": outputs.logits.detach().cpu().numpy()
                        }
                        
                        intermediate_key = f"epoch_{epoch}_batch_{batch_idx}_results"
                        self.stored_models[intermediate_key] = intermediate_results
                        
                        # Clean up batch from our dictionary
                        if batch_key in self.stored_models:
                            del self.stored_models[batch_key]
                        
                        # Log progress
                        if (batch_idx // batch_size) % 10 == 0:
                            self.log(f"  Batch {batch_idx//batch_size}/{num_batches}, Loss: {loss.item():.4f}")
                        
                        # Track memory usage
                        if torch.cuda.is_available():
                            gpu_memory = get_gpu_stats()
                            if gpu_memory:
                                self.metrics["memory_usage"].append({
                                    "epoch": epoch,
                                    "batch": batch_idx // batch_size,
                                    "gpu_used": gpu_memory["used"],
                                    "gpu_free": gpu_memory["free"]
                                })
                    except Exception as e:
                        self.log(f"Error in batch {batch_idx}: {str(e)}")
                        import traceback
                        self.log(traceback.format_exc())
                        raise
                
                # End of epoch
                avg_epoch_loss = epoch_loss / num_batches
                self.metrics["loss_history"].append(avg_epoch_loss)
                
                # Create checkpoint in our dictionary
                checkpoint = {
                    "epoch": epoch,
                    "model_state": self.stored_models[self.model_key],
                    "optimizer_state": self.optimizer.state_dict(),
                    "loss": avg_epoch_loss
                }
                
                checkpoint_key = f"checkpoint_epoch_{epoch}"
                self.stored_models[checkpoint_key] = checkpoint
                self.checkpoint_keys.append(checkpoint_key)
                
                # Track checkpoint size
                checkpoint_size = len(str(checkpoint))  # Approximate size
                self.metrics["checkpoint_sizes"].append(checkpoint_size)
                
                # Log epoch results
                epoch_time = time.time() - epoch_start_time
                self.log(f"  Epoch {epoch+1} completed in {epoch_time:.2f}s, Avg Loss: {avg_epoch_loss:.4f}")
        except Exception as e:
            self.log(f"Error during training: {str(e)}")
            import traceback
            self.log(traceback.format_exc())
            
        # End of training
        total_time = time.time() - start_time
        self.metrics["training_time"] = total_time
        
        self.log(f"Training completed in {total_time:.2f}s")
        
        # Archive final model to our dictionary
        final_model = self.stored_models[self.model_key]
        final_model_key = "final_model"
        self.stored_models[final_model_key] = final_model
        
        self.log(f"Final model archived")
        
        # Save training metrics
        self._save_metrics()
        
        return True
    
    def _save_metrics(self):
        """Save training metrics to a file."""
        metrics_file = self.output_dir / "training_metrics.txt"
        
        with open(metrics_file, "w") as f:
            f.write(f"LLM Training Metrics\n")
            f.write(f"{'='*50}\n\n")
            
            f.write(f"Total training time: {self.metrics['training_time']:.2f}s\n\n")
            
            f.write(f"Loss history:\n")
            for i, loss in enumerate(self.metrics["loss_history"]):
                f.write(f"  Epoch {i+1}: {loss:.4f}\n")
            
            f.write(f"\nCheckpoint sizes:\n")
            for i, size in enumerate(self.metrics["checkpoint_sizes"]):
                f.write(f"  Checkpoint {i+1}: {size} bytes\n")
            
            f.write(f"\nMemory tier migrations:\n")
            for tier, count in self.metrics["tier_migrations"].items():
                f.write(f"  {tier}: {count}\n")
        
        self.log(f"Training metrics saved to {metrics_file}")
    
    def cleanup(self):
        """Clean up resources."""
        self.log("Cleaning up resources...")
        
        # Clean up memory manager resources
        # Note: MemoryManager doesn't have a cleanup method in the current implementation
        
        # Clean up model
        if hasattr(self, 'model') and self.model is not None:
            del self.model
        
        # Clean up optimizer
        if hasattr(self, 'optimizer') and self.optimizer is not None:
            del self.optimizer
        
        # Clean up CUDA cache if available
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        self.log("Resources cleaned up")
        return True

def main():
    """Main function to run the example."""
    parser = argparse.ArgumentParser(description="LLM Training Optimizer Example")
    parser.add_argument("--model_size", type=str, default="small", choices=["small", "medium", "large"],
                        help="Size of the model to train")
    parser.add_argument("--epochs", type=int, default=3, help="Number of training epochs")
    parser.add_argument("--batch_size", type=int, default=8, help="Batch size for training")
    parser.add_argument("--output_dir", type=str, default="./llm_training_output",
                        help="Directory to save outputs")
    parser.add_argument("--dataset_path", type=str, default=None,
                        help="Path to the dataset file (if None, generates synthetic data)")
    parser.add_argument("--hot_memory", type=int, default=8,
                        help="Size of hot memory (GPU) in GB")
    parser.add_argument("--warm_memory", type=int, default=32,
                        help="Size of warm memory (RAM) in GB")
    parser.add_argument("--cold_memory", type=int, default=500,
                        help="Size of cold memory (SSD) in GB")
    parser.add_argument("--glacier_memory", type=int, default=2048,
                        help="Size of glacier memory (HDD/Cloud) in GB")
    
    args = parser.parse_args()
    
    # Initialize the optimizer
    optimizer = LLMTrainingOptimizer(
        model_size=args.model_size,
        output_dir=args.output_dir,
        hot_memory_size=args.hot_memory,
        warm_memory_size=args.warm_memory,
        cold_memory_size=args.cold_memory,
        glacier_memory_size=args.glacier_memory
    )
    
    try:
        # Initialize model
        optimizer.initialize_model()
        
        # Load training data
        optimizer.load_training_data(args.dataset_path)
        
        # Train the model
        optimizer.train(epochs=args.epochs, batch_size=args.batch_size)
        
    except Exception as e:
        optimizer.log(f"Error: {str(e)}")
    finally:
        # Clean up resources
        optimizer.cleanup()

if __name__ == "__main__":
    main() 