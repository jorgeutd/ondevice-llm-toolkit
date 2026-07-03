# Hi, I'm Jorge 👋

**Staff AI Engineer II – AI Agents** · Columbus, OH

I design and ship production AI systems end to end: multi-agent architectures, on-device and cloud LLM/STT inference, MCP tooling, and the evaluation, observability, and release governance that make them safe to run. 12+ years across data science, ML engineering, and GenAI in retail, insurance, and healthcare.

## 🔭 What I work on

- **AI agents in production** — multi-agent swarm architectures with LangGraph, Azure OpenAI, FastAPI, and Kafka serving tens of thousands of daily interactions; agent evaluation and legacy-app modernization with agentic workflows.
- **On-device inference** — local LLM + speech pipelines on Apple Silicon with llama.cpp and whisper.cpp (GGUF quantization, grammar-constrained decoding with GBNF for production-grade structured outputs), eliminating cloud inference cost and latency where the use case allows.
- **Model Context Protocol (MCP)** — building MCP and FastMCP 2.0 servers so agents can safely operate over real business systems (policy management, claims, billing).
- **Fine-tuning and adaptation** — SFT and alignment of open models (Llama, Gemma, DeBERTa) for function calling, intent recognition, and domain tasks; prompt-guard and content-filtering layers for safe release.
- **AI observability and release governance** — cross-functional benchmarking, LLM-as-judge evaluation pipelines, MLflow tracing, and checksum-governed model release controls.

## 🛠️ Stack

**Agents & orchestration:** LangGraph · LangChain · Strands Agents · LlamaIndex · MCP / FastMCP · OpenAI Responses API

**Inference & serving:** vLLM · SGLang · llama.cpp · whisper.cpp · GGUF · GBNF grammars · Apple Silicon (Metal) · TGI

**Models & fine-tuning:** Hugging Face Transformers · PyTorch · PEFT (LoRA/QLoRA) · AWS SageMaker · Llama · Gemma · Qwen · DeBERTa

**Cloud AI platforms:** AWS Bedrock · Azure OpenAI / AI Foundry · Google Vertex AI (Gemini)

**ML / forecasting:** scikit-learn · TensorFlow · Keras · Sktime · Darts · Prophet · NeuralForecast · statsforecast

**Data & infra:** Python · Rust · SQL (Presto, Snowflake, PostgreSQL, Hive) · CYPHER (Neo4j) · Qdrant · Redis · DynamoDB · Kafka · Docker · Terraform

## 📌 Featured projects

- [`ondevice-llm-toolkit`](https://github.com/jorgeutd/ondevice-llm-toolkit) — macOS-first CLI for benchmarking llama.cpp builds and managing GGUF models locally (speed: tokens/sec, time to first token, memory).
- [`local-agent-bench`](https://github.com/jorgeutd/local-agent-bench) — statistical benchmark for tool calling and structured outputs on local/quantized LLMs, with Wilson confidence intervals and bootstrap comparisons (quality: does your Q4 model still call the right tool?).
- [`swarm-multi-agent-orchestration`](https://github.com/jorgeutd/swarm-multi-agent-orchestration) — multi-agent orchestration patterns.
- [`llm-finetuning-scripts-utils`](https://github.com/jorgeutd/llm-finetuning-scripts-utils) — SFT and alignment training scripts for transformer LMs on SageMaker.

## 🌎 Languages

English · Spanish · Portuguese

## 🔗 Let's connect

<a href="https://www.linkedin.com/in/jorge-lopez-grisman" target="_blank"><img alt="LinkedIn" src="https://img.shields.io/badge/linkedin-%230077B5.svg?&style=for-the-badge&logo=linkedin&logoColor=white" /></a>
<a href="https://twitter.com/jorge_utd" target="_blank"><img alt="Twitter" src="https://img.shields.io/badge/twitter-%231DA1F2.svg?&style=for-the-badge&logo=twitter&logoColor=white" /></a>
