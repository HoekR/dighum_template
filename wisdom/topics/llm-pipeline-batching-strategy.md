# LLM Pipeline Batching Strategy: Local Prototyping to HPC Scaling

**Context:** Large-scale historical text annotation pipelines (e.g. TRIFECTA, FrameNet, NER, information extraction) across hundreds of thousands of passages.

---

## Architecture: Staged Execution vs Single-Pass

Multi-stage extraction pipelines (e.g. Step A entity validation $\rightarrow$ Step B macro classification $\rightarrow$ Step C fine qualia/slot extraction) should avoid monolithic execution over raw corpora.

### 1. Early Dropout Filtering (Lightweight Step A first)
- **Problem:** Running a full A $\rightarrow$ B $\rightarrow$ C structured output prompt on uncurated KWIC snippets spends ~70% of LLM compute on non-relevant or metaphoric passages.
- **Strategy:** Run a fast, lightweight Step A filter in bulk first.
- **Impact:** Discards 20–40% of non-food/irrelevant instances in 1 fast call, halving total inference time for subsequent Steps B & C.

### 2. Hybrid Pre-Filtering with Small Language Models (SLMs / Fine-Tuned Encoders)
- **Problem:** Generative LLMs with structured outputs (`instructor` / JSON schemas) have high latency (3–15 seconds per record on local hardware).
- **Strategy:** Train or fine-tune an encoder model (e.g. GijsBERT, RoBERTa) on gold/silver data as a fast macro-filter or `NONE` detector.
- **Throughput:** An encoder processes 1,000+ items/minute on local CPU/GPU, routing only ambiguous or positive candidate frames to the generative LLM.

### 3. Scaling Tiers

| Tier | Workload | Engine | Expected Throughput |
|------|----------|--------|---------------------|
| **Local (Apple Silicon M4)** | Prototyping, gold evaluation, few-shot calibration, batches up to ~5k–10k rows | Ollama + `instructor` (Metal GPU offload) | ~200–500 rows/hour |
| **Local SLM Filter** | Bulk filtering across ~100k+ candidate snippets | Hugging Face Transformers / PyTorch | ~10k–50k rows/hour |
| **HPC / Cloud (SURF Dual A10 GPUs)** | Full corpus annotation (~100k–1M+ rows) | `vLLM` (tensor parallelism, continuous batching) + `instructor`/`outlines` | ~5k–20k rows/hour |

---

## Operational Rule of Thumb
- **Do not run 50k+ full A $\rightarrow$ B $\rightarrow$ C LLM passes locally.**
- Stage local work: Filter with Step A or SLM first $\rightarrow$ batch survivor slices $\rightarrow$ scale massive corpus passes to HPC via `vLLM`.
