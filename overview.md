# Shinra Defense - Vue d'ensemble Technique

## Introduction

Shinra Defense est une plateforme de défense active conçue pour le déploiement de leurres (honeypots), la détection de menaces en temps réel, et l'extraction d'artefacts d'attaque. Le système utilise eBPF pour la surveillance au niveau du noyau, RAG (Retrieval-Augmented Generation) pour la corrélation de renseignements sur les menaces, et des playbooks automatisés pour la réponse aux incidents.

L'architecture est divisée en trois strates isolées : un agent Rust pour la détection eBPF et la réponse système, un moteur Python pour la logique RAG et les décisions d'attaque, et une interface HTML/CSS pour le dashboard de monitoring. Les playbooks YAML définissent les actions de contre-mesure, et les scripts Nix automatisent le déploiement et le rollback.

## Architecture Principale

### src-agent (Rust - Détection eBPF & Réponse)

Couche agent exécutée au niveau kernel pour la surveillance et la réponse immédiate.

- **eBPF Programs** : Programmes eBPF pour monitoring des syscalls (openat, read, connect) via aya-rs
- **Memory Scraper** : Algorithme de pattern-matching en mémoire pour détection de signatures de clés (AES/RSA) post-compromission
- **Kill-Switch** : Interruption de processus via signaux OS immédiats (SIGKILL)
- **Honeypot Monitor** : Suivi des activités suspectes sur les cibles de leurrage avec seuil de suspicion

### src-engine (Python - RAG & Décisions d'Attaque)

Couche moteur pour le control plane et l'intelligence artificielle.

- **FastAPI** : API REST pour gestion du cycle de vie des conteneurs leurres et artefacts
- **SQLite** : Base de données avec VSS pour le RAG (tables: honeypots, events_ebpf, artifacts, vectors_rag)
- **ChromaDB** : Base de données vectorielle locale pour corrélation RAG avec embeddings sentence-transformers
- **Container Manager** : Gestion du cycle de vie des conteneurs (Docker/Podman API) pour SMB, SSH, HTTP honeypots
- **WebSocket** : Exposition des WebSockets pour le flux d'événements temps réel

### src-ui (HTML/CSS - Dashboard de Monitoring)

Couche présentation pour le centre d'opérations (SOC Dashboard).

- **Dashboard** : Vue principale avec statistiques en temps réel, activité récente, état des honeypots, santé système
- **Live Feed** : Flux d'événements en temps réel avec filtrage par type et statistiques
- **eBPF Nodes** : Monitoring des nodes eBPF avec métriques détaillées et état des programmes
- **Artifacts** : Inventaire des artefacts extraits (clés cryptographiques, shellcodes, hashs) avec modal de détails

### playbooks (YAML - Actions de Contre-Mesure)

Fichiers YAML définissant les actions automatisées de réponse aux incidents.

- **ransomware_response.yml** : Réponse automatique aux attaques ransomware (suspension, dump mémoire, extraction clés, terminaison)
- **honeypot_provisioning.yml** : Provisionnement automatisé des leurres (SMB, SSH, HTTP) avec monitoring eBPF
- **artifact_extraction.yml** : Extraction et analyse des artefacts depuis les dumps mémoire avec validation
- **network_isolation.yml** : Isolation réseau des processus hostiles avec règles firewall
- **system_hardening.yml** : Durcissement système post-incident (mises à jour, permissions, services)

### scripts (Nix - Déploiement/Rollback)

Automatisation du déploiement et rollback avec Nix pour la reproductibilité.

- **deploy.sh** : Script de déploiement automatisé (build Rust, install Python deps, init DB, start services)
- **rollback.sh** : Script de rollback automatisé (stop services, remove honeypots, cleanup, restore backup)
- **health-check.sh** : Script de vérification de santé (engine, agent, honeypots, database, resources)
- **flake.nix** : Configuration Nix flake pour environnement de développement reproductible

## Stack Technique

### Backend
- Python 3.9+ (FastAPI, SQLAlchemy, Celery)
- Rust 1.70+ (eBPF avec aya-rs, tokio)
- SQLite (base de données relationnelle)
- ChromaDB (base de données vectorielle)

### Intelligence Artificielle et RAG
- Sentence Transformers (embeddings pour RAG)
- ChromaDB (recherche de similarité vectorielle)
- Pattern Matching (détection d'artefacts basée sur regex)
- Heuristic Analysis (détection de clés AES/RSA, shellcodes)

### Infrastructure
- Conteneurisation : Docker/Podman (pour leurres)
- Nix (gestion des paquets et déploiement reproductible)
- Shell Scripts (automatisation déploiement/rollback)

### Frontend
- HTML5/CSS3 (interface dashboard moderne)
- Vanilla JavaScript (mises à jour temps réel via WebSocket)
- TailwindCSS (design system responsive)

## Sécurité et Conformité

### Isolation et Privilèges
- eBPF agent exécute avec CAP_BPF et CAP_SYS_ADMIN
- Cloisonnement du moteur Python de l'agent Rust
- Conteneurs leurres isolés avec namespaces

### Minimisation des Données
- Dumps mémoire parsés en RAM
- Destruction immédiate après extraction de la clé
- Pas de stockage de données sensibles collatérales

### Souveraineté
- 100% opérations on-premise
- Pas d'appels API externes
- LLM local, vectorisation et stockage locaux

### Standards
- ISO 27001/27007
- NIST Cybersecurity Framework
- GDPR (détection automatique PII)

### Audit
- Logs chiffrés et immuables
- Monitoring temps réel
- Traçabilité complète des événements

## Performance Cibles

| Composant                  | Langage | Cible               | Statut      |
|----------------------------|---------|---------------------|-------------|
| Monitoring eBPF syscalls    | Rust    | < 200 ms            | Implémenté  |
| Scraping mémoire           | Rust    | < 500 ms            | Implémenté  |
| Réponse API                | Python  | < 100 ms            | Implémenté  |
| Corrélation RAG            | Python  | < 300 ms            | Implémenté  |
| Déploiement leurres        | Shell   | < 60 s              | Implémenté  |
| Extraction artefacts       | Python  | < 1 s               | Implémenté  |
| Streaming WebSocket        | Python  | Temps réel          | Implémenté  |

## Architecture de Déploiement

### Environnements
- **Development** : Installation locale avec scripts manuels
- **Staging** : Tests complets avec déploiement automatisé
- **Production** : Haute disponibilité avec monitoring continu

### Déploiement et Rollback
- Scripts shell automatisés (deploy.sh, rollback.sh)
- Vérification de santé (health-check.sh)
- Sauvegardes automatiques avant déploiement
- Nix flakes pour reproductibilité

### Monitoring et Observabilité
- Vérification santé système (CPU, mémoire, disque)
- Logs structurés dans /var/log/shinra
- Rapports de santé générés automatiquement
- WebSocket pour streaming temps réel

## Cas d'Usage

### Défense Active / Leurrage
Déploiement automatisé de leurres SMB, SSH, HTTP, surveillance eBPF des activités suspectes, extraction automatique de clés cryptographiques.

### Renseignement Menaces / RAG
Corrélation vectorielle d'artefacts avec base de connaissances locale, analyse heuristique de patterns, détection de signatures connues.

### Opérations SOC
Monitoring temps réel via dashboard, flux live d'événements, playbooks automatisés de réponse aux incidents.

## Structure du Projet

```
shinra-defense/
├── src-agent/              # Détection eBPF et réponse système (Rust)
│   ├── Cargo.toml
│   ├── build.rs
│   ├── ebpf/
│   │   ├── main.bpf.c
│   │   └── vmlinux.h
│   └── src/
│       └── main.rs
├── src-engine/             # Logique RAG et décisions (Python)
│   ├── requirements.txt
│   ├── database.py
│   ├── main.py
│   ├── container_manager.py
│   └── rag_engine.py
├── src-ui/                 # Dashboard monitoring (HTML/CSS)
│   ├── dashboard.html
│   ├── live-feed.html
│   ├── ebpf-nodes.html
│   ├── artifacts.html
│   └── styles.css
├── playbooks/              # Actions de contre-mesure (YAML)
│   ├── ransomware_response.yml
│   ├── honeypot_provisioning.yml
│   ├── artifact_extraction.yml
│   ├── network_isolation.yml
│   └── system_hardening.yml
└── scripts/                # Automatisation déploiement/rollback (Nix)
    ├── deploy.sh
    ├── rollback.sh
    ├── health-check.sh
    └── flake.nix
```

## Installation et Configuration

### Prérequis
- Docker ou Podman (pour conteneurs leurres)
- Python 3.9+
- Rust 1.70+ (pour agent eBPF)
- Nix (optionnel, pour builds reproductibles)
- Linux kernel 5.5+ (pour support eBPF)

### Installation Manuelle
```bash
# Installer les dépendances Python
cd src-engine
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Construire l'agent Rust
cd ../src-agent
cargo build --release

# Initialiser la base de données
cd ../src-engine
python -c "from database import init_db; init_db()"

# Démarrer le moteur Python
python main.py

# Démarrer l'agent Rust (nécessite root)
sudo ./target/release/shinra-agent
```

### Déploiement Automatisé
```bash
# Exécuter le script de déploiement
./scripts/deploy.sh

# Vérifier la santé
./scripts/health-check.sh

# Rollback si nécessaire
./scripts/rollback.sh
```

## Conclusion

Shinra Defense constitue une plateforme de défense active complète intégrant détection eBPF au niveau noyau, corrélation RAG pour le renseignement sur les menaces, et playbooks automatisés pour la réponse aux incidents. Son architecture modulaire, ses performances mesurées et sa conformité stricte aux standards de sécurité en font une solution idéale pour les opérations SOC modernes.

Le projet est prêt pour un déploiement opérationnel. La documentation technique complète, les scripts d'automatisation et les outils de monitoring garantissent une maintenabilité et une évolutivité optimales. L'approche on-premise avec souveraineté des données assure une conformité totale aux exigences de sécurité et de confidentialité.