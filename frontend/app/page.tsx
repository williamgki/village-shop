"use client";

import { useState, useRef, useEffect } from 'react';
import { Send, ShoppingBasket, HelpCircle } from 'lucide-react';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

const SuggestedQuestions = ({ onQuestionClick }: { onQuestionClick: (question: string) => void }) => {
  const questions = [
    "How do I pay for items?",
    "What if I don't have exact change?",
    "Are the eggs fresh today?",
    "Do you have milk available?",
    "What payment methods do you accept?",
    "How does the honesty box work?"
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 mb-6">
      {questions.map((question, idx) => (
        <button
          key={idx}
          onClick={() => onQuestionClick(question)}
          className="p-3 bg-green-50 hover:bg-green-100 border border-green-200 rounded-lg
                     text-green-800 text-sm font-medium transition-all duration-200
                     hover:shadow-md focus:outline-none focus:ring-2 focus:ring-green-500/50
                     text-left"
        >
          {question}
        </button>
      ))}
    </div>
  );
};

const ChatMessage = ({ message }: { message: Message }) => {
  const isUser = message.role === 'user';
  
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      <div className={`max-w-[80%] p-4 rounded-lg ${
        isUser 
          ? 'bg-green-600 text-white' 
          : 'bg-white border border-gray-200 text-gray-800'
      }`}>
        <div className="text-sm font-medium mb-1">
          {isUser ? 'You' : 'Dave'}
        </div>
        <div className="whitespace-pre-wrap">{message.content}</div>
        <div className="text-xs opacity-70 mt-2">
          {new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </div>
      </div>
    </div>
  );
};

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [customerType, setCustomerType] = useState<'general' | 'first_time' | 'returning'>('general');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMessage = input;
    setMessages(prev => [...prev, { 
      role: 'user', 
      content: userMessage, 
      timestamp: new Date().toISOString()
    }]);
    setLoading(true);
    setInput('');

    try {
      const response = await fetch(process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          question: userMessage,
          customer_type: customerType
        })
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Failed to get response from Dave');
      }

      setMessages(prev => [...prev, {
        role: 'assistant',
        content: data.answer,
        timestamp: new Date().toISOString()
      }]);

    } catch (error) {
      console.error('Error:', error);
      
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: "Sorry, I'm having a bit of trouble right now. The till's playing up! Try again in a moment.",
        timestamp: new Date().toISOString()
      }]);
    } finally {
      setLoading(false);
    }
  };

  const handleSuggestedQuestionClick = (question: string) => {
    setInput(question);
  };

  const handleClearConversation = () => {
    setMessages([]);
  };

  return (
    <main className="min-h-screen bg-gradient-to-br from-green-50 to-blue-50">
      <div className="container mx-auto px-4 py-8 max-w-4xl">
        <div className="bg-white rounded-2xl shadow-xl p-6 sm:p-8">
          {/* Header */}
          <div className="text-center mb-8">
            <div className="flex justify-center items-center gap-3 mb-4">
              <ShoppingBasket className="w-8 h-8 text-green-600" />
              <h1 className="text-3xl font-bold text-gray-800">Dave&apos;s Village Shop</h1>
            </div>
            <p className="text-gray-600">Honest prices, friendly service • Ask Dave anything!</p>
          </div>

          {/* Customer Type Selector */}
          <div className="mb-6 flex justify-center">
            <div className="bg-gray-50 rounded-lg p-1 flex">
              <button
                onClick={() => setCustomerType('first_time')}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-all ${
                  customerType === 'first_time' 
                    ? 'bg-white text-green-600 shadow-sm' 
                    : 'text-gray-600 hover:text-gray-800'
                }`}
              >
                First Visit
              </button>
              <button
                onClick={() => setCustomerType('general')}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-all ${
                  customerType === 'general' 
                    ? 'bg-white text-green-600 shadow-sm' 
                    : 'text-gray-600 hover:text-gray-800'
                }`}
              >
                General
              </button>
              <button
                onClick={() => setCustomerType('returning')}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-all ${
                  customerType === 'returning' 
                    ? 'bg-white text-green-600 shadow-sm' 
                    : 'text-gray-600 hover:text-gray-800'
                }`}
              >
                Regular Customer
              </button>
            </div>
          </div>

          {/* Suggested Questions */}
          {messages.length === 0 && (
            <>
              <div className="flex items-center gap-2 mb-4">
                <HelpCircle className="w-5 h-5 text-green-600" />
                <h2 className="text-lg font-semibold text-gray-800">Common Questions</h2>
              </div>
              <SuggestedQuestions onQuestionClick={handleSuggestedQuestionClick} />
            </>
          )}

          {/* Chat Input */}
          <form onSubmit={handleSubmit} className="flex gap-3 mb-6">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask Dave about the shop, products, or how to pay..."
              className="flex-1 p-4 border border-gray-300 rounded-xl text-gray-800 
                         focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent
                         placeholder-gray-500"
              disabled={loading}
              maxLength={500}
            />
            <button
              type="submit"
              disabled={loading || !input.trim()}
              className="px-6 py-4 bg-green-600 text-white rounded-xl hover:bg-green-700 
                         disabled:bg-gray-300 disabled:cursor-not-allowed
                         transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-green-500"
            >
              <Send className="w-5 h-5" />
            </button>
          </form>

          {/* Chat Messages */}
          {messages.length > 0 && (
            <>
              <div className="flex justify-between items-center mb-4">
                <div className="text-sm font-medium text-gray-600">
                  Chat with Dave
                </div>
                <button
                  onClick={handleClearConversation}
                  className="text-sm font-medium text-red-500 hover:text-red-700 px-3 py-1 rounded-full 
                             hover:bg-red-50 transition-all duration-200"
                >
                  Clear chat
                </button>
              </div>
              
              <div className="h-[400px] overflow-y-auto bg-gray-50 rounded-xl p-4 mb-4">
                {messages.map((message, idx) => (
                  <ChatMessage key={idx} message={message} />
                ))}
                
                {loading && (
                  <div className="flex justify-start mb-4">
                    <div className="bg-white border border-gray-200 p-4 rounded-lg">
                      <div className="flex items-center space-x-3">
                        <div className="flex space-x-1">
                          <div className="w-2 h-2 bg-green-500 rounded-full animate-bounce"></div>
                          <div className="w-2 h-2 bg-green-500 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
                          <div className="w-2 h-2 bg-green-500 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
                        </div>
                        <span className="text-gray-600 font-medium">Dave is thinking...</span>
                      </div>
                    </div>
                  </div>
                )}
                
                <div ref={messagesEndRef} />
              </div>
            </>
          )}

          {/* Footer */}
          <div className="text-center text-sm text-gray-500 mt-6">
            <p>🏪 Honesty Box System • Pay what&apos;s fair • Village trust since 1987</p>
          </div>
        </div>
      </div>
    </main>
  );
}
