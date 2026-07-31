# MUNTU LLM

MUNTU is a Sparse Mixture of Experts Large Language Model built in PyTorch. It utilizes a Transformer (decoder-only) architecture optimized for computational efficiency and the integration of specialized knowledge.

## Project Status
- **Current Phase:** Proof of Concept (PoC) / Architectural Validation
- **Status:** Training pipeline validated, training/inference loops operational on CUDA infrastructure.
- **Goal:** Enable local execution of LLMs specialized in African fintech and regulatory ecosystems.

## Key Technical Features

* **Sparse MoE Architecture:** Implementation of a *Top-1 routing* mechanism. This distributes tokens to independent feed-forward experts, decoupling the number of parameters from inference latency.
* **Contextual Integration:** Designed for domain-specific pre-training, focusing on regional business logic, regulatory frameworks, and financial infrastructures (e.g., Mobile Money ecosystems).
* **Training Stability:** Features Pre-LN normalization for gradient propagation and an auxiliary *Load Balancing Loss* to prevent expert collapse.

## Technical Specifications

| Feature | Specification |
| :--- | :--- |
| **Framework** | PyTorch |
| **Architecture** | Transformer Decoder-only |
| **Routing** | Sparse Top-1 MoE |
| **Normalization** | Pre-LN (LayerNorm) |
| **Attention** | Multi-head causal attention (causal masking) |
| **Gating Control** | Auxiliary Load Balancing Loss |

## Roadmap

### Phase 1: Architectural Validation (Completed)
- [x] Implementation of core Transformer blocks.
- [x] Development of the Sparse MoE Top-1 routing mechanism.
- [x] Integration of Load Balancing Loss.
- [x] Validation of training/inference loops on test dataset.

### Phase 2: Scaling & Benchmarking (In Progress)
- [>] Optimization of training pipeline for GPU/CUDA environments (AMP/Mixed Precision).
- [>] Latency and throughput benchmarking on local hardware.
- [>] Hyperparameter tuning for larger vocabulary and context windows.
- [>] Metric monitoring (Loss, Perplexity, Expert distribution) via TensorBoard.

### Phase 3: Domain Integration & Deployment (Planned)
- [ ] Tokenizer adaptation for regional linguistic specificities.
- [ ] Pre-training on domain-specific corpora (Fintech, Legal, Tech Specs).
- [ ] Fine-tuning for Mobile Money ecosystems and local trade logic.
- [ ] Inference pipeline productionization.
