# Groq AI Integration for Big-O Tracker

## Setup

### 1. Get Free Groq API Key

1. Go to https://console.groq.com
2. Sign up for a free account (no credit card required)
3. Create an API key

### 2. Install Groq Package

```bash
pip install groq
```

### 3. Set Environment Variable

**Option A: Create `.env` file** (recommended)

```bash
cd extension/analyzer
cp .env.example .env
# Edit .env and add your API key
```

**Option B: Export in terminal**

```bash
export GROQ_API_KEY="your_api_key_here"
```

**Option C: Add to your shell profile**

Add to `~/.bashrc` or `~/.zshrc`:
```bash
export GROQ_API_KEY="your_api_key_here"
```

## Usage

Once configured, the analyzer will automatically use Groq AI:

1. **AI Analysis** (if API key is set) → More accurate, handles O(√n) and complex patterns
2. **AST Fallback** (if no API key or error) → Fast, handles common patterns

## Available Models

The integration uses `llama-3.3-70b-versatile` by default (fast and accurate).

Other available models:
- `llama-3.1-70b-versatile` - Alternative Llama model
- `mixtral-8x7b-32768` - Mixtral model with large context
- `gemma2-9b-it` - Google's Gemma model

To change the model, edit `ast_parser.py` line with `model="..."`.

## Testing

Test with O(√n) code:

```python
def is_prime(n):
    if n < 2:
        return False
    for i in range(2, int(n**0.5) + 1):
        if n % i == 0:
            return False
    return True
```

**Expected with AI**: `O(sqrt(n))` or `O(√n)`  
**Fallback with AST**: `O(n)`

## Troubleshooting

### "groq package not installed"
```bash
pip install groq
```

### "No API key" - Always uses AST
Set `GROQ_API_KEY` environment variable (see Setup above)

### API errors
- Check your API key is valid
- Ensure you have internet connection
- Groq has generous free tier limits

## Benefits

✅ **Free** - No credit card required  
✅ **Fast** - Sub-second responses  
✅ **Accurate** - Llama 3.3 70B model  
✅ **No browser needed** - Pure Python  
✅ **Automatic fallback** - Uses AST if unavailable
