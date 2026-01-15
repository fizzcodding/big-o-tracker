# Groq AI Integration - Quick Start

## 1. Install Groq

```bash
pip3 install groq
```

## 2. Get Free API Key

Visit https://console.groq.com and create a free account (no credit card needed).

## 3. Set API Key

```bash
export GROQ_API_KEY="your_api_key_here"
```

Or create `.env` file in `extension/analyzer/`:
```
GROQ_API_KEY=your_api_key_here
```

## 4. Test

Open a Python file in VSCode and run Big-O Tracker analysis. It will now use AI!

## Models Available

- `llama-3.3-70b-versatile` (default) - Fast & accurate
- `llama-3.1-70b-versatile` - Alternative
- `mixtral-8x7b-32768` - Large context
- `gemma2-9b-it` - Google's model

See [GROQ_README.md](file:///home/fizzcodding/Documents/allcodingshit/big-o-tracker/extension/analyzer/GROQ_README.md) for full documentation.
