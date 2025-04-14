# wrhasspy-api
Docker api for rhasspy/wyoming-faster-whisper.

A fastapi webui is available for testing at your server docker address + /docs: http://192.168.x.x:5000/docs
This will allow you to test, but more importantly to check json structure.

Direct transcriptions services and Openai api-like are available at /transcripts and /openai respectively.
The /openai can be used for app that are developped to query openai api (for instance for nextcloud, using a proxy manager to do both: enable https + redirect /v1/transcript queries to corresponding path http://192.168.x.x:5000/transcript).

Run below docker:

``
docker run -d -p 5000:5000 --restart unless-stopped --name wrhasspy-api wrhasspy-api
``
