# Changelog

## [Unreleased]

## Added
- ✨(backend) document accounts api in the openapi schema #72
- ✨(frontend) fit chat bubble size to the message text #75
- ✨(backend) stream answers token by token with a real model streamer #68
- ✨(backend) add max-distance ceiling and distance scores to chunk retrieval #68
- 🔧(config) expose rag tuning env vars in compose and env example #68
- ✨(backend) support mps inference for apple silicon macs #68
## Fixed
- 🐛(docker) raise nginx body limit for avatar uploads (413 fix) #61
- ✨(frontend) add clear french error messages for api failures #61
- 🐛(docker) fix nginx proxying to stale container ips #51

## Added
- ✨(backend) add openapi schema, api docs and production media serving #60
- ✨(backend) add json schema endpoint and download button in api docs #60
- ✨(backend) document bearer auth and request bodies in openapi schema #62
- ✨(backend) make openapi schema version configurable via api version #63
- ✨(frontend) group chat history into per-conversation threads with deletion #52
- ✨(backend) send the conversation history as context to the generator #52
- 📝(docs) add validated debug=false production checklist and profile tests #64
- 🐛(docker) pass csrf trusted origins to the api container for lan access #69
- ✨(backend) add admin oversight of all user api tokens #59
- ✨(frontend) add user profile page with avatar and token management #57
- ✨(backend) add self-service api tokens with scopes and throttle #56
- ✨(frontend) add admin ui with temporary passwords and user blocking #55
- ✨(backend) add admin and user roles with bootstrap admin account #54
- 📝(docs) record pgvector vs qdrant decision and benchmark tooling #53
- ✨(backend) add gpu inference via device flag and compose overlay #50
- ✨(backend) add ocr ingestion for image documents #49

## Changed
- ✨(backend) add multi-user authentication with per-document sharing #43
- 🐛(frontend) fix vite dev server missing api proxy #42
- 🐛(backend) fix e2e pdf fixture carrying no extractable text #41
- ✨(backend) add end-to-end test suite for the full pipeline #41
- ✨(frontend) restyle app with sidebar layout and glassmorphism design #42
- ✨(CI) add complete ci pipeline with backend and frontend jobs #40
- 🐛(docker) fix web healthcheck probing ipv6 localhost #39
- 🐛(backend) fix root env lookup crashing inside containers #39
- ✨(config) gather all configuration in a single root env file #39
- ✨(docker) add optional hf token build arg for model downloads #39
- 🛠️(docker) serve api with gunicorn behind nginx reverse proxy #39
- 🐛(backend) add accelerate dependency for model loading #36
- 🔒(docker) make hf model download mandatory at image build #36

## Fixed

- 🐛(backend) fix query view unpacking chunks as distance tuples #37
- 🔥(docker) bake generation model into api image and log query failures #38

## Fixed

- 🐳(docker) share uploads volume between api and worker containers #35

## Added

- ✨(frontend) add chat page with streaming answers sources and history #36

- ✨(frontend) add documents page with upload status and delete #34

## Fixed

- ♿(frontend) fix dark theme contrast making table headers unreadable #34
- 🐳(docker) add web service serving the react build via nginx #33
- ✨(frontend) add react vite typescript scaffold with shadcn #33
- ✨(backend) add query api with sse streaming and history #32
- ✨(backend) add documents rest api with upload and delete #31
- 🧹(backend) migrate rag core to rag_api and remove rag-management #30
- ✨(backend) add ingestion pipeline for txt pdf docx and md #29
- ✨(backend) add celery redis ingestion worker #28
- ✨(backend) add pgvector embedding column with hnsw index #26
- 🐳(docker) add makefile with docker commands grouped by usage #27
- ✨(backend) add document chunk and query data models #25
- 🐳(docker) add api and postgres services to the compose file #24
- ✨(backend) add django drf scaffold with health endpoint #24
- 📦(config) scaffold v2 src/rag-api and src/rag-web directories #23

- 📝(docs) add contributing guidelines #1
- 📝(docs) add mermaid diagrams for architecture and structure #1
- 💄(docs) modernize readme with badges, tables and styled diagrams #1
- 👷(CI) add ruff lint and format quality gate #2
- ⚙️(config) make the hf cache location configurable via hf_home #4

## Changed

- 🚚(docker) move rag sources to src/rag-management #2
- 🏗️(docker) move compose to root as central orchestration point #3

## Removed

- 🔥(backend) remove the v1 rag-management module after migration #30
- 🔥(docker) remove duplicate compose files #3

## Fixed

- 🐛(docker) fix dockerfile parse error in the model download step #5
- 🐛(docker) set hf_home before model download so the cache is found #6
- 🐛(docker) named volume for chroma_db to avoid readonly sqlite #7
- 🐛(docker) exclude macos metadata files from the build context #8
