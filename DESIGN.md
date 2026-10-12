# DESIGN.md — direction « clair éditorial »

## Mode

Operate (app UI : documents, chat, admin, profil). Scanabilité, cohérence et
confort de lecture avant l'expression.

## Color

- Fond : papier chaud `oklch(0.985 0.005 95)` ; surface carte `oklch(1 0 0)`.
- Encre : `oklch(0.19 0.01 95)` (titres), `oklch(0.45 0.01 95)` (corps).
- Accent unique : violet `oklch(0.55 0.22 295)`, réservé aux actions
  primaires, aux liens et à la sélection. Jamais de dégradé, jamais de halo.
- Statuts : gris (pending), ambre (processing), vert profond (indexed),
  rouge (failed) — teintes désaturées, sur fonds pastel.
- Interdits : glassmorphism, néons, blurs décoratifs, beige « IA »,
  serif italique décorative.

## Type

- Geist Variable. Titres 600 serrés, corps 400.
- Échelle : 13px (méta) / 14px (corps) / 16px (titres de page) / 22px (login).
- Longueur de ligne de chat ≤ 72 caractères.

## Shape

- Rayons : 10px (champs/boutons), 14px (cartes), pilule (badges de statut).
- Bordures 1px `oklch(0.91 0.005 95)`, ombre quasi nulle (`shadow-xs` max).
- Pas d'élévation au-delà d'un niveau (dialog).

## Layout

- Sidebar 240px sur desktop ≥ lg ; barre supérieure + drawer sur mobile.
- Le chat est une colonne centrée max 760px, jamais une grille figée.
- Listes : lignes denses avec labels visibles (pas de placeholder seul).

## Motion

- Transitions ≤ 150ms, ease-out. Aucun spring visible, aucun parallax.
- Streaming des tokens : curseur fin, sans pulsation.

## Responsive

- 390px : une seule colonne, nav en drawer, actions à hauteur de pouce.
- 768px : sidebar réduite en icônes ou deux colonnes selon la page.
- 1440px : contenu max 1120px centré, le blanc respire.
