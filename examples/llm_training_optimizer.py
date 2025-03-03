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
from memories.models.load_model import LoadModel
from memories.utils.earth.processors import gpu_stat

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
            hot_memory_size: Size of hot memory (GPU) in GB
            warm_memory_size: Size of warm memory (RAM) in GB
            cold_memory_size: Size of cold memory (SSD) in GB
            glacier_memory_size: Size of glacier memory (HDD/Cloud) in GB
        """
        self.model_size = model_size
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize memory manager
        self.memory_manager = MemoryManager(
            hot_memory_size=hot_memory_size,
            warm_memory_size=warm_memory_size,
            cold_memory_size=cold_memory_size,
            glacier_memory_size=glacier_memory_size
        )
        
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
            f.write(f"  - Hot memory: {self.memory_manager.hot_memory_size} GB\n")
            f.write(f"  - Warm memory: {self.memory_manager.warm_memory_size} GB\n")
            f.write(f"  - Cold memory: {self.memory_manager.cold_memory_size} GB\n")
            f.write(f"  - Glacier memory: {self.memory_manager.glacier_memory_size} GB\n")
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
        gpu_memory = gpu_stat()
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
        self.model_key = self.memory_manager.store(
            "active_model",
            self.model.state_dict(),
            tier="hot",
            priority="high"
        )
        
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
            
            # Generate random input IDs and attention masks
            input_ids = torch.randint(0, 50000, (size[0], size[1]))
            attention_mask = torch.ones_like(input_ids)
            labels = torch.randint(0, 50000, (size[0], size[1]))
            
            self.training_data = {
                "input_ids": input_ids,
                "attention_mask": attention_mask,
                "labels": labels
            }
        
        # Store training data in cold memory (it's large but not accessed frequently)
        self.dataset_key = self.memory_manager.store(
            "training_dataset",
            self.training_data,
            tier="cold",
            compression=True
        )
        
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
        
        # Training loop
        for epoch in range(epochs):
            epoch_start_time = time.time()
            self.log(f"Epoch {epoch+1}/{epochs}")
            
            # Get dataset from cold memory
            dataset = self.memory_manager.retrieve(self.dataset_key)
            
            # Track epoch loss
            epoch_loss = 0.0
            num_batches = len(dataset["input_ids"]) // batch_size
            
            for batch_idx in range(0, len(dataset["input_ids"]), batch_size):
                # Extract batch data
                end_idx = min(batch_idx + batch_size, len(dataset["input_ids"]))
                
                # Load batch data into warm memory
                batch_data = {
                    "input_ids": dataset["input_ids"][batch_idx:end_idx],
                    "attention_mask": dataset["attention_mask"][batch_idx:end_idx],
                    "labels": dataset["labels"][batch_idx:end_idx]
                }
                
                # Move batch to hot memory for processing
                batch_key = self.memory_manager.store(
                    f"batch_{batch_idx}",
                    batch_data,
                    tier="hot"
                )
                
                # Get model from hot memory
                model_state = self.memory_manager.retrieve(self.model_key)
                self.model.load_state_dict(model_state)
                
                # Forward pass
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
                
                # Store updated model in hot memory
                self.memory_manager.update(
                    self.model_key,
                    self.model.state_dict()
                )
                
                # Store intermediate results in warm memory
                intermediate_results = {
                    "batch_idx": batch_idx,
                    "loss": loss.item(),
                    "outputs": outputs.logits.detach().cpu().numpy()
                }
                
                self.memory_manager.store(
                    f"epoch_{epoch}_batch_{batch_idx}_results",
                    intermediate_results,
                    tier="warm"
                )
                
                # Clean up batch from hot memory
                self.memory_manager.delete(batch_key)
                
                # Log progress
                if (batch_idx // batch_size) % 10 == 0:
                    self.log(f"  Batch {batch_idx//batch_size}/{num_batches}, Loss: {loss.item():.4f}")
                
                # Track memory usage
                if torch.cuda.is_available():
                    gpu_memory = gpu_stat()
                    if gpu_memory:
                        self.metrics["memory_usage"].append({
                            "epoch": epoch,
                            "batch": batch_idx // batch_size,
                            "gpu_used": gpu_memory["used"],
                            "gpu_free": gpu_memory["free"]
                        })
            
            # End of epoch
            avg_epoch_loss = epoch_loss / num_batches
            self.metrics["loss_history"].append(avg_epoch_loss)
            
            # Create checkpoint in cold memory
            checkpoint = {
                "epoch": epoch,
                "model_state": self.memory_manager.retrieve(self.model_key),
                "optimizer_state": self.optimizer.state_dict(),
                "loss": avg_epoch_loss
            }
            
            checkpoint_key = self.memory_manager.store(
                f"checkpoint_epoch_{epoch}",
                checkpoint,
                tier="cold",
                metadata={"epoch": epoch, "timestamp": time.time()}
            )
            
            self.checkpoint_keys.append(checkpoint_key)
            
            # Track checkpoint size
            checkpoint_size = len(str(checkpoint))  # Approximate size
            self.metrics["checkpoint_sizes"].append(checkpoint_size)
            
            # Log epoch results
            epoch_time = time.time() - epoch_start_time
            self.log(f"  Epoch {epoch+1} completed in {epoch_time:.2f}s, Avg Loss: {avg_epoch_loss:.4f}")
        
        # End of training
        total_time = time.time() - start_time
        self.metrics["training_time"] = total_time
        
        self.log(f"Training completed in {total_time:.2f}s")
        
        # Archive final model to glacier memory
        final_model = self.memory_manager.retrieve(self.model_key)
        
        self.memory_manager.store(
            "final_model",
            final_model,
            tier="glacier",
            metadata={"training_completed": time.time()}
        )
        
        self.log(f"Final model archived to glacier memory")
        
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
        
        # Clean up memory manager
        self.memory_manager.cleanup()
        
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