# Changelog

## [Unreleased]

## Added

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
