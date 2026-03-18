# GGUF Benchmarking & Inspection Tool (v1.5)

A lightweight, Python-based graphical interface for **llama.cpp**'s `llama-cli.exe`. This tool allows users to inspect GGUF model metadata, estimate RAM requirements with visual feedback, and benchmark inference performance on local hardware.

### You can find the [executable in the releases HERE](https://github.com/fabiomatricardi/tkinter-llamaCLI-speedTest/releases/tag/llamacpp)

---


<img src='https://github.com/fabiomatricardi/tkinter-llamaCLI-speedTest/raw/main/GGUF_Bench_v1.5.gif' width=1000>

---

## 🚀 Key Features

* **Model Inspection**: Extract architecture details (layers, embedding length, etc.) without running full inference.
* **Real-time RAM Visualization**: A dynamic bar chart showing OS memory usage, projected model footprint, and free RAM.
* **Performance KPIs**: Automatically captures and displays **Prefill (Prompt) speed** and **Generation speed** in tokens per second (t/s).
* **KV Cache Optimization**: Toggle Q8_0 quantization for K and V caches to save memory on long context windows.
* **Subprocess Management**: Monitors the unique PID of the engine, allowing for graceful termination of "runaway" processes.

---

## 🛠️ How to Use

1. **Browse**: Select a local `.gguf` model file.
2. **Inspect**: Click **"Inspect Model"** to see general information and RAM requirements. This is recommended before running to ensure you have enough available memory.
3. **Run**: Click **"Run Inference"** to discover the actual speed and performance of the model on your CPU/GPU.
4. **Optimize**: If the RAM required for your desired Context length is too high (indicated by a red bar), activate the **Quantize K/V Cache** flags.

---

## 📊 Understanding the Interface

### 1. The RAM Bar

The bar chart provides a safety-first view of your system resources:

* **Grey (OS/Apps)**: Memory currently used by your operating system and other open programs.
* **Blue (Model Total)**: The combined estimate of Model Weights + KV Cache + Compute Buffer.
* **Bright Green (Projected Free)**: The estimated RAM that will remain available after the model is loaded.
* **Red Alert**: If the total usage exceeds 90% of your physical RAM, the status turns red to warn of potential system instability or "swapping".

### 2. Performance Stats

* **Prompt (Prefill)**: How fast the model processes your input prompt.
* **Generation**: The speed at which the model produces new text.

---

## ⚙️ Requirements

* **llama-cli.exe**: This script expects the executable to be in the same folder. Donwload the [full binary ZIP archive from llama.cpp](https://github.com/ggml-org/llama.cpp/releases/download/b8287/llama-b8287-bin-win-cpu-x64.zip) un unzip it in the main project directory
* **Python 3.10+** (if running from source).
* **Dependencies**: `psutil` (for hardware monitoring).

```bash
pip install psutil

```

---

## 🖥️ Technical Details

The app interacts with the `llama-cli.exe` using the following specialized flags to ensure clean data extraction:

* `-st`: Single-turn mode to prevent the engine from idling in a server state.
* `-lv 3`: Log level 3 to capture detailed memory breakdown and architecture metadata.
* `-n 0 --no-display-prompt`: Used during inspection to force the model to exit immediately after loading metadata.

---

## 🛠️ Build as Executable

To create a standalone `.exe` while keeping the engine independent:

```bash
pyinstaller --noconsole --onefile --name "GGUF_Bench_v1.5" TK_GGUF_bench_v1.5.py

```

---

**Would you like me to add a "Troubleshooting" section to the README to handle common llama.cpp errors?**
