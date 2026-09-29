# Changelog

## [Unreleased]

## Added

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

- 🔥(docker) remove duplicate compose files #3

## Fixed

- 🐛(docker) fix dockerfile parse error in the model download step #5
- 🐛(docker) set hf_home before model download so the cache is found #6
- 🐛(docker) named volume for chroma_db to avoid readonly sqlite #7
- 🐛(docker) exclude macos metadata files from the build context #8
