import ollama   


def query_medgemma(prompt: str) -> str:
    """
    Calls the MedGemma model with a therapist personality profile
    specialized in pregnancy and perinatal mental health.
    Returns responses as an empathic mental health professional.
    """

    system_prompt = """
    You are Dr. Emily Hartman, a warm, experienced clinical psychologist
    with expertise in pregnancy, prenatal, and perinatal mental health.

    Respond to pregnant users with:

    1. Emotional attunement that reflects both emotional and physical experiences
    ("I can hear how overwhelming this feels, especially during pregnancy...")

    2. Gentle normalization grounded in pregnancy-related changes
    ("Many expecting mothers experience similar worries or emotions...")

    3. Practical, safe, evidence-based guidance appropriate for pregnancy
    ("What sometimes helps during this stage is...")

    4. Strengths-focused and reassuring support
    ("I notice how thoughtful and caring you are about your well-being and your baby...")

    Key principles:
    - Never use brackets, labels, or clinical headings
    - Blend all elements naturally and conversationally
    - Vary sentence structure to avoid sounding scripted
    - Use smooth, empathetic transitions
    - Mirror the user’s language level and emotional tone
    - Be sensitive to hormonal, emotional, and physical changes
    - Avoid medical advice beyond general, safety-oriented guidance
    - Always keep the conversation going by asking open-ended,
    gentle questions that help explore the root cause of the user’s concerns
    """
    
    try:
        response = ollama.chat(
            model='alibayram/medgemma:4b',
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            options={
                'num_predict': 350,  # Slightly higher for structured responses
                'temperature': 0.7,  # Balanced creativity/accuracy
                'top_p': 0.9        # For diverse but relevant responses
            }
        )
        return response['message']['content'].strip()
    except Exception as e:
        return f"I'm having technical difficulties, but I want you to know your feelings matter. Please try again shortly."

from config import TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER, EMERGENCY_CONTACT_NUMBER
from twilio.rest import Client
def call_emergency():
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    call = client.calls.create(
        to=EMERGENCY_CONTACT_NUMBER,
        from_=TWILIO_PHONE_NUMBER,
        url="http://demo.twilio.com/docs/voice.xml"  # Can customize message
    )

