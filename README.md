# wrhasspy-api
Docker api for rhasspy/wyoming-faster-whisper.

A fastapi webui is available for testing at your server docker address + /docs: http://192.168.x.x:5000/docs
This will allow you to test, but more importantly to check json structure required by the api.

Direct transcription services and Openai api-like are available at /transcripts and /openai respectively.
The /openai path is to be used for app that are developped to request openai api transcript service for any mp3 file (for instance for nextcloud, using a proxy manager to do both: enable https + redirect /v1/transcript queries to corresponding path http://192.168.x.x:5000/transcript).

Run below docker:

``
docker run -d -p 5000:5000 --restart unless-stopped --name wrhasspy-api wrhasspy-api
``
