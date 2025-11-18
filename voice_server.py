from fastapi import FastAPI, Request, Query
from pydantic import BaseModel
from fastapi.responses import JSONResponse, PlainTextResponse
from twilio.rest import Client
import os
from dotenv import load_dotenv

load_dotenv()

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_CALLER_NUMBER = os.getenv("TWILIO_CALLER_NUMBER")
# BASE_PUBLIC_URL = os.getenv("BASE_PUBLIC_URL", "https://your-ngrok-url") 


twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

app = FastAPI()

call_results = {}

class CallRequest(BaseModel):
    user_id: str
    phone_number: str
    message: str

@app.post("/call_user")
async def call_user(payload: CallRequest):
    try:
        twiml = f"""
        <Response>
            <Say voice="Polly.Joanna" language="en-US">
                {payload.message}
            </Say>
        </Response>
        """

        call = twilio_client.calls.create(
            to=payload.phone_number,
            from_=TWILIO_CALLER_NUMBER,
            twiml=twiml,
        )

        return JSONResponse(
            {
                "status": "ok",
                "call_sid": call.sid,
                "user_id": payload.user_id,
                "phone_number": payload.phone_number,
                "message": payload.message,
            }
        )
    except Exception as e:
        return JSONResponse(
            {"status": "error", "error": str(e)},
            status_code=500,
        )    

# @app.post("/call_user")
# async def call_user(payload: CallRequest):
#     try:
#         entry_url = f"{BASE_PUBLIC_URL}/voice/entry?user_id={payload.user_id}"

#         call = twilio_client.calls.create(
#             to=payload.phone_number,
#             from_=TWILIO_CALLER_NUMBER,
#             url=entry_url,
#         )

#         call_results[payload.user_id] = "Call initiated. Waiting for user response."

#         return JSONResponse(
#             {
#                 "status": "ok",
#                 "call_sid": call.sid,
#                 "user_id": payload.user_id,
#                 "phone_number": payload.phone_number,
#                 "message": payload.message,
#             }
#         )
#     except Exception as e:
#         return JSONResponse(
#             {"status": "error", "error": str(e)},
#             status_code=500,
#         )

# @app.post("/voice/entry")
# async def voice_entry(request: Request, user_id: str = Query(...)):
#     """
#     Twilio hits this when the call is answered:
#     - speaks a short intro
#     - records the caller's reply
#     """
#     twiml = f"""
# <Response>
#     <Say voice="Polly.Joanna" language="en-US">
#         Hello! We are calling regarding your recent activity. 
#         After the beep, please describe any issues or feedback.
#         When you are done, just stop speaking.
#     </Say>
#     <Record
#         maxLength="30"
#         playBeep="true"
#         action="{BASE_PUBLIC_URL}/voice/handle_recording?user_id={user_id}"
#         method="POST"
#     />
# </Response>
#     """.strip()

#     return PlainTextResponse(content=twiml, media_type="application/xml")

# @app.post("/voice/handle_recording")
# async def handle_recording(request: Request, user_id: str = Query(...)):
#     """
#     Twilio calls this after recording the caller.
#     We:
#     - check if anything was recorded
#     - if yes: store stub 'transcript'
#     - if no: mark as 'Call not connected.'
#     """
#     form = await request.form()
#     recording_url = form.get("RecordingUrl", "")
#     recording_duration = form.get("RecordingDuration", "0")  # seconds as string

#     if not recording_url or recording_duration == "0":
#         call_results[user_id] = "Call not connected."
#     else:
#         # stub 'transcript' – you can plug Whisper here later
#         transcript = f"User recording at {recording_url} (duration {recording_duration}s)."
#         call_results[user_id] = transcript

#     response_twiml = """
# <Response>
#     <Say voice="Polly.Joanna" language="en-US">
#         Thank you for your response. Goodbye!
#     </Say>
#     <Hangup />
# </Response>
#     """.strip()

#     return PlainTextResponse(content=response_twiml, media_type="application/xml")

# @app.get("/get_call_result")
# async def get_call_result(user_id: str):
#     """
#     Streamlit calls this to fetch the latest result for a given user.
#     """
#     result = call_results.get(user_id)
#     if result is None:
#         return JSONResponse(
#             {"status": "pending", "user_id": user_id, "summary": None}
#         )
#     return JSONResponse(
#         {"status": "done", "user_id": user_id, "summary": result}
#     )
