'use client';

import { useState, useRef, useEffect } from 'react';
import { Send, Plane, User, MessageSquare, Globe, Calendar, MapPin, Clock, Search, Navigation, Building2, Route, Users, Link } from 'lucide-react';
import {MapWidget} from "../../components/MapComponent"

interface Message {
  id: number;
  text: string;
  isUser: boolean;
  timestamp: Date;
  apiResponse?: ApiResponse;
}

// Map types mirroring backend utils/route_map.py
export type MapAirport = {
  code?: string | null;
  iata?: string | null;
  icao?: string | null;
  name: string;
  city: string;
  country: string;
  latitude: number;
  longitude: number;
};

export type DirectRoute = {
  route_id: number;
  src: string;
  dst: string;
  src_city: string;
  src_country: string;
  dst_city: string;
  dst_country: string;
  airline: string;
  airline_code: string;
  equipment: string;
  stops: number;      // always 0 for direct
  type: 'direct';
};

export type LayoverRoute = {
  src: string;
  hub: string;
  dst: string;
  hub_name: string;
  hub_city: string;
  hub_country: string;
  hub_latitude: number | null;
  hub_longitude: number | null;
  leg1_airline: string;
  leg2_airline: string;
  leg1_equipment: string;
  leg2_equipment: string;
  leg1_rid: number;
  leg2_rid: number;
  stops: number;      // 1 for one-stop
  type: 'layover';
};

export type MapData = {
  airports: MapAirport[];
  direct_routes: DirectRoute[];
  layover_routes: LayoverRoute[];
};

// Your existing response with map fields added
export interface ApiResponse {
  query: string;
  classification: string[];
  results: {
    airports?: Array<[string, string, number, number]>;
    airlines?: Array<[string, string | null, string | null, number, number]>;
    routes?: Array<[string, string, string, string, string, string, string, string, string, number, number]>;
  };
  summary: string;
  total_results: number;
  // NEW
  has_map?: boolean;
  map_data?: MapData | null;
}


// Utility function to get airport code from name
const getAirportCode = (airportName: string): string => {
  // Try to extract common airport codes or use first 3 letters of city name
  const codeMap: { [key: string]: string } = {
    'Chennai International Airport': 'MAA',
    'Mumbai': 'BOM',
    'Delhi': 'DEL',
    'Bangalore': 'BLR',
    'Kolkata': 'CCU',
    'Hyderabad': 'HYD',
    'Pune': 'PNQ',
    'Ahmedabad': 'AMD',
    'Kochi': 'COK',
    'Goa': 'GOI',
    'Tokyo Haneda International Airport': 'HND',
    'Tokyo Narita': 'NRT',
    'London Heathrow': 'LHR',
    'New York JFK': 'JFK',
    'Dubai': 'DXB',
    'Kempegowda International Airport': 'BLR',
    'Beijing Capital International Airport': 'PEK',
    'Shanghai Hongqiao International Airport': 'SHA',
    'Singapore Changi Airport': 'SIN'
  };
  
  // Check if we have a direct mapping
  for (const [key, code] of Object.entries(codeMap)) {
    if (airportName.toLowerCase().includes(key.toLowerCase())) {
      return code;
    }
  }
  
  // Fallback: use first 3 letters of the first word (usually city name)
  return airportName.substring(0, 3).toUpperCase();
};

// Utility function to generate booking URL in Goibibo format
const generateBookingURL = (fromCode: string, toCode: string): string => {
  const today = new Date();
  const dateStr = `${today.getDate().toString().padStart(2, '0')}/${(today.getMonth() + 1).toString().padStart(2, '0')}/${today.getFullYear()}`;
  
  return `https://www.goibibo.com/flight/search?itinerary=${fromCode}-${toCode}-${dateStr}&tripType=O&paxType=A-1_C-0_I-0&intl=false&cabinClass=E&lang=eng`;
};

// Card Components
const AirportCard = ({ airport }: { airport: [string, string, number, number] }) => {
  const [name, country, id, similarity] = airport;

  return (
    <div className="bg-gradient-to-r from-blue-50 to-sky-50 dark:from-gray-800 dark:to-gray-750 border border-blue-200 dark:border-gray-600 rounded-xl p-4 shadow-sm hover:shadow-md transition-all">
      <div className="flex items-start gap-3">
        <div className="w-10 h-10 bg-blue-500 rounded-full flex items-center justify-center">
          <Building2 className="w-5 h-5 text-white" />
        </div>
        <div className="flex-1">
          <h3 className="font-semibold text-gray-800 dark:text-white">{name}</h3>
          <div className="flex items-center gap-2 mt-1">
            <MapPin className="w-4 h-4 text-gray-500" />
            <span className="text-sm text-gray-600 dark:text-gray-400">{country}</span>
          </div>
          <div className="flex items-center justify-between mt-2">
            <span className="text-xs text-gray-500">ID: {id}</span>
            <span className="text-xs bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300 px-2 py-1 rounded-full">
              {(similarity * 100).toFixed(1)}% match
            </span>
          </div>
          
          {/* Search Flights Button */}
          <div className="mt-3 pt-3 border-t border-blue-200 dark:border-gray-600">
            <button
              onClick={() => {
                const fromCode = getAirportCode(name);
                // Use a popular destination based on the country or default to DEL
                const defaultDestination = country === 'India' ? 'BOM' : 
                                         country === 'United Kingdom' ? 'BOM' :
                                         country === 'Japan' ? 'NRT' : 'DEL';
                window.open(generateBookingURL(fromCode, defaultDestination), '_blank');
              }}
              className="w-full bg-gradient-to-r from-blue-500 to-sky-500 hover:from-blue-600 hover:to-sky-600 text-white font-medium py-2 px-4 rounded-lg transition-all duration-200 transform hover:scale-105 shadow-md hover:shadow-lg text-sm"
            >
              ✈️ Search Flights from {getAirportCode(name)}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

const RouteCard = ({ route }: { route: [string, string, string, string, string, string, string, string, string, number, number] }) => {
  const [airlineCode, airline, fromCode, fromAirport, fromCity, toCode, toAirport, toCity, aircraft, id, similarity] = route;
  
  return (
    <div className="bg-gradient-to-r from-orange-50 to-red-50 dark:from-gray-800 dark:to-gray-750 border border-orange-300 dark:border-orange-500 rounded-xl p-4 shadow-lg hover:shadow-xl transition-all">
      <div className="flex items-start gap-3">
        <div className="w-10 h-10 bg-orange-500 rounded-full flex items-center justify-center shadow-md">
          <Route className="w-5 h-5 text-white" />
        </div>
        <div className="flex-1">
          <div className="flex items-center justify-between mb-3">
            <span className="font-bold text-lg text-gray-900 dark:text-white bg-white dark:bg-gray-700 px-2 py-1 rounded shadow">{airlineCode}</span>
            <span className="text-xs bg-orange-100 dark:bg-orange-900 text-orange-800 dark:text-orange-200 px-3 py-1 rounded-full font-medium shadow">
              {(similarity * 100).toFixed(1)}% match
            </span>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-white dark:bg-gray-700 rounded-lg p-3 shadow-sm">
              <div className="text-xs text-orange-600 dark:text-orange-400 uppercase tracking-wide font-bold">From</div>
              <div className="font-bold text-lg text-gray-900 dark:text-white">{fromCode}</div>
              <div className="text-sm font-medium text-gray-700 dark:text-gray-300">{fromAirport}</div>
              <div className="text-xs text-gray-600 dark:text-gray-400">{fromCity}</div>
            </div>
            <div className="bg-white dark:bg-gray-700 rounded-lg p-3 shadow-sm">
              <div className="text-xs text-orange-600 dark:text-orange-400 uppercase tracking-wide font-bold">To</div>
              <div className="font-bold text-lg text-gray-900 dark:text-white">{toAirport}</div>
              <div className="text-sm font-medium text-gray-700 dark:text-gray-300">{toCode}</div>
              <div className="text-xs text-gray-600 dark:text-gray-400">{toCity}</div>
            </div>
          </div>
          <div className="mt-3 pt-3 border-t-2 border-orange-200 dark:border-orange-600">
            <div className="flex items-center justify-between text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
              <span>✈️ Aircraft: {aircraft.replace('\r', '')}</span>
              <span>🆔 Route: #{id}</span>
            </div>
            
            {/* Booking Button */}
            <div className="flex gap-2">
              <button
                onClick={() => window.open(generateBookingURL(fromCode, toAirport), '_blank')}
                className="flex-1 bg-gradient-to-r from-orange-500 to-red-500 hover:from-orange-600 hover:to-red-600 text-white font-bold py-2 px-4 rounded-lg transition-all duration-200 transform hover:scale-105 shadow-md hover:shadow-lg"
              >
                🛫 Book Flight on Goibibo
              </button>
              <button
                onClick={() => {
                  const url = generateBookingURL(fromCode, toCode);
                  navigator.clipboard.writeText(url);
                  // You could add a toast notification here
                }}
                className="bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 font-medium py-2 px-3 rounded-lg transition-all duration-200"
                title="Copy booking link"
              >
                📋
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

const AirlineCard = ({ airline }: { airline: [string, string | null, string | null, number, number] }) => {
  const [name, country, iata, id, similarity] = airline;
  return (
    <div className="bg-gradient-to-r from-purple-50 to-pink-50 dark:from-gray-800 dark:to-gray-750 border border-purple-200 dark:border-gray-600 rounded-xl p-4 shadow-sm hover:shadow-md transition-all">
      <div className="flex items-start gap-3">
        <div className="w-10 h-10 bg-purple-500 rounded-full flex items-center justify-center">
          <Users className="w-5 h-5 text-white" />
        </div>
        <div className="flex-1">
          <h3 className="font-semibold text-gray-800 dark:text-white">{name || 'Unknown Airline'}</h3>
          <div className="flex items-center gap-4 mt-1">
            {country && (
              <div className="flex items-center gap-1">
                <MapPin className="w-4 h-4 text-gray-500" />
                <span className="text-sm text-gray-600 dark:text-gray-400">{country}</span>
              </div>
            )}
            {iata && (
              <span className="text-sm font-mono bg-gray-100 dark:bg-gray-700 px-2 py-1 rounded">
                {iata}
              </span>
            )}
          </div>
          <div className="flex items-center justify-between mt-2">
            <span className="text-xs text-gray-500">ID: {id}</span>
            <span className="text-xs bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300 px-2 py-1 rounded-full">
              {(similarity * 100).toFixed(1)}% match
            </span>
          </div>
        </div>
      </div>
    </div>
  );
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
        const aiMessage: Message = {
          id: Date.now() + 1,
          text: data.summary || "Search completed successfully",
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
                      className={`${
                        message.isUser
                          ? 'px-5 py-3 bg-blue-500 text-white rounded-2xl shadow-sm'
                          : 'w-full'
                      }`}
                    >
                      {message.isUser ? (
                        <>
                          <p>{message.text}</p>
                          <p className="text-xs opacity-70 mt-2">
                            {message.timestamp.toLocaleTimeString()}
                          </p>
                        </>
                      ) : (
                        <div className="space-y-4">
                          {/* Summary Message */}
                          <div className="bg-white dark:bg-gray-800 text-gray-800 dark:text-white border border-gray-200 dark:border-gray-700 rounded-xl p-4 shadow-sm">
                            <div className="flex items-center gap-2 mb-2">
                              <Search className="w-4 h-4 text-blue-500" />
                              <span className="font-semibold">Search Results</span>
                            </div>
                            <p className="text-sm text-gray-600 dark:text-gray-400">
                              {message.apiResponse?.summary || message.text}
                            </p>
                            <p className="text-xs opacity-70 mt-2">
                              {message.timestamp.toLocaleTimeString()}
                            </p>
                          </div>

                          {/* Display Cards */}
                          {message.apiResponse && (
                            <>
                              {/* Airports Section */}
                              {message.apiResponse.results.airports && message.apiResponse.results.airports.length > 0 && (
                                <div className="space-y-3">
                                  <h3 className="flex items-center gap-2 font-semibold text-gray-800 dark:text-white">
                                    <Building2 className="w-5 h-5 text-blue-500" />
                                    Airports ({message.apiResponse.results.airports.length})
                                  </h3>
                                  <div className="grid gap-3">
                                    {message.apiResponse.results.airports.map((airport, index) => (
                                      <AirportCard key={index} airport={airport} />
                                    ))}
                                  </div>
                                </div>
                              )}

                              {/* Routes Section */}
                              {message.apiResponse.results.routes && message.apiResponse.results.routes.length > 0 && (
                                <div className="space-y-3">
                                  <h3 className="flex items-center gap-2 font-semibold text-gray-800 dark:text-white">
                                    <Route className="w-5 h-5 text-orange-500" />
                                    Flight Routes ({message.apiResponse.results.routes.length})
                                  </h3>
                                  <div className="grid gap-3">
                                    {message.apiResponse.results.routes.map((route, index) => (
                                      <RouteCard key={index} route={route} />
                                    ))}
                                  </div>
                                </div>
                              )}

                              {message.apiResponse?.map_data && message.apiResponse?.map_data.airports?.length > 0 && (
                              <div className="space-y-3">
                                <h3 className="flex items-center gap-2 font-semibold text-gray-800 dark:text-white">
                                  <span className="inline-flex w-5 h-5 items-center justify-center rounded bg-blue-500 text-white">🗺️</span>
                                  Route Map
                                </h3>
                                <MapWidget mapData={message.apiResponse.map_data as MapData} />
                              </div>
                            )}


                              {/* Airlines Section */}
                              {message.apiResponse.results.airlines && message.apiResponse.results.airlines.length > 0 && (
                                <div className="space-y-3">
                                  <h3 className="flex items-center gap-2 font-semibold text-gray-800 dark:text-white">
                                    <Users className="w-5 h-5 text-purple-500" />
                                    Airlines ({message.apiResponse.results.airlines.length})
                                  </h3>
                                  <div className="grid gap-3">
                                    {message.apiResponse.results.airlines.map((airline, index) => (
                                      <AirlineCard key={index} airline={airline} />
                                    ))}
                                  </div>
                                </div>
                              )}
                            </>
                          )}

                          {/* Fallback for non-API responses */}
                          {!message.apiResponse && (
                            <div className="bg-white dark:bg-gray-800 text-gray-800 dark:text-white border border-gray-200 dark:border-gray-700 rounded-xl p-4 shadow-sm">
                              <pre className="whitespace-pre-wrap font-sans text-sm overflow-x-auto">
                                {message.text}
                              </pre>
                              <p className="text-xs opacity-70 mt-2">
                                {message.timestamp.toLocaleTimeString()}
                              </p>
                            </div>
                          )}
                        </div>
                      )}
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
