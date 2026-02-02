from fastapi import FastAPI, Request, Form
from pydantic import BaseModel
import uvicorn
from ai_agent import graph, SYSTEM_PROMPT, parse_response
from fastapi.responses import PlainTextResponse
from xml.etree.ElementTree import Element, tostring

app = FastAPI()

class Query(BaseModel):
    message: str

@app.post("/ask")
async def ask_question(query: Query):
    inputs = {"messages": [("system", SYSTEM_PROMPT), ("user", query.message)]}
    
    stream = graph.stream(inputs, stream_mode="updates")
    tool_called_name, final_response = parse_response(stream)

    # Step3: Send response to the frontend
    return {"response": final_response,
            "tool_called": tool_called_name}

def _twiml_message(body: str) -> PlainTextResponse:
    """Create minimal TwiML <Response><Message>...</Message></Response>"""
    response_el = Element('Response')
    message_el = Element('Message')
    message_el.text = body
    response_el.append(message_el)
    xml_bytes = tostring(response_el, encoding='utf-8')
    return PlainTextResponse(content=xml_bytes, media_type='application/xml')



@app.post("/whatsapp_ask")
async def whatsapp_ask(Body: str = Form(...)): 
    user_text = Body.strip() if Body else ""
    inputs = {"messages": [("system", SYSTEM_PROMPT), ("user", user_text)]}
    stream = graph.stream(inputs, stream_mode="updates")
    tool_called_name, final_response = parse_response(stream)    

    if not final_response:
        final_response = "I'm here to support you, but I couldn't generate a response just now."

    # Step3: Send response to Twilio
    return _twiml_message(final_response)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)