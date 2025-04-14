from fastapi import FastAPI, File, UploadFile, HTTPException, Request
from pydub import AudioSegment
from wyoming.asr import Transcribe, Transcript
from wyoming.audio import AudioChunk, AudioStart, AudioStop
from wyoming.client import AsyncTcpClient
import tempfile
import os
import logging
import asyncio

app = FastAPI()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ASYNCTCPSERVER_HOST = "192.168.x.y"
ASYNCTCPSERVER_PORT = "10300"

SAMPLE_RATE = 16000
SAMPLE_WIDTH = 2
SAMPLE_CHANNELS = 1

def convert_mp3_to_wav(mp3_file_content: bytes) -> bytes:
	"""Converts MP3 to WAV (16kHz, 16-bit mono)."""
	try:
		logging.info("converting to wave")
		audio = AudioSegment.from_mp3(io.BytesIO(mp3_file_content))
		audio = audio.set_frame_rate(SAMPLE_RATE).set_sample_width(SAMPLE_WIDTH).set_channels(SAMPLE_CHANNELS)  # 16kHz, 16-bit, mono
		wav_buffer = io.BytesIO()
		audio.export(wav_buffer, format="wav")
		logging.info("convertion completed")
		return wav_buffer.getvalue()
	except Exception as e:
		raise HTTPException(status_code=400, detail=f"Error converting MP3 to WAV: {e}")

async def async_process_audio_stream( audio_data ):
	"""Process an audio stream to STT service."""
	try:
		logging.info("try connection AsyncTcpClient")
		async with AsyncTcpClient(ASYNCTCPSERVER_HOST, ASYNCTCPSERVER_PORT) as client:
			logging.info("connection AsyncTcpClient OK")
			# Set transcription language
			#await client.write_event(Transcribe(language="fr").event())

			# Begin audio stream
			await client.write_event(
				AudioStart(
					rate=SAMPLE_RATE,
					width=SAMPLE_WIDTH,
					channels=SAMPLE_CHANNELS,
				).event(),
			)

			# Stream chunks
			chunk = AudioChunk(
				rate=SAMPLE_RATE,
				width=SAMPLE_WIDTH,
				channels=SAMPLE_CHANNELS,
				audio=audio_data,
			)
			await client.write_event(chunk.event())

			# End audio stream
			await client.write_event(AudioStop().event())

			while True:
				event = await client.read_event()
				if event is None:
					_LOGGER.debug("Connection lost")
					return {"error": "Connection lost"}

				if Transcript.is_type(event.type):
					transcript = Transcript.from_event(event)
					text = transcript.text

					return {"text":text}

					break

	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e))


@app.post( "/openai" )
async def process_audio(request: Request):
	"""
	Processes audio data and model information from a multipart/form-data request.
	"""
	try:
		form_data = await request.form()
		model_name: Optional[str] = form_data.get("model")
		audio_file = form_data.get("file")

		if not audio_file:
			raise HTTPException(status_code=400, detail="Audio file not provided.")

		if not model_name:
			raise HTTPException(status_code=400, detail="Model name not provided.")

		# Create temporariry mp3 mirror file
		with tempfile.NamedTemporaryFile(delete=True, suffix=".mp3") as temp_audio:
			await audio_file.seek(0) # ensure read from start.
			temp_audio.write(await audio_file.read())
			mp3_path = temp_audio.name

			try:
				# Convert the MP3 file to WAV format
				mp3_file = AudioSegment.from_mp3(mp3_path)
				wav_data = mp3_file.set_frame_rate(16000).set_channels(1).get_array_of_samples()
				audio_data = bytes(wav_data)
				transcription = await async_process_audio_stream(audio_data)

			except Exception as e:
				raise HTTPException(status_code=500, detail=f"Whisper API Error: {str(e)}")

			return {"text": transcription["text"]}

	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e))


@app.post( "/transcript" )
async def transcribe_audio(file: UploadFile = File(...)):
	# Create temporariry mp3 mirror file
	with tempfile.NamedTemporaryFile(delete=True, suffix='.mp3') as temp_audio:
		content = await file.read()
		temp_audio.write(content)
		mp3_path = temp_audio.name

		try:
			# Convert the MP3 file to WAV format
			mp3_file = AudioSegment.from_mp3(mp3_path)
			wav_data = mp3_file.set_frame_rate(16000).set_channels(1).get_array_of_samples()
			audio_data = bytes(wav_data)
			transcription = await async_process_audio_stream(audio_data)

		except Exception as e:
			raise HTTPException(status_code=500, detail=str(e))

		return {"transcription": transcription}
