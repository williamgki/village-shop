import os
import traceback
from datetime import datetime

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from anthropic import Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Anthropic client
api_key = os.getenv("ANTHROPIC_API_KEY")
if not api_key:
    print("WARNING: ANTHROPIC_API_KEY not found. Please set it in environment variables.")
    print("Available env vars:", list(os.environ.keys()))
    raise ValueError("ANTHROPIC_API_KEY is required")

anthropic_client = Client(api_key=api_key)

# Conversation logging
CONVERSATIONS_FILE = "daily_conversations.txt"

# Pydantic models
class Query(BaseModel):
    question: str
    customer_type: str = "general"  # general, returning, first_time

class ResponseModel(BaseModel):
    answer: str

# Dave's personality examples
DAVE_EXAMPLES = """
Q: How do I pay for items?
A: Right, just pop your money in the honesty box there! We take cash - coins or notes, whatever you've got. Just match what the price says on the label. Been running this way for years and folks are brilliant about it. Trust works both ways in our village!

Q: What if I don't have exact change?
A: No worries at all! Take what change you need from the box - there's usually some coins in there. Or if you're a regular, just catch me up next time you're passing. Village life, isn't it? We look after each other.

Q: Are the eggs fresh?
A: Oh yes, lovely fresh eggs from our hens! Collected this morning as always. You can see the date on the box - never more than a day or two old. The girls are free-range and happy, so you get proper golden yolks. Can't beat a fresh village egg!

Q: Do you have milk?
A: Should do! Check the little fridge unit - we get deliveries Tuesday and Friday from the local dairy. All fresh, usually gone by Saturday though - very popular! If we're out, there might be some long-life cartons on the shelf as backup.
"""

def log_conversation(customer_type: str, question: str, answer: str, client_ip: str):
    """Log conversation to daily text file for owner review."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"""
=== {timestamp} ===
Customer Type: {customer_type}
IP: {client_ip}
Question: {question}
Dave's Response: {answer}
---

"""
    
    try:
        with open(CONVERSATIONS_FILE, "a", encoding="utf-8") as f:
            f.write(log_entry)
    except Exception as e:
        print(f"Failed to log conversation: {e}")

def get_dave_prompt(question: str, customer_type: str) -> str:
    """Builds Dave's response prompt."""
    
    customer_context = ""
    if customer_type == "first_time":
        customer_context = "This seems to be someone's first time using the honesty box. Be extra welcoming and explain how things work."
    elif customer_type == "returning":
        customer_context = "This is likely a regular customer. Be friendly and familiar."
    
    return (
        f"You are Dave, the friendly owner of a village honesty box shop. You're warm, helpful, "
        f"and have that genuine village shopkeeper personality. You trust your customers and "
        f"believe in community spirit.\n\n"
        f"You collect customer feedback and pass it to the shop owner who makes decisions about "
        f"products and prices. If customers have suggestions, complaints, or requests, let them "
        f"know you'll pass it along.\n\n"
        f"Examples of how you respond:\n{DAVE_EXAMPLES}\n\n"
        f"{customer_context}\n\n"
        f"Customer asks: {question}\n\n"
        f"Respond as Dave in a helpful, friendly way. Keep it conversational and practical. "
        f"If it's about products, mention what you typically stock. If it's about payment, "
        f"explain the honesty system warmly. If they have feedback, acknowledge it and mention "
        f"you'll pass it to the owner. Stay in character as a genuine village shop assistant.\n\n"
        f"Dave:"
    )

def get_client_ip(request: Request) -> str:
    """Extracts client IP address from request headers."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0]
    return request.client.host if request.client else "unknown"

# Chat endpoint
@app.post("/api/chat", response_model=ResponseModel)
async def chat_endpoint(query: Query, request: Request):
    """Handles customer questions to Dave."""
    client_ip = get_client_ip(request)
    
    try:
        # Build Dave's prompt (no vector database needed)
        prompt = get_dave_prompt(query.question, query.customer_type)

        # Call Anthropic API with Dave's personality
        anth_resp = anthropic_client.messages.create(
            model="claude-3-5-sonnet-latest",
            max_tokens=300,  # Keep responses concise and practical
            temperature=0.7,  # Warm and friendly but consistent
            messages=[{"role": "user", "content": prompt}]
        )

        # Extract answer
        answer_text = ""
        if anth_resp.content and isinstance(anth_resp.content, list) and len(anth_resp.content) > 0:
            if hasattr(anth_resp.content[0], 'text'):
                answer_text = anth_resp.content[0].text

        if not answer_text:
            print(f"Warning: Could not extract text from Anthropic response")
            answer_text = "Sorry, I'm having a bit of trouble right now. Try again in a moment!"

        # Log the conversation for daily review
        log_conversation(query.customer_type, query.question, answer_text, client_ip)

        return ResponseModel(answer=answer_text.strip())

    except Exception as e:
        print(f"Error processing request: {e}")
        traceback.print_exc()
        
        error_response = "Sorry, having a bit of trouble right now. The till's playing up! Try again in a moment."
        
        # Log the error conversation too
        log_conversation(query.customer_type, query.question, f"ERROR: {str(e)}", client_ip)
        
        raise HTTPException(status_code=500, detail=error_response)

# Health check endpoint
@app.get("/api/health")
async def health_check():
    """Simple health check endpoint."""
    return {"status": "healthy", "message": "Dave's shop is open!"}

# Shop info endpoint
@app.get("/api/shop-info")
async def shop_info():
    """Basic shop information."""
    return {
        "name": "Dave's Village Shop",
        "type": "Honesty Box",
        "location": "Village High Street",
        "owner": "Dave",
        "payment_methods": ["Cash (honesty box)", "Exact change preferred"],
        "specialty": "Fresh local produce, eggs, milk, and essentials"
    }

# Download daily conversations (for shop owner)
@app.get("/api/conversations")
async def get_conversations():
    """Download daily conversations for review."""
    try:
        if not os.path.exists(CONVERSATIONS_FILE):
            return {"conversations": "No conversations logged yet today."}
        
        with open(CONVERSATIONS_FILE, "r", encoding="utf-8") as f:
            content = f.read()
        
        return {"conversations": content, "filename": CONVERSATIONS_FILE}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read conversations: {str(e)}")

# Clear daily conversations (for new day)
@app.post("/api/conversations/clear")
async def clear_conversations():
    """Clear the daily conversations file (start fresh for new day)."""
    try:
        if os.path.exists(CONVERSATIONS_FILE):
            # Archive the file with today's date
            today = datetime.now().strftime("%Y-%m-%d")
            archive_name = f"conversations_{today}.txt"
            os.rename(CONVERSATIONS_FILE, archive_name)
            return {"message": f"Conversations archived as {archive_name}"}
        else:
            return {"message": "No conversations to clear"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear conversations: {str(e)}")

# Run the application
if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host=host, port=port, log_level="info")