# Google ADK Research Agent

A powerful AI research assistant that performs multi-step web research with reflection and iterative improvement to provide thorough, well-cited answers to your questions.

## ✨ Features

- **Intelligent Research**: Automatically generates diverse search queries from your questions
- **Comprehensive Analysis**: Performs multiple web searches and synthesizes findings
- **Quality Assurance**: Analyzes research quality and conducts follow-up searches if needed
- **Real-time Updates**: Live progress tracking as research unfolds
- **Flexible Depth**: Choose between quick, thorough, or comprehensive research
- **Proper Citations**: All answers include sources and citations

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js 16+
- Google API Key with Gemini access

### Setup

1. **Clone and install**
```bash
git clone <repository-url>
cd research-google-agent-adk

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# or .venv\Scripts\activate  # Windows

# Install dependencies
pip install -r adk-backend/requirements.txt
```

2. **Configure API key**
```bash
# Copy example environment file
cp .env.example .env

# Edit .env file with your Google API key
nano .env
```

3. **Run the application**
```bash
# Start both frontend and backend
./run_full_stack.sh
```

4. **Access the application**
- Open http://localhost:5173 in your browser
- Backend API available at http://localhost:8000

## 🔍 How to Use

1. **Enter your question** - Type any research question
2. **Select effort level**:
   - **Low**: Quick research (1 search, 1 iteration)
   - **Medium**: Thorough research (3 searches, up to 3 iterations)
   - **High**: Comprehensive research (5 searches, up to 10 iterations)
3. **Choose AI model** - Select between available Gemini models
4. **Submit** - Watch the research progress in real-time
5. **Get results** - Receive a comprehensive answer with citations

## 🛠️ Configuration

### Environment Variables
Create a `.env` file with:
```env
GOOGLE_API_KEY=your-google-api-key-here
GOOGLE_GENAI_USE_VERTEXAI=FALSE
```

### Available Models
- `gemini-2.0-flash` - Fast, efficient research
- `gemini-2.5-flash-preview-04-17` - Latest flash model (default)
- `gemini-2.5-pro-preview-05-06` - Highest quality responses

## 📡 API Reference

### Stream Research Results
**POST** `/api/adk-research-stream`

Request:
```json
{
  "question": "What are the latest advances in quantum computing?",
  "effort_level": "medium",
  "reasoning_model": "gemini-2.5-flash-preview-04-17"
}
```

Response: Server-Sent Events stream with real-time updates

## 🏗️ Architecture

The system uses Google's Agent Development Kit (ADK) with an enhanced orchestrator that manages:
- Query generation from user questions
- Parallel web searches using Google Search API
- Quality analysis and gap identification
- Iterative research loops for comprehensive coverage
- Final answer synthesis with proper citations

## 📄 License

MIT License - see LICENSE file for details