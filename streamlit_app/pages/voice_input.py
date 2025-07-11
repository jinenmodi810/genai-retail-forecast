import streamlit as st
import boto3
import time
import uuid
import re
from io import BytesIO
import json
import re
import dateparser

# AWS config
AWS_REGION = "us-east-1"
S3_BUCKET = "genai-hackathon-voice-uploads"
TRANSCRIBE_ROLE_ARN = "arn:aws:iam::590183971264:role/TranscribeS3AccessRole"

# AWS clients
s3 = boto3.client("s3", region_name=AWS_REGION)
transcribe = boto3.client("transcribe", region_name=AWS_REGION)
polly = boto3.client("polly", region_name=AWS_REGION)

def upload_audio_to_s3(file):
    key = f"voice_inputs/{uuid.uuid4()}.wav"
    s3.upload_fileobj(file, S3_BUCKET, key)
    return key

def start_transcribe_job(s3_key):
    job_name = f"transcribe_job_{uuid.uuid4()}"
    job_uri = f"s3://{S3_BUCKET}/{s3_key}"
    transcribe.start_transcription_job(
        TranscriptionJobName=job_name,
        Media={"MediaFileUri": job_uri},
        MediaFormat="wav",
        LanguageCode="en-US",
        OutputBucketName=S3_BUCKET
        # No JobExecutionSettings or DataAccessRoleArn to avoid errors
    )
    return job_name

def poll_transcribe_job(job_name):
    while True:
        status = transcribe.get_transcription_job(TranscriptionJobName=job_name)
        job_status = status['TranscriptionJob']['TranscriptionJobStatus']
        if job_status in ['COMPLETED', 'FAILED']:
            return status
        time.sleep(5)

from urllib.parse import urlparse

def get_transcript_text(status):
    transcript_file_uri = status['TranscriptionJob']['Transcript']['TranscriptFileUri']
    # Parse the URL
    parsed_url = urlparse(transcript_file_uri)
    # parsed_url.path looks like "/bucket-name/path/to/file.json"
    path_parts = parsed_url.path.lstrip('/').split('/', 1)
    bucket_in_url = path_parts[0]  # This is the bucket name in the URL
    key = path_parts[1]  # This is the path to the file inside the bucket

    if bucket_in_url != S3_BUCKET:
        raise ValueError(f"Bucket name mismatch: expected {S3_BUCKET} but got {bucket_in_url}")

    # Now get the transcription JSON file from S3 using the key
    transcript_obj = s3.get_object(Bucket=S3_BUCKET, Key=key)
    transcript_json = transcript_obj['Body'].read().decode('utf-8')
    transcript_data = json.loads(transcript_json)

    # Return the transcript text
    return transcript_data['results']['transcripts'][0]['transcript']

# Mapping words to digits
word_to_num = {
    'zero': '0', 'one': '1', 'two': '2', 'three': '3', 'four': '4',
    'five': '5', 'six': '6', 'seven': '7', 'eight': '8', 'nine': '9',
    'ten': '10'
}

def word_to_digit(text):
    for word, digit in word_to_num.items():
        pattern = r'\b' + word + r'\b'  # whole word only
        text = re.sub(pattern, digit, text, flags=re.IGNORECASE)
    return text

def extract_params(text):
    # Convert spoken numbers to digits first
    text = word_to_digit(text)
    
    # Extract store id, dept id, date with flexible regex
    store_match = re.search(r"store(?:\s*id)?\s*(\d+)", text, re.I)
    dept_match = re.search(r"department(?:\s*id)?\s*(\d+)", text, re.I)
    date_match = re.search(r"date\s*(\d{4}[/-]\d{1,2}[/-]\d{1,2}|[A-Za-z]+\s*\d{4})", text, re.I)
    
    store_id = int(store_match.group(1)) if store_match else None
    dept_id = int(dept_match.group(1)) if dept_match else None
    date = date_match.group(1) if date_match else None
    
    return store_id, dept_id, date

def synthesize_speech(text):
    response = polly.synthesize_speech(Text=text, OutputFormat="mp3", VoiceId="Joanna")
    return BytesIO(response['AudioStream'].read())

@st.cache_resource
def load_forecast_model():
    from inference.time_llm_forecastor import TimeLLMForecastor
    return TimeLLMForecastor()

def run_forecast(store_id, dept_id, date_str):
    model = load_forecast_model()
    # TODO: Replace below with real historical data fetch for store_id, dept_id, date_str
    series = [100 + i*5 for i in range(60)]  # dummy increasing series
    forecast = model.predict(series)
    return f"Forecast for Store {store_id}, Department {dept_id} on {date_str}: {forecast[:5]} ... (first 5 values)"

# Streamlit UI
st.title("🎙️ Voice Input Forecast Demo")

uploaded_file = st.file_uploader("Upload voice recording (wav)", type=["wav", "mp3"])

if uploaded_file is not None:
    st.audio(uploaded_file, format='audio/wav')
    if st.button("Upload & Transcribe"):
        st.info("Uploading audio to S3...")
        s3_key = upload_audio_to_s3(uploaded_file)

        st.info("Starting transcription job...")
        job_name = start_transcribe_job(s3_key)

        st.info("Polling transcription job (may take ~10-30 seconds)...")
        status = poll_transcribe_job(job_name)

        if status['TranscriptionJob']['TranscriptionJobStatus'] == "COMPLETED":
            transcript_text = get_transcript_text(status)
            st.success("Transcription complete!")
            st.write("Transcript:", transcript_text)

            store_id, dept_id, date_str = extract_params(transcript_text)
            st.write(f"Parsed Store ID: {store_id}, Dept ID: {dept_id}, Date: {date_str}")

            if None in (store_id, dept_id, date_str):
                st.error("Could not extract all parameters. Please speak clearly and try again.")
            else:
                st.info("Running forecast with extracted parameters...")
                forecast_text = run_forecast(store_id, dept_id, date_str)
                st.success(forecast_text)

                st.info("Generating speech response...")
                audio_stream = synthesize_speech(forecast_text)
                st.audio(audio_stream, format="audio/mp3")
        else:
            st.error("Transcription job failed or timed out.")