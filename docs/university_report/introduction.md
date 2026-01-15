# Introduction

## Contexte et Motivation

Le screening d'éligibilité aux essais cliniques représente un défi majeur dans le développement pharmaceutique moderne. Selon les estimations, le processus de recrutement des patients peut représenter jusqu'à 30% du temps total d'un essai clinique, avec des taux d'échec de screening atteignant 50% dans certaines études.

### Problématique Actuelle

1. **Complexité des critères**: Les protocoles d'essais modernes contiennent en moyenne 31 critères d'éligibilité, une augmentation de 58% par rapport aux années 1990.

2. **Temps de traitement**: Un coordinateur clinique expérimenté nécessite en moyenne 15-30 minutes par patient pour évaluer manuellement l'éligibilité.

3. **Erreurs humaines**: Les études montrent un taux d'erreur de 10-15% dans les décisions d'éligibilité manuelles.

4. **Manque de transparence**: Les décisions traditionnelles manquent souvent de documentation explicite du raisonnement.

### Solution Proposée

Ce projet propose une architecture agentique basée sur l'IA pour automatiser et améliorer le screening d'éligibilité, en utilisant:

- **RAG (Retrieval-Augmented Generation)**: Pour contextualiser les décisions avec des connaissances médicales actualisées
- **Architecture Multi-Agent**: Pour décomposer le problème en étapes spécialisées
- **Scoring de Confiance**: Pour quantifier la fiabilité des décisions
- **Explainability AI**: Pour garantir la transparence et la conformité réglementaire

## Objectifs du Projet

### Objectif Principal

Développer un système d'IA capable de:
1. Évaluer automatiquement l'éligibilité des patients aux essais cliniques
2. Fournir des décisions explicables et auditables
3. Atteindre une précision supérieure aux méthodes manuelles

### Objectifs Secondaires

- Réduire le temps de screening de 40% minimum
- Augmenter le taux d'inscription aux essais
- Générer une documentation conforme aux exigences FDA/EMA
- Fournir une interface utilisateur intuitive pour les coordinateurs cliniques

## Structure du Rapport

1. **Introduction** (ce chapitre) - Contexte et objectifs
2. **Méthodologie** - Approche technique et architecture
3. **Implémentation** - Détails de réalisation
4. **Résultats** - Évaluation et métriques
5. **Conclusion** - Synthèse et perspectives

## Contributions Principales

Ce travail apporte les contributions suivantes:

1. **Architecture agentique innovante**: Utilisation de LangGraph pour orchestrer un workflow de screening en 6 étapes

2. **RAG hybride pour le domaine médical**: Combinaison de BM25 et embeddings denses avec fusion RRF

3. **Système de confiance calibré**: Self-consistency scoring avec calibration probabiliste

4. **Table d'explainability FDA/EMA**: Format standardisé pour la documentation des décisions AI

5. **Interface utilisateur moderne**: Application Streamlit avec visualisations interactives
