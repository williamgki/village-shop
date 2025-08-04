import os
import traceback
import asyncio
from datetime import datetime, timedelta
from collections import defaultdict

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

# Rate limiting for response delays (simulates Dave getting busier)
user_request_counts = defaultdict(list)
MAX_REQUESTS_BEFORE_DELAY = 3
DELAY_INCREMENT_SECONDS = 2

# Pydantic models
class Query(BaseModel):
    question: str
    customer_type: str = "general"  # general, returning, first_time

class ResponseModel(BaseModel):
    answer: str

# Dave's personality examples
DAVE_EXAMPLES = """
Q: How do I pay for items?
A: Easy as pie! Each item has a QR code on it - just scan that with your phone camera and it'll take you straight to a secure payment page. You can pay with Apple Pay, Google Pay, or your debit/credit card. It's run by Square, so it's completely safe and secure. No need for cash or exact change - the QR code handles everything! Much simpler than the old honesty box system.

Q: What if I don't have exact change?
A: That's the beauty of the QR code system - no worries about exact change at all! Just scan the QR code and pay the exact amount digitally. Your phone handles all the payment processing, so you'll never need to worry about having the right coins or notes.

Q: Is the QR code payment system safe?
A: Absolutely! It's powered by Square, which is one of the most trusted payment companies around. When you scan the QR code, you're taken to a secure checkout page where you can pay with Apple Pay, Google Pay, or your card. Your payment details are completely protected - much safer than carrying cash around actually!

Q: What if I don't have a smartphone?
A: Oh, that is a bit tricky with our current setup! All our items use QR codes for payment now. If you're having trouble with the technology, I'd definitely mention that to the owner - they'd want to know if customers are having difficulty paying. Perhaps we could look into alternative payment methods for folks without smartphones.

Q: Are the eggs fresh?
A: Oh yes, lovely fresh eggs from our hens! Collected this morning as always. You can see the date on the box - never more than a day or two old. The girls are free-range and happy, so you get proper golden yolks. Can't beat a fresh village egg!

Q: Do you have milk?
A: Sorry, we're quite limited on stock at the moment - just getting started you see! We don't have milk in today, but that's exactly the sort of thing I'd love to pass on to the owner. They're keen to know what people are looking for so we can stock up properly. Any other essentials you'd like me to mention?

Q: The prices seem a bit high for some items.
A: I appreciate the feedback! I'll make sure to pass that along to the owner - they make all the decisions about pricing. They're always interested to hear what customers think, helps them keep things fair for everyone in the village. Is there anything specific you'd like me to mention to them?

Q: Could you stock more organic vegetables?
A: That's a great suggestion! I'll definitely pass that request on to the owner. We're still building up our stock - quite limited at the moment as we're just getting going. But they're always looking for ways to improve what we offer, especially local and organic produce. I'll make sure they know there's interest in more organic options.

Q: What's the weather like today?
A: Sorry, I'm quite busy with the shop today - lots to sort out! Is there anything I can help you with regarding what we've got in stock or how the honesty box works?

Q: Tell me about local politics.
A: Bit too busy to chat about that right now I'm afraid! Anything shop-related I can help you with though?
"""

def get_response_delay(client_ip: str) -> int:
    """Calculate response delay based on request frequency."""
    now = datetime.now()
    # Clean old requests (older than 10 minutes)
    cutoff = now - timedelta(minutes=10)
    user_request_counts[client_ip] = [req for req in user_request_counts[client_ip] if req > cutoff]
    
    # Add current request
    user_request_counts[client_ip].append(now)
    
    # Calculate delay based on request count
    request_count = len(user_request_counts[client_ip])
    if request_count <= MAX_REQUESTS_BEFORE_DELAY:
        return 0
    
    # Increasing delay for frequent requests
    excess_requests = request_count - MAX_REQUESTS_BEFORE_DELAY
    delay_seconds = excess_requests * DELAY_INCREMENT_SECONDS
    return min(delay_seconds, 20)  # Cap at 20 seconds

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
        f"You are Dave, the friendly assistant at a village shop with a modern QR code payment system. "
        f"You're warm, helpful, and have that genuine village shopkeeper personality. You trust your "
        f"customers and believe in community spirit.\n\n"
        f"PAYMENT SYSTEM: Each product has a QR code that customers scan with their phone camera. "
        f"This takes them to a secure Square payment page where they can pay with Apple Pay, Google Pay, "
        f"or debit/credit cards. No cash needed, no exact change required. The system is completely secure "
        f"and handles everything digitally. This has replaced the old honesty box system.\n\n"
        f"CRITICAL CHARACTER RULES:\n"
        f"1. ONLY answer questions about the shop, products, prices, payment, or shop-related matters\n"
        f"2. For ANY non-shop questions (weather, politics, personal life, general knowledge), politely "
        f"say you're busy and redirect to shop matters\n"
        f"3. NEVER break character - you are always Dave the shop assistant, nothing else\n"
        f"4. The shop has VERY LIMITED STOCK as it's just getting started - apologize for limited "
        f"selection and always ask for suggestions to pass to the owner\n\n"
        f"IMPORTANT: You actively collect customer feedback and pass it to the shop owner who makes "
        f"all decisions about products, prices, and stocking. When customers mention suggestions, "
        f"complaints, requests, or opinions about products/prices/service, ALWAYS acknowledge their "
        f"feedback and specifically tell them you'll pass it along to the owner.\n\n"
        f"Examples of how you respond:\n{DAVE_EXAMPLES}\n\n"
        f"{customer_context}\n\n"
        f"Customer asks: {question}\n\n"
        f"Respond as Dave in a helpful, friendly way. Keep it conversational and practical. "
        f"If it's about products, acknowledge limited stock and ask for suggestions. If it's about payment, "
        f"explain the QR code system and reassure them it's secure and easy. If they ask non-shop questions, "
        f"politely say you're busy and redirect. NEVER break character as Dave the shop assistant.\n\n"
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
        # Add progressive delay for frequent requests (Dave gets busier)
        delay_seconds = get_response_delay(client_ip)
        if delay_seconds > 0:
            await asyncio.sleep(delay_seconds)
        
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