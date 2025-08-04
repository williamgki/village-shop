# Village Shop - Dave's Honesty Box Assistant

A friendly AI assistant for village honesty box vending machines, powered by Dave's warm personality and local knowledge.

## Overview

Village Shop is a customer service chatbot designed for honesty box vending machines. Dave, the virtual shop owner, helps customers with questions about products, payments, and how the honesty system works.

## Architecture

```
Frontend (Next.js) → Backend (FastAPI) → Cohere (embeddings) → Pinecone (vector DB) → Claude (AI responses)
```

## Features

- **Dave's Personality**: Warm, friendly village shop owner character
- **Customer Types**: Tailored responses for first-time visitors, regulars, and general customers
- **Honesty Box Focus**: Specialized knowledge about payment systems, product freshness, and village shop operations
- **Clean UI**: Simple, accessible interface perfect for touch screens

## Project Structure

```
village-shop/
├── backend/
│   ├── main.py              # FastAPI application
│   ├── requirements.txt     # Python dependencies
│   ├── Procfile            # Railway deployment
│   └── railway.toml        # Railway configuration
├── frontend/
│   ├── app/
│   │   └── page.tsx        # Main chat interface
│   ├── package.json        # Node.js dependencies
│   └── tailwind.config.ts  # Styling configuration
└── README.md
```

## Getting Started

### Backend Setup

1. **Install dependencies:**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Set environment variables:**
   ```bash
   # Create .env file with:
   COHERE_API_KEY=your_cohere_key
   PINECONE_API_KEY=your_pinecone_key
   ANTHROPIC_API_KEY=your_anthropic_key
   ```

3. **Run locally:**
   ```bash
   python main.py
   # Server runs on http://localhost:8000
   ```

### Frontend Setup

1. **Install dependencies:**
   ```bash
   cd frontend
   npm install
   ```

2. **Set environment variables:**
   ```bash
   # Create .env.local file with:
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```

3. **Run locally:**
   ```bash
   npm run dev
   # App runs on http://localhost:3000
   ```

## Deployment

### Backend (Railway)
- Deploy `backend/` folder to Railway
- Set environment variables in Railway dashboard
- Uses `Procfile` and `railway.toml` for configuration

### Frontend (Vercel)
- Deploy `frontend/` folder to Vercel
- Set `NEXT_PUBLIC_API_URL` to your Railway backend URL
- Automatic deployments from Git

## API Endpoints

- `POST /api/chat` - Main chat endpoint
- `GET /api/health` - Health check
- `GET /api/shop-info` - Shop information

## Dave's Character

Dave is designed to be:
- **Warm & Welcoming**: Friendly village shop owner personality
- **Trustworthy**: Explains the honesty system with confidence
- **Practical**: Focuses on helpful, actionable advice
- **Local**: Uses village-appropriate language and references

## Customization

To adapt for different shops:
1. Update `DAVE_EXAMPLES` in `backend/main.py`
2. Modify suggested questions in `frontend/app/page.tsx`
3. Adjust branding and colors in Tailwind config
4. Update shop info in `/api/shop-info` endpoint

## Requirements

- **Backend**: Python 3.8+, FastAPI, Pinecone, Cohere, Anthropic
- **Frontend**: Node.js 18+, Next.js 15, React 19, Tailwind CSS
- **Services**: Pinecone vector database, Cohere embeddings, Claude AI

## License

Built for village communities - use freely and spread the honesty! 🏪

**Live Demo**: Coming soon!