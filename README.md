**🧠 OutsystemLogsAI**

This project demonstrates how to build a Retrieval-Augmented Generation (RAG) system to assist developers with OutSystems-related issues, using open-source LLMs (Mistral and Phi-3) via Ollama.

🚀 Features

✅ Custom dataset of OutSystems problems & solutions (from real logs from outsystems forums)

✅ Preprocessing scripts (cleaning, base64 conversion, web scraping)

✅ Image screenshots from OutSystems forums were automatically converted into descriptive text using Google Gemini LLM, enriching the dataset

✅ Smart document ranking with keyword & screenshot metadata

✅ LangChain-based RAG setup

✅ Works with either Mistral or Phi-3 (via Ollama)

📦 Requirements

Install the required dependencies:

-pip install langchain faiss-cpu transformers

To use Ollama LLMs:


-curl -fsSL https://ollama.com/install.sh | sh

-ollama run mistral

-ollama run phi3

📊 Dataset

The dataset is enriched with real-world problems and solutions from OutSystems forums. It includes:

-Cleaned text from user posts

-Automatically generated image descriptions (from forum screenshots)

-Keyword-based metadata (e.g., technical keywords, error detection)

📥 Available on Kaggle:

https://www.kaggle.com/datasets/mohamedanoun/final-dataset

Note: You can directly run the notebooks using this dataset — it's already preprocessed and ready for implementing the RAG models.

Make sure to download and place it in the appropriate location in the repo.

🧪 Notebooks
Notebook                                              	Description
Generating-Model-With-RAG-Using-Mistral.ipynb	          Implements RAG pipeline using Mistral via Ollama
Generating-Model-With-RAG-Using-Phi3.ipynb	            Implements RAG pipeline using Phi-3 via Ollama

💡 Use Case
This system can be used by OutSystems developers and support engineers to:

-Understand errors from logs

-Get fast, structured troubleshooting advice

-Leverage past support cases to avoid reinventing the wheel

🧠 How It Works

The system follows dual logic:

🧩 If similar logs exist in the dataset:

RAG retrieves the most relevant documents and provides a structured answer based on historical context.

🧠 If no similar logs are found:

The LLM falls back to a general reasoning mode and generates a custom solution using its own knowledge base.

📊 Model Comparison
Model	              Accuracy	            Recommendation
Phi-3	              86.67%	              ✅ Recommended
Mistral	            75.83%	               Optional

You can choose either model by switching a single parameter in the notebook.
However, Phi-3 is recommended for better accuracy and reasoning in technical cases.
