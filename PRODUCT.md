# PRODUCT.md — simple-local-rag

## Produit

RAG 100 % local : on dépose des documents (txt, md, pdf, docx, images OCR),
l'ingestion les découpe et les indexe (pgvector), puis on interroge un
assistant (Qwen3) qui répond en streaming avec ses sources.

## Platform

Web (React + Vite + Tailwind + shadcn/ui). Desktop et mobile à égalité :
chaque page doit être pleinement utilisable de 390px à 1440px.

## Users

Petite équipe (2 à 10 personnes), à l'aise en informatique. Chacun gère ses
documents et ses conversations ; un admin gère les comptes et les tokens.

## Principes

- Calme par défaut : une action principale par écran, pas de décoration gratuite.
- La réponse et ses sources sont le cœur du produit : lisibilité avant tout.
- Statuts visibles : on sait toujours si un document est indexé ou en échec.
- Interface entièrement en français.
