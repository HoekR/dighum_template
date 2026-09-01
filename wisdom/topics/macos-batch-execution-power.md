# macOS Batch Execution & Power Management

**Context:** Long-running local ML/LLM batches, token extraction, or data migrations on Apple Silicon (M-series) Macs with external scratch drives.

---

## The Problem

When running multi-hour or overnight CLI/batch jobs without active user interaction or when the display sleeps:
1. **App Nap & Thread Throttling:** macOS lowers process Quality of Service (QoS) and shifts CPU worker threads from Performance (P) cores to Efficiency (E) cores.
2. **GPU Downclocking:** Without an explicit power assertion, the Apple Silicon Metal/GPU power state is throttled down to save energy.
3. **External Drive Spin-Down:** External NVMe/SSD scratch drives (e.g., `/Volumes/Extreme SSD`) can be aggressively power-managed or unmounted.

---

## The Solution: `caffeinate -dims`

Always wrap long batch jobs in `caffeinate` with full assertion flags:

```bash
caffeinate -dims uv run your-batch-command ...
```

### Flag reference:
- `-d` — Prevent display idle sleep (keeps display state active).
- `-i` — Prevent system idle sleep (keeps SoC at full clock priority).
- `-m` — Prevent disk idle sleep (crucial for external USB/Thunderbolt scratch SSDs).
- `-s` — Prevent system sleep on AC power.

---

## Display Blanking Without Process Throttling

To turn off the physical screen while keeping the background job running at maximum Performance-core clocks:

### Method 1: Instant terminal command
```bash
pmset displaysleepnow
```

### Method 2: Keyboard shortcut
1. Lock screen: `Control + Command + Q`
2. Turn off display: Press `Escape` immediately after locking.

### Method 3: Wrap and sleep
```bash
caffeinate -w $(pgrep -f target_process_name) & pmset displaysleepnow
```
