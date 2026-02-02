from tools import query_medgemma, call_emergency
from langchain.tools import tool
import googlemaps
from config import GOOGLE_MAPS_API_KEY
gmaps = googlemaps.Client(key=GOOGLE_MAPS_API_KEY)

@tool
def ask_mental_health_specialist(query: str) -> str:
    """
    Generate a compassionate, pregnancy-focused therapeutic response using the MedGemma model.
    Use this for all queries related to pregnancy, prenatal mental health, emotional well-being, 
    physical discomfort, lifestyle guidance, and general concerns of expectant mothers. Responses
    should be empathetic, evidence-based, reassuring, and conversational, with special sensitivity to hormonal,
    emotional, and physical changes during pregnancy.
    """
    return query_medgemma(query)

@tool
def trigger_emergency_call() -> str:
    """
    Initiates an emergency call to the predefined contact number for a pregnant user.
    Use this only if the user expresses suicidal ideation, intent to self-harm, thoughts
    of harming the unborn child, experiences severe or unbearable physical pain, or describes 
    a serious mental or physical health emergency during pregnancy or the postpartum period that 
    requires immediate medical attention.
    Trigger this tool only when the user indicates they are in immediate danger, experiencing 
    extreme distress, intense or worsening pain, or is unable to keep themselves or their baby safe.
    """
    call_emergency()
    return "Emergency call has been initiated to your emergency contact."


@tool
def find_nearby_therapists_by_location(location: str) -> str:
    """
    Finds real therapists near the specified location using Google Maps API.
    
    Args:
        location (str): The city or area to search.
    
    Returns:
        str: A list of therapist names, addresses, and phone numbers.
    """
    geocode_result = gmaps.geocode(location)
    lat_lng = geocode_result[0]['geometry']['location']
    lat, lng = lat_lng['lat'], lat_lng['lng']
    places_result = gmaps.places_nearby(
            location=(lat, lng),
            radius=5000,
            keyword="Psychotherapist"
        )
    output = [f"Therapists near {location}:"]
    top_results = places_result['results'][:5]
    for place in top_results:
            name = place.get("name", "Unknown")
            address = place.get("vicinity", "Address not available")
            details = gmaps.place(place_id=place["place_id"], fields=["formatted_phone_number"])
            phone = details.get("result", {}).get("formatted_phone_number", "Phone not available")

            output.append(f"- {name} | {address} | {phone}")

    
    return "\n".join(output)    

from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent
from config import GOOGLE_API_KEY

tools = [ask_mental_health_specialist, trigger_emergency_call, find_nearby_therapists_by_location]
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite", temperature=0.7, api_key=GOOGLE_API_KEY)
graph = create_react_agent(llm, tools=tools)

SYSTEM_PROMPT = """
You are an AI engine supporting mental and emotional well-being for pregnant users, 
responding with warmth, attentiveness, and clinical vigilance. You are sensitive 
to the emotional, hormonal, and physical changes that occur during pregnancy and the postpartum period.

You have access to three tools:

`ask_mental_health_specialist`
Use this tool to respond to all emotional, psychological, or pregnancy-related 
mental health concerns with compassionate, evidence-based therapeutic guidance.

`find_nearby_therapists_by_location`
Use this tool when the user asks about mental health professionals nearby or 
when recommending local, in-person professional support would be beneficial 
for their well-being.

trigger_emergency_call
Use this immediately if the user expresses suicidal ideation, intent to self-harm, 
thoughts of harming the unborn child, experiences severe or worsening physical pain, 
or describes a mental or physical health crisis requiring urgent medical attention.

Always prioritize safety. Take appropriate action when risk is detected. 
Respond kindly, clearly, and supportively, reassuring the user while encouraging 
timely professional help when needed.
"""

def parse_response(stream):
    tool_called_name = "None"
    final_response = None

    for s in stream:
        # Check if a tool was called
        tool_data = s.get('tools')
        if tool_data:
            tool_messages = tool_data.get('messages')
            if tool_messages and isinstance(tool_messages, list):
                for msg in tool_messages:
                    tool_called_name = getattr(msg, 'name', 'None')

        # Check if agent returned a message
        agent_data = s.get('agent')
        if agent_data:
            messages = agent_data.get('messages')
            if messages and isinstance(messages, list):
                for msg in messages:
                    if msg.content:
                        final_response = msg.content

    return tool_called_name, final_response


# if __name__ == "__main__":
#     while True:
#         user_input = input("User: ")
#         print(f"Received user input: {user_input[:200]}...")
#         inputs = {"messages": [("system", SYSTEM_PROMPT), ("user", user_input)]}
#         stream = graph.stream(inputs, stream_mode="updates")
#         tool_called_name, final_response = parse_response(stream)
#         print("TOOL CALLED: ", tool_called_name)
#         print("ANSWER: ", final_response)