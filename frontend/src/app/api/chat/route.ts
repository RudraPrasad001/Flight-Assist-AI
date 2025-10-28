import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const { message } = await request.json();

    if (!message) {
      return NextResponse.json({ error: 'Message is required' }, { status: 400 });
    }

    // Flight-specific AI response logic
    const response = generateFlightResponse(message);

    return NextResponse.json({ 
      response,
      timestamp: new Date().toISOString()
    });

  } catch (error) {
    console.error('Flight AI API error:', error);
    return NextResponse.json(
      { error: 'Sorry, I encountered an issue. Please try again.' }, 
      { status: 500 }
    );
  }
}

function generateFlightResponse(message: string): string {
  const lowerMessage = message.toLowerCase();

  // Flight search queries
  if (lowerMessage.includes('flight') && (lowerMessage.includes('search') || lowerMessage.includes('find') || lowerMessage.includes('book'))) {
    return "🔍 I can help you search for flights! To provide the best options, I'll need:\n\n✈️ Departure city/airport\n📍 Destination city/airport\n📅 Travel dates\n👥 Number of passengers\n💺 Preferred class (Economy, Business, First)\n\nPlease share these details and I'll help you find the perfect flight!";
  }

  // Flight status queries
  if (lowerMessage.includes('status') || lowerMessage.includes('delay') || lowerMessage.includes('on time')) {
    return "📊 For real-time flight status, I can help you track:\n\n✅ Departure and arrival times\n🕐 Delay information\n🛫 Gate assignments\n📍 Terminal information\n\nPlease provide your flight number (e.g., AA 123, UA 456) and travel date for accurate status updates.";
  }

  // Baggage policies
  if (lowerMessage.includes('baggage') || lowerMessage.includes('luggage') || lowerMessage.includes('carry') || lowerMessage.includes('checked')) {
    return "🧳 Baggage policies vary by airline and route. Here's what I can help with:\n\n📦 Carry-on size and weight limits\n✈️ Checked baggage allowances\n💰 Excess baggage fees\n🚫 Prohibited items\n🌍 International vs domestic rules\n\nWhich airline and route type (domestic/international) are you asking about?";
  }

  // Airport information
  if (lowerMessage.includes('airport') || lowerMessage.includes('terminal')) {
    return "🏢 I can provide comprehensive airport information:\n\n🗺️ Terminal maps and layouts\n🍽️ Dining and shopping options\n🚗 Transportation options\n📶 WiFi and amenities\n⏰ Security wait times\n🅿️ Parking information\n\nWhich airport would you like information about?";
  }

  // Trip planning
  if (lowerMessage.includes('plan') || lowerMessage.includes('trip') || lowerMessage.includes('travel') || lowerMessage.includes('itinerary')) {
    return "🗺️ I'd love to help plan your trip! I can assist with:\n\n✈️ Flight recommendations and routing\n🏨 Accommodation suggestions\n🎯 Destination highlights\n📋 Travel document requirements\n💉 Health and visa information\n🌡️ Weather and best travel times\n\nWhere are you planning to travel, and what type of experience are you looking for?";
  }

  // Airline policies
  if (lowerMessage.includes('policy') || lowerMessage.includes('rule') || lowerMessage.includes('change') || lowerMessage.includes('cancel')) {
    return "📋 I can explain various airline policies:\n\n🔄 Flight change and cancellation policies\n💰 Refund procedures\n👶 Child and infant travel rules\n🐕 Pet travel policies\n♿ Special assistance services\n🍽️ Meal and dietary requirements\n\nWhich specific policy would you like me to explain?";
  }

  // Greetings
  if (lowerMessage.includes('hello') || lowerMessage.includes('hi') || lowerMessage.includes('hey')) {
    return "✈️ Hello! Welcome to FlightAssist AI. I'm your professional flight assistant, ready to help with:\n\n🔍 Flight searches and booking assistance\n📊 Real-time flight status updates\n🧳 Baggage and travel policies\n🗺️ Trip planning and recommendations\n🏢 Airport information and services\n\nWhat can I help you with today?";
  }

  // Help requests
  if (lowerMessage.includes('help') || lowerMessage.includes('assist') || lowerMessage.includes('support')) {
    return "🆘 I'm here to provide comprehensive flight assistance! I can help you with:\n\n🔍 **Flight Search**: Find and compare flights\n📊 **Flight Status**: Real-time updates and tracking\n🧳 **Travel Policies**: Baggage, changes, cancellations\n🗺️ **Trip Planning**: Destinations and itineraries\n🏢 **Airport Info**: Services, amenities, navigation\n💺 **Seat Selection**: Preferences and availability\n📱 **Check-in**: Mobile and online procedures\n\nWhat specific area would you like help with?";
  }

  // Default response for flight-related context
  return `✈️ Thank you for your question about "${message}". As your FlightAssist AI, I'm here to provide professional flight and travel assistance.\n\nI can help with flight searches, bookings, status updates, travel policies, airport information, and trip planning. Could you please provide more specific details about what you need help with?\n\n🔍 Flight search and booking\n📊 Flight status and updates\n🧳 Baggage and travel policies\n🗺️ Trip planning assistance\n🏢 Airport services and information\n\nHow can I best assist you today?`;
}