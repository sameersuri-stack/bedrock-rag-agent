# Bedrock RAG Agent

A document Q&A assistant and tool-calling agent built on Amazon Bedrock.

## What it does
- `ask.py`: answers questions from PDFs stored in S3 using a Bedrock Knowledge Base (S3 Vectors) and cites sources.
- `agent.py`: a Nova Lite agent that chooses between searching the Knowledge Base and calling a live weather API (Open-Meteo).

## Architecture
PDFs in S3 -> Bedrock Knowledge Base (Titan Text Embeddings v2 + S3 Vectors) -> Nova Lite via the Converse API -> tools: `search_docs`, `get_weather`

## Setup
1. Create an S3 bucket and upload text-based PDFs.
2. Create a Bedrock Knowledge Base with S3 Vectors and sync it.
3. Put your Knowledge Base ID in `KB_ID` and your account ID in `MODEL_ARN` (`ask.py`).
4. `pip install boto3`, run `aws configure`, then `py ask.py` or `py agent.py`.

## Lessons learned
- Image-only PDFs index as empty; use text-based PDFs.
- Small models can skip tools or loop, so I added a retry limit and a tool-first system prompt.
- Wikipedia reference sections add noise to retrieval.
