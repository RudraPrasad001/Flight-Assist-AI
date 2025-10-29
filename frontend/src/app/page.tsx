'use client';

import { useState, useRef, useEffect } from 'react';
import { Send, Plane, User, MessageSquare, Globe, Calendar, MapPin, Clock, Search, Navigation } from 'lucide-react';

interface Message {
  id: number;
  text: string;
  isUser: boolean;
  timestamp: Date;
  apiResponse?: ApiResponse;
}

interface ApiResponse {
  query: string;
  classification: string[];
  results: {
    airports?: Array<[string, string, number, number]>;
    airlines?: Array<[string, string | null, string | null, number, number]>;
    routes?: Array<[string, string, string, string, string, string, string, string, string, number, number]>;
  };
  summary: string;
  total_results: number;
}

const formatApiResponse = (data: ApiResponse): string => {
  let formattedText = `🔍 **Search Results for:** "${data.query}"\n\n`;
  
  const airports = data.results.airports || [];
  const routes = data.results.routes || [];
  const airlines = data.results.airlines || [];
  
  if (airports.length > 0) {
    formattedText += `✈️ **AIRPORTS** (${airports.length})\n`;
    formattedText += `┌─────────────────────────────────────────────┐\n`;
    airports.forEach((airport, index) => {
      const [name, country, id, similarity] = airport;
      formattedText += `│ 🏢 ${name}\n`;
      formattedText += `│    📍 ${country}\n`;
      formattedText += `│    🆔 ID: ${id} | Match: ${(similarity * 100).toFixed(1)}%\n`;
      if (index < airports.length - 1) {
        formattedText += `├─────────────────────────────────────────────┤\n`;
      }
    });
    formattedText += `└─────────────────────────────────────────────┘\n\n`;
  }

  if (routes.length > 0) {
    formattedText += `🛫 **FLIGHT ROUTES** (${routes.length})\n`;
    formattedText += `┌─────────────────────────────────────────────┐\n`;
    routes.forEach((route, index) => {
      const [airlineCode, , sourceCode, sourceName, sourceCity, destCode, destName, destCity, aircraft, id, similarity] = route;
      formattedText += `│ 🌟 ${airlineCode} Flight\n`;
      formattedText += `│    🛫 FROM: ${sourceName} (${sourceCode})\n`;
      formattedText += `│         📍 ${sourceCity}\n`;
      formattedText += `│    🛬 TO: ${destName} (${destCode})\n`;
      formattedText += `│         📍 ${destCity}\n`;
      formattedText += `│    ✈️ Aircraft: ${aircraft.replace(/\r/g, '')} | Match: ${(similarity * 100).toFixed(1)}%\n`;
      if (index < routes.length - 1) {
        formattedText += `├─────────────────────────────────────────────┤\n`;
      }
    });
    formattedText += `└─────────────────────────────────────────────┘\n\n`;
  }

  if (airlines.length > 0) {
    formattedText += `🏢 **AIRLINES** (${airlines.length})\n`;
    formattedText += `┌─────────────────────────────────────────────┐\n`;
    airlines.forEach((airline, index) => {
      const [name, country, code, id, similarity] = airline;
      formattedText += `│ 🏢 ${name || 'Unknown Airline'}\n`;
      if (country) formattedText += `│    📍 ${country}\n`;
      if (code) formattedText += `│    🔤 Code: ${code}\n`;
      formattedText += `│    🆔 ID: ${id} | Match: ${(similarity * 100).toFixed(1)}%\n`;
      if (index < airlines.length - 1) {
        formattedText += `├─────────────────────────────────────────────┤\n`;
      }
    });
    formattedText += `└─────────────────────────────────────────────┘\n\n`;
  }

  formattedText += `📊 **Summary:** ${data.summary}`;
  
  return formattedText;
};

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 0,
      text: "✈️ Welcome to FlightAssist AI! I'm your professional flight assistant. I can help you with flight searches, booking information, travel planning, airport details, airline policies, and any aviation-related questions. How can I assist with your travel needs today?",
      isUser: false,
      timestamp: new Date()
    }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now(),
      text: input,
      isUser: true,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/chat?query=${encodeURIComponent(input)}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      const data = await response.json();

      if (response.ok) {
        const formattedText = formatApiResponse(data);
        const aiMessage: Message = {
          id: Date.now() + 1,
          text: formattedText,
          isUser: false,
          timestamp: new Date(),
          apiResponse: data
        };
        setMessages(prev => [...prev, aiMessage]);
      } else {
        throw new Error(data.error || 'Failed to get response');
      }
    } catch (error) {
      const errorMessage: Message = {
        id: Date.now() + 1,
        text: 'Sorry, something went wrong. Please try again.',
        isUser: false,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const clearChat = () => {
    setMessages([{
      id: 0,
      text: "Hello! I'm your AI assistant. How can I help you today?",
      isUser: false,
      timestamp: new Date()
    }]);
  };

  return (
    <div className="h-screen w-screen bg-gradient-to-br from-sky-50 via-blue-50 to-indigo-50 dark:from-gray-900 dark:via-blue-900 dark:to-indigo-900 overflow-hidden">
      {/* Header */}
      <header className="bg-gradient-to-r from-sky-600 to-blue-700 shadow-lg px-4 py-3 mb-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-white/20 backdrop-blur-sm rounded-lg">
              <Plane className="w-4 h-4 text-white" />
            </div>
            <div>
              <h1 className="text-8 font-bold text-white">
                FlightAssist AI
              </h1>
              <p className="text-sm text-sky-50">Your Professional Flight Assistant</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={clearChat}
              className="p-2 hover:bg-white/20 rounded-lg transition-colors"
              title="Clear chat"
            >
              <MessageSquare className="w-5 h-5 text-white" />
            </button>
            <div className="flex items-center gap-2 text-white">
              <Globe className="w-4 h-4" />
              <span className="text-sm">24/7 Support</span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Chat Area */}
      <main className="flex-1 h-[calc(100vh-76px)] flex flex-col">
        {/* Messages Container */}
        <div className="flex-1 overflow-y-auto px-6 py-4">
          {messages.length === 1 ? (
            <div className="h-full flex items-center justify-center">
              <div className="text-center max-w-2xl">
                <div className="mb-8">
                  <div className="w-24 h-24 bg-gradient-to-br from-sky-400 to-blue-600 rounded-full flex items-center justify-center mx-auto mb-6 shadow-xl">
                    <Plane className="w-8 h-8 text-white" />
                  </div>
                  <h2 className="text-2xl font-bold text-gray-800 dark:text-white mb-3">
                    Welcome to FlightAssist AI
                  </h2>
                  <p className="text-gray-600 dark:text-gray-400 text-lg">
                    Your professional flight companion for seamless travel planning and support
                  </p>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <button
                    onClick={() => setInput("Search flights from New York to London")}
                    className="p-4 text-left bg-white dark:bg-gray-800 border border-sky-200 dark:border-gray-700 rounded-xl hover:border-sky-400 dark:hover:border-sky-600 transition-all hover:shadow-lg group"
                  >
                    <Search className="w-5 h-5 text-sky-600 mb-2 group-hover:scale-110 transition-transform" />
                    <div className="text-sm font-semibold text-gray-800 dark:text-white">Search Flights</div>
                    <div className="text-xs text-gray-500">Find the best deals</div>
                  </button>
                  <button
                    onClick={() => setInput("What are the baggage policies for international flights?")}
                    className="p-4 text-left bg-white dark:bg-gray-800 border border-sky-200 dark:border-gray-700 rounded-xl hover:border-sky-400 dark:hover:border-sky-600 transition-all hover:shadow-lg group"
                  >
                    <Globe className="w-5 h-5 text-blue-600 mb-2 group-hover:scale-110 transition-transform" />
                    <div className="text-sm font-semibold text-gray-800 dark:text-white">Travel Info</div>
                    <div className="text-xs text-gray-500">Policies & guidelines</div>
                  </button>
                  <button
                    onClick={() => setInput("Check flight status for AA 123")}
                    className="p-4 text-left bg-white dark:bg-gray-800 border border-sky-200 dark:border-gray-700 rounded-xl hover:border-sky-400 dark:hover:border-sky-600 transition-all hover:shadow-lg group"
                  >
                    <Clock className="w-5 h-5 text-green-600 mb-2 group-hover:scale-110 transition-transform" />
                    <div className="text-sm font-semibold text-gray-800 dark:text-white">Flight Status</div>
                    <div className="text-xs text-gray-500">Real-time updates</div>
                  </button>
                  <button
                    onClick={() => setInput("Help me plan a trip to Paris")}
                    className="p-4 text-left bg-white dark:bg-gray-800 border border-sky-200 dark:border-gray-700 rounded-xl hover:border-sky-400 dark:hover:border-sky-600 transition-all hover:shadow-lg group"
                  >
                    <MapPin className="w-5 h-5 text-purple-600 mb-2 group-hover:scale-110 transition-transform" />
                    <div className="text-sm font-semibold text-gray-800 dark:text-white">Trip Planning</div>
                    <div className="text-xs text-gray-500">Personalized itineraries</div>
                  </button>
                </div>
              </div>
            </div>
          ) : (
            <div className="max-w-4xl mx-auto space-y-6">
              {messages.slice(1).map((message) => (
                <div
                  key={message.id}
                  className={`flex ${message.isUser ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`flex items-start gap-3 max-w-2xl ${
                      message.isUser ? 'flex-row-reverse' : 'flex-row'
                    }`}
                  >
                    <div
                      className={`w-10 h-10 rounded-full flex items-center justify-center ${
                        message.isUser
                          ? 'bg-gradient-to-r from-sky-500 to-blue-600 text-white'
                          : 'bg-gradient-to-r from-blue-600 to-sky-700 text-white'
                      }`}
                    >
                      {message.isUser ? (
                        <User className="w-5 h-5" />
                      ) : (
                        <Plane className="w-5 h-5" />
                      )}
                    </div>
                    <div
                      className={`px-5 py-3 rounded-2xl ${
                        message.isUser
                          ? 'bg-blue-500 text-white'
                          : 'bg-white dark:bg-gray-800 text-gray-800 dark:text-white border border-gray-200 dark:border-gray-700'
                      } shadow-sm`}
                    >
                      <div className="leading-relaxed">
                        {message.isUser ? (
                          <p>{message.text}</p>
                        ) : (
                          <pre className="whitespace-pre-wrap font-sans text-sm overflow-x-auto">
                            {message.text}
                          </pre>
                        )}
                      </div>
                      <p className="text-xs opacity-70 mt-2">
                        {message.timestamp.toLocaleTimeString()}
                      </p>
                    </div>
                  </div>
                </div>
              ))}
              {isLoading && (
                  <div className="flex justify-start">
                  <div className="flex items-start gap-3 max-w-2xl">
                    <div className="w-10 h-10 rounded-full bg-gradient-to-r from-blue-600 to-sky-700 text-white flex items-center justify-center">
                      <Plane className="w-5 h-5" />
                    </div>
                    <div className="px-5 py-3 rounded-2xl bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 shadow-sm">
                      <div className="flex space-x-1">
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-75"></div>
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-150"></div>
                      </div>
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* Input Area */}
        <div className="bg-white/80 dark:bg-gray-800/80 backdrop-blur-md border-t border-gray-200/50 dark:border-gray-700/50 px-6 py-4">
          <div className="max-w-4xl mx-auto">
            <div className="flex gap-3 items-end">
              <div className="flex-1 relative">
                <textarea
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Type your message here..."
                  className="w-full px-4 py-3 pr-12 border border-gray-300 dark:border-gray-600 rounded-2xl focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white resize-none"
                  rows={1}
                  style={{ minHeight: '48px', maxHeight: '120px' }}
                  onInput={(e) => {
                    const target = e.target as HTMLTextAreaElement;
                    target.style.height = '48px';
                    target.style.height = Math.min(target.scrollHeight, 120) + 'px';
                  }}
                />
              </div>
              <button
                onClick={sendMessage}
                disabled={!input.trim() || isLoading}
                className="p-3 bg-gradient-to-r from-sky-500 to-blue-600 text-white rounded-2xl hover:from-sky-600 hover:to-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 transform hover:scale-105 active:scale-95 shadow-lg"
              >
                <Send className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
