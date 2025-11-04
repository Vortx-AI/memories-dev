"""Multi-model inference for comparing results from multiple models."""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import numpy as np

from memories.models.load_model import LoadModel

logger = logging.getLogger(__name__)


class MultiModelInference:
    """Compare and synthesize results from multiple models."""

    def __init__(self, models: Dict[str, LoadModel], consensus_threshold: float = 0.7):
        """Initialize multi-model inference.

        Args:
            models: Dictionary mapping provider names to LoadModel instances
            consensus_threshold: Threshold for consensus agreement (0-1)
        """
        self.models = models
        self.consensus_threshold = consensus_threshold
        self.logger = logging.getLogger(__name__)

    def get_responses(
        self,
        query: str,
        **kwargs
    ) -> Dict[str, Dict[str, Any]]:
        """Get responses from all models in parallel.

        Args:
            query: Input query/prompt
            **kwargs: Additional parameters for model generation

        Returns:
            Dict mapping provider names to their responses
        """
        responses = {}

        with ThreadPoolExecutor(max_workers=len(self.models)) as executor:
            futures = {
                provider: executor.submit(model.get_response, query, **kwargs)
                for provider, model in self.models.items()
            }

            for provider, future in futures.items():
                try:
                    response = future.result(timeout=kwargs.get('timeout', 60))
                    responses[provider] = response
                    self.logger.info(f"Got response from {provider}")
                except Exception as e:
                    self.logger.error(f"Error from {provider}: {str(e)}")
                    responses[provider] = {
                        "text": None,
                        "error": str(e),
                        "metadata": {}
                    }

        return responses

    async def get_responses_async(
        self,
        query: str,
        **kwargs
    ) -> Dict[str, Dict[str, Any]]:
        """Get responses from all models asynchronously.

        Args:
            query: Input query/prompt
            **kwargs: Additional parameters for model generation

        Returns:
            Dict mapping provider names to their responses
        """
        tasks = {
            provider: asyncio.create_task(
                asyncio.to_thread(model.get_response, query, **kwargs)
            )
            for provider, model in self.models.items()
        }

        responses = {}
        for provider, task in tasks.items():
            try:
                response = await task
                responses[provider] = response
                self.logger.info(f"Got async response from {provider}")
            except Exception as e:
                self.logger.error(f"Error from {provider}: {str(e)}")
                responses[provider] = {
                    "text": None,
                    "error": str(e),
                    "metadata": {}
                }

        return responses

    def get_responses_with_earth_memory(
        self,
        query: str,
        location: Dict[str, float],
        earth_memory_analyzers: Optional[List[str]] = None,
        **kwargs
    ) -> Dict[str, Dict[str, Any]]:
        """Get responses with Earth memory integration.

        Args:
            query: Input query/prompt
            location: Location dict with 'lat' and 'lon' keys
            earth_memory_analyzers: List of analyzer names to use
            **kwargs: Additional parameters

        Returns:
            Dict mapping provider names to their responses
        """
        # Build context from Earth memory
        earth_context = self._build_earth_context(location, earth_memory_analyzers)

        # Enhance query with context
        enhanced_query = f"""
        Query: {query}

        Earth Memory Context:
        Location: {location}
        {earth_context}

        Please provide a comprehensive analysis considering the environmental context.
        """

        return self.get_responses(enhanced_query, **kwargs)

    def _build_earth_context(
        self,
        location: Dict[str, float],
        analyzers: Optional[List[str]] = None
    ) -> str:
        """Build Earth memory context string.

        Args:
            location: Location dictionary
            analyzers: List of analyzer names

        Returns:
            Context string
        """
        context_parts = []

        if not analyzers:
            analyzers = ["terrain", "climate", "water"]

        for analyzer in analyzers:
            context_parts.append(f"- {analyzer.title()} analysis requested")

        return "\n".join(context_parts)

    def synthesize_consensus(
        self,
        responses: Dict[str, Dict[str, Any]],
        method: str = "weighted"
    ) -> Dict[str, Any]:
        """Synthesize consensus from multiple responses.

        Args:
            responses: Dict of responses from different models
            method: Consensus method ("weighted", "majority", "best")

        Returns:
            Dict with consensus response
        """
        # Filter out error responses
        valid_responses = {
            provider: resp for provider, resp in responses.items()
            if resp.get("text") and not resp.get("error")
        }

        if not valid_responses:
            return {
                "consensus_text": None,
                "error": "No valid responses to synthesize",
                "confidence": 0.0,
                "contributing_models": []
            }

        if method == "weighted":
            return self._weighted_consensus(valid_responses)
        elif method == "majority":
            return self._majority_consensus(valid_responses)
        elif method == "best":
            return self._best_response(valid_responses)
        else:
            raise ValueError(f"Unknown consensus method: {method}")

    def _weighted_consensus(
        self,
        responses: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Create weighted consensus based on response quality.

        Args:
            responses: Valid responses

        Returns:
            Consensus dict
        """
        # Simple implementation: weight by response length and metadata
        weights = {}
        total_weight = 0

        for provider, response in responses.items():
            text = response.get("text", "")
            metadata = response.get("metadata", {})

            # Weight factors
            length_weight = min(len(text) / 1000, 1.0)  # Normalize to 0-1
            time_weight = 1.0 / max(metadata.get("generation_time", 1.0), 0.1)

            weight = (length_weight + time_weight) / 2
            weights[provider] = weight
            total_weight += weight

        # Normalize weights
        normalized_weights = {
            provider: weight / total_weight
            for provider, weight in weights.items()
        }

        # Select best response as representative
        best_provider = max(normalized_weights, key=normalized_weights.get)
        consensus_text = responses[best_provider]["text"]

        # Calculate confidence as agreement level
        confidence = normalized_weights[best_provider]

        return {
            "consensus_text": consensus_text,
            "error": None,
            "confidence": confidence,
            "contributing_models": list(responses.keys()),
            "weights": normalized_weights,
            "primary_model": best_provider
        }

    def _majority_consensus(
        self,
        responses: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Create consensus based on majority agreement.

        Args:
            responses: Valid responses

        Returns:
            Consensus dict
        """
        # For text responses, this is simplified - just pick the most common length range
        texts = [resp["text"] for resp in responses.values()]

        # Group by length ranges
        length_groups = {}
        for provider, text in zip(responses.keys(), texts):
            length_category = len(text) // 500  # Group by 500 char ranges
            if length_category not in length_groups:
                length_groups[length_category] = []
            length_groups[length_category].append((provider, text))

        # Find majority group
        majority_group = max(length_groups.values(), key=len)
        majority_provider, consensus_text = majority_group[0]

        confidence = len(majority_group) / len(responses)

        return {
            "consensus_text": consensus_text,
            "error": None,
            "confidence": confidence,
            "contributing_models": [p for p, _ in majority_group],
            "total_models": len(responses)
        }

    def _best_response(
        self,
        responses: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Select the best single response.

        Args:
            responses: Valid responses

        Returns:
            Best response dict
        """
        # Score based on length, generation time, and metadata
        scores = {}

        for provider, response in responses.items():
            text = response.get("text", "")
            metadata = response.get("metadata", {})

            # Scoring factors
            length_score = min(len(text) / 1000, 1.0)
            time_score = 1.0 / max(metadata.get("generation_time", 1.0), 0.1)
            token_score = metadata.get("total_tokens", 0) / 1000

            # Combined score
            score = (length_score + time_score + token_score) / 3
            scores[provider] = score

        best_provider = max(scores, key=scores.get)

        return {
            "consensus_text": responses[best_provider]["text"],
            "error": None,
            "confidence": 1.0,
            "contributing_models": [best_provider],
            "best_model": best_provider,
            "scores": scores
        }

    def compare_responses(
        self,
        responses: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Compare responses across models.

        Args:
            responses: Dict of responses from different models

        Returns:
            Comparison analysis
        """
        comparison = {
            "total_models": len(responses),
            "successful_responses": 0,
            "failed_responses": 0,
            "response_lengths": {},
            "generation_times": {},
            "token_counts": {},
            "average_length": 0,
            "average_time": 0
        }

        lengths = []
        times = []

        for provider, response in responses.items():
            if response.get("error"):
                comparison["failed_responses"] += 1
                continue

            comparison["successful_responses"] += 1

            text = response.get("text", "")
            metadata = response.get("metadata", {})

            length = len(text)
            gen_time = metadata.get("generation_time", 0)
            tokens = metadata.get("total_tokens", 0)

            comparison["response_lengths"][provider] = length
            comparison["generation_times"][provider] = gen_time
            comparison["token_counts"][provider] = tokens

            lengths.append(length)
            times.append(gen_time)

        if lengths:
            comparison["average_length"] = np.mean(lengths)
            comparison["std_length"] = np.std(lengths)

        if times:
            comparison["average_time"] = np.mean(times)
            comparison["std_time"] = np.std(times)

        return comparison

    def cleanup(self):
        """Clean up all models."""
        for provider, model in self.models.items():
            try:
                model.cleanup()
                self.logger.info(f"Cleaned up model: {provider}")
            except Exception as e:
                self.logger.error(f"Error cleaning up {provider}: {str(e)}")

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the multi-model system.

        Returns:
            Dict with statistics
        """
        return {
            "total_models": len(self.models),
            "model_providers": list(self.models.keys()),
            "consensus_threshold": self.consensus_threshold
        }
