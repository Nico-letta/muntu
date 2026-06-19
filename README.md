# MUNTU LLM 

MUNTU is an autoregressive large language model based on the Transformer architecture (decoder-only) and implemented from scratch in PyTorch. It features a sparse Mixture of Experts (MoE) Top-1 routing mechanism designed to optimize computational efficiency and enable modular parameter specialization across distinct training domains.

This repository serves as a **functional validation of the architecture (Proof of Concept)**. The pipeline is currently validated on a scaled-down composite dataset (source code, technical specifications, and regulatory frameworks), demonstrating routing stability and loss convergence on CPU infrastructures prior to scaling up the vocabulary and data workloads.

---

##  Strategic Positioning & Core Differentiators

MUNTU distinguishes itself from global, large-scale language models through two primary pillars:

* **Computational Efficiency (Sparse MoE):** The *Sparse MoE Top-1* routing approach expands the model's total parameter capacity (knowledge retention) while maintaining a low inference cost. This architecture makes deployment and execution viable on local hardware (standard servers or workstations), removing strict dependencies on massive cloud infrastructures.
* **Contextual Sovereignty:** The model explicitly targets the semantic and technical blind spots of Western-centric LLMs. MUNTU natively integrates regional business logic, local regulatory frameworks, and regional fintech infrastructures (e.g., Mobile Money ecosystems) specific to the African context into its pre-training strategy.

---

##  Architectural Specifications

The software implementation complies with rigorous Deep Learning engineering standards to ensure network stability under scaling:

* **Base Model:** Decoder-only Transformer architecture optimized for autoregressive sequence learning.
* **Normalization (Pre-LN):** Layer normalization (`LayerNorm`) applied at the input of each sub-block (Attention and MoE) to stabilize gradient propagation and prevent training divergence.
* **Attention Mechanism:** Multi-head causal attention (`MuntuCausalAttention`) with strict lower-triangular future masking.
* **Sparse MoE Routing:** Dynamic *Top-1 Routing* gating system distributing tokens to a set of independent feed-forward experts (`MuntuExpert`). Total expert capacity is fully parameterizable (configured to 4 experts by default).
* **Gating Control (Anti-Collapse):** In-flight calculation of an auxiliary **Load Balancing Loss** (weighted at `0.01`) to enforce uniform token distribution across experts and prevent single-expert monopoly.

---

##  Project Structure

```text
muntu/
├── data_engine/                 # Data ingestion and pre-processing pipeline
│   ├── corpus_raw/              # Raw source datasets categorized by domain
│   │   ├── 00-core-principles/  # Architecture guidelines and performance standards
│   │   ├── 01-react-native/     # UI optimizations and memoization rules
│   │   ├── 02-fintech-local/    # Mobile Money data structures and regional regulations
│   │   └── 10-case-studies/     # Interface (UI) implementation case studies
│   ├── _output/                 # Generated training artifacts
│   │   ├── muntu_tokenizer/     # BPE Tokenizer assets (vocab.json, merges.txt)
│   │   └── corpus_pretrain.txt  # Unified, model-ready pre-training corpus
│   └── generate_corpus.py       # Source aggregation, deduplication, and cleaning
├── model_engine/                # Core model architecture and execution layer
│   ├── src/                     # Core engine source code
│   │   ├── attention.py         # Multi-head causal attention mechanics
│   │   ├── dataset.py           # Tokenized text loading and batching pipeline
│   │   ├── embedding.py         # Unified Token & Positional Embedding management
│   │   ├── model.py             # Main MuntuLM definition (Logits & combined Loss)
│   │   ├── moe_layer.py         # Top-1 gating logic and Load Balancing Loss
│   │   └── transformer_block.py # Pre-LN Transformer blocks coupled with MoE layers
│   ├── tokenizer_core/          # Tokenizer training engine
│   │   └── train_tokenizer.py   # Byte-Pair Encoding (BPE) training script
│   ├── test_bench.py            # Autoregressive generation suite (Temperature, Top-K, Top-P)
│   └── train.py                 # Training script with OS-level checkpoint archiving
├── main.py                      # Application entry point
├── LICENSE                      # Apache 2.0 License
└── README.md                    # Technical documentation