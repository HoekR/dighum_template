# mlx-llm

A lightweight local LLM inference wrapper built on [mlx-lm](https://github.com/ml-explore/mlx-lm), providing:

- **Cached model loading**: In-process model cache keyed by model name, avoiding repeated weight loads
- **Simple generation**: `generate(prompt, model, temperature, max_tokens) -> str | None`
- **Safe error handling**: Never raises; returns `None` on any failure (model load, generation, etc.)
- **Response parsing utilities**:
  - `extract_json(text) -> dict | None`: Find and parse the first JSON object in prose-wrapped output
  - `parses_affirmative(text) -> bool | None`: Distinguish YES/NO responses from ambiguous ones

## Why mlx-lm?

Unlike daemon-based runners (Ollama, LM Studio), mlx-lm is an in-process Python library. No separate process, no HTTP API, no symlink-based model storage — just direct library calls. This trades off broad IDE integration for simpler model lifecycle management and fewer moving parts.

For model storage, mlx-lm uses the standard Hugging Face cache (`~/.cache/huggingface`, configurable via `HF_HOME`), avoiding tool-specific storage location conventions.

## Usage

```python
from mlx_llm import generate, check_available, extract_json

# Check if a model is available (cached or resolvable)
if check_available("mlx-community/Qwen2.5-7B-Instruct-4bit"):
    # Generate with the model
    response = generate(
        prompt="What is the capital of France?",
        model="mlx-community/Qwen2.5-7B-Instruct-4bit",
        temperature=0.0,
        max_tokens=256
    )
    if response:
        print(response)
    else:
        print("Generation failed (model load, inference, or other error)")

# Parse JSON from model output
text = 'The answer is {"capital": "Paris"} I believe.'
data = extract_json(text)
if data:
    print(data)  # {"capital": "Paris"}
```

## Vendoring

This package is designed to be vendored as a plain directory copy (like `data_io`), not installed as a pip dependency:

```bash
# From a consuming project:
cp -r ~/develop/dighum_template/packages/mlx_llm ./mlx_llm
# or
rsync -a ~/develop/dighum_template/packages/mlx_llm/ ./mlx_llm/
```

Add `mlx_llm/` to `.gitignore` in the consuming project to avoid duplicating the vendored copy in version control.

## Model selection

The default model is `mlx-community/Qwen2.5-32B-Instruct-4bit` — **this exact repo id/tag has not been confirmed against Hugging Face**. Before using this package with real data, run a small smoke test with a confirmed-available model to verify the plumbing, then update the default or pass an explicit model name to `generate()`.

## License

Copyright 2026 Rik Hoekstra. Licensed under the Apache License, Version 2.0. See [LICENSE](LICENSE).
