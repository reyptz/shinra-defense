# Shinra Defense — Active Defense Platform

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com)
[![Rust](https://img.shields.io/badge/Rust-1.70+-orange.svg)](https://rust-lang.org)
[![License](https://img.shields.io/badge/License-AGPL%20v3-yellow.svg)](LICENSE)
[![Security](https://img.shields.io/badge/Security-ISO%2027001-red.svg)](https://www.iso.org/isoiec-27001-information-security.html)
[![DevSecOps](https://img.shields.io/badge/DevSecOps-Enabled-purple.svg)](https://www.devsecops.org)

---

## English Version

## Description

Shinra Defense is an active defense platform designed for honeypot deployment, real-time threat detection, and artifact extraction. The system uses eBPF for kernel-level monitoring, RAG for threat intelligence correlation, and automated playbooks for incident response.

## Architecture

### src-agent (Rust - eBPF Detection & Response)
- **eBPF Programs**: Kernel-level syscall monitoring (openat, read, connect)
- **Memory Scraper**: Pattern-matching for cryptographic key detection (AES/RSA)
- **Kill-Switch**: Process termination via SIGKILL
- **Honeypot Monitor**: Tracks suspicious activity on honeypot targets

### src-engine (Python - RAG & Attack Decisions)
- **FastAPI**: REST API for honeypot and artifact management
- **SQLite**: Database for honeypots, events, and artifacts
- **ChromaDB**: Vector database for RAG correlation
- **Container Manager**: Docker/Podman for honeypot provisioning
- **WebSocket**: Real-time event streaming

### src-ui (HTML/CSS - Monitoring Dashboard)
- **Dashboard**: SOC dashboard with real-time statistics
- **Live Feed**: Real-time event stream with filtering
- **eBPF Nodes**: Monitoring of eBPF agent nodes
- **Artifacts**: Inventory of extracted cryptographic keys and shellcodes

### playbooks (YAML - Counter-Measure Actions)
- **Ransomware Response**: Automatic neutralization of ransomware attacks
- **Honeypot Provisioning**: Automated honeypot deployment
- **Artifact Extraction**: Memory scraping and artifact analysis
- **Network Isolation**: Hostile process containment
- **System Hardening**: Post-incident security hardening

### scripts (Nix - Deployment/Rollback)
- **deploy.sh**: Automated deployment script
- **rollback.sh**: Automated rollback script
- **health-check.sh**: System health verification
- **flake.nix**: Nix flake configuration

## Technologies Used

### Backend
- **Python 3.9+**: FastAPI, SQLAlchemy, Celery
- **Rust 1.70+**: eBPF with aya-rs, tokio
- **SQLite**: Database for honeypots, events, artifacts
- **ChromaDB**: Vector database for RAG

### Frontend
- **HTML5/CSS3**: Modern dashboard interface
- **Vanilla JavaScript**: Real-time updates via WebSocket
- **TailwindCSS**: Responsive design system

### Artificial Intelligence
- **Sentence Transformers**: Embeddings for RAG
- **ChromaDB**: Vector similarity search
- **Pattern Matching**: Regex-based artifact detection

### Infrastructure
- **Containerization**: Docker/Podman for honeypots
- **Nix**: Package management and deployment
- **Shell Scripts**: Automated deployment and rollback

## Installation

### Technical Prerequisites

#### Mandatory
- **Docker** or **Podman** (for honeypot containers)
- **Python 3.9+**
- **Rust 1.70+** (for eBPF agent)
- **Nix** (optional, for reproducible builds)
- **Linux kernel 5.5+** (for eBPF support)

#### Optional
- **Nix flakes** (for reproducible development environment)

### Quick Installation

```bash
# Clone the repository
git clone https://github.com/reyptz/shinra-defense.git
cd shinra-defense
```

### Manual Installation

```bash
# Install Python dependencies
cd src-engine
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Build Rust agent
cd ../src-agent
cargo build --release

# Initialize database
cd ../src-engine
python -c "from database import init_db; init_db()"

# Start Python engine
python main.py

# Start Rust agent (requires root)
sudo ./target/release/shinra-agent
```

### Automated Deployment

```bash
# Run deployment script
./scripts/deploy.sh

# Check health
./scripts/health-check.sh

# Rollback if needed
./scripts/rollback.sh
```

## Use Cases

### Active Defense / Honeypot Operations
- **Honeypot Deployment**: Automated provisioning of SMB, SSH, and HTTP honeypots
- **Real-time Detection**: eBPF-based monitoring of suspicious file operations
- **Artifact Extraction**: Automatic extraction of cryptographic keys from memory
- **Automated Response**: Playbook-based incident response with kill-switch

### Threat Intelligence / RAG
- **Artifact Correlation**: Vector-based similarity search for known threat signatures
- **Pattern Analysis**: Heuristic detection of AES/RSA keys and shellcodes
- **Knowledge Base**: Local vector database for offline threat intelligence

### SOC Operations
- **Real-time Monitoring**: WebSocket-based live feed of security events
- **Dashboard Analytics**: Visual overview of honeypot status and system health
- **Incident Response**: Automated playbooks for ransomware and network isolation

## Performance Targets

| Component | Language | Target | Status |
|-----------|---------|--------|---------|
| eBPF syscall monitoring | Rust | < 200ms | Implemented |
| Memory scraping | Rust | < 500ms | Implemented |
| API response | Python | < 100ms | Implemented |
| RAG correlation | Python | < 300ms | Implemented |
| Honeypot deployment | Shell | < 60s | Implemented |
| Artifact extraction | Python | < 1s | Implemented |
| WebSocket streaming | Python | Real-time | Implemented |

## Security & Compliance

### Standards
- **ISO 27001**: Information security management
- **NIST Cybersecurity Framework**: Cybersecurity framework
- **GDPR**: Personal data protection (automatic PII detection)

### Security Measures
- **Isolation**: eBPF agent runs with CAP_BPF and CAP_SYS_ADMIN
- **Data Minimization**: Memory dumps parsed and destroyed after extraction
- **Sovereignty**: 100% on-premise operations (no external API calls)
- **Audit Logs**: Encrypted logs with real-time monitoring

## Contributing

We warmly welcome contributions! Here's how to participate:

### Contribution Guidelines

1. **Fork** the project
2. **Create** a feature branch (`git checkout -b feature/AmazingFeature`)
3. **Commit** your changes (`git commit -m 'Add AmazingFeature'`)
4. **Push** to the branch (`git push origin feature/AmazingFeature`)
5. **Open** a Pull Request

### Code Standards
- Follow **PEP 8** for Python
- Add **unit tests** for new features
- Document code with **docstrings**
- Respect **security principles**

## License

This project is licensed under **AGPL v3**. See the [LICENSE](LICENSE) file for more details.

## Author & Contact

### Development Team
**Kamoshe Team**
- Cybersecurity Capstone Project
- Year: 2025

### Contact Methods

- **Email**: [reypotozy@gmail.com](mailto:reypotozy@gmail.com)
- **GitHub**: [reyptz](https://github.com/reyptz)

### Support

- **Issues**: [GitHub Issues](https://github.com/reyptz/Cyber-Universe-Capstone-v1/issues)
- **Discussions**: [GitHub Discussions](https://github.com/reyptz/Cyber-Universe-Capstone-v1/discussions)

## Project Statistics

![GitHub stars](https://img.shields.io/github/stars/reyptz/Cyber-Universe-Capstone-v1?style=social)
![GitHub forks](https://img.shields.io/github/forks/reyptz/Cyber-Universe-Capstone-v1?style=social)
![GitHub issues](https://img.shields.io/github/issues/reyptz/Cyber-Universe-Capstone-v1)
![GitHub pull requests](https://img.shields.io/github/issues-pr/reyptz/Cyber-Universe-Capstone-v1)

---

**If this project helps you, don't hesitate to give it a star!**

Made with ❤️ by Kamoshe Team

---

## Version Française

## Description

Shinra Defense est une plateforme de défense active conçue pour le déploiement de leurres, la détection de menaces en temps réel et l'extraction d'artefacts. Le système utilise eBPF pour la surveillance au niveau du noyau, RAG pour la corrélation de renseignements sur les menaces et des playbooks automatisés pour la réponse aux incidents.

## Architecture

### src-agent (Rust - Détection eBPF & Réponse)
- **Programmes eBPF** : Surveillance des syscalls au niveau noyau (openat, read, connect)
- **Memory Scraper** : Pattern-matching pour la détection de clés cryptographiques (AES/RSA)
- **Kill-Switch** : Interruption de processus via SIGKILL
- **Honeypot Monitor** : Suivi des activités suspectes sur les leurres

### src-engine (Python - RAG & Décisions d'Attaque)
- **FastAPI** : API REST pour la gestion des leurres et artefacts
- **SQLite** : Base de données pour leurres, événements et artefacts
- **ChromaDB** : Base de données vectorielle pour corrélation RAG
- **Container Manager** : Docker/Podman pour le provisionnement des leurres
- **WebSocket** : Streaming d'événements en temps réel

### src-ui (HTML/CSS - Dashboard de Monitoring)
- **Dashboard** : Dashboard SOC avec statistiques en temps réel
- **Live Feed** : Flux d'événements en temps réel avec filtrage
- **Nodes eBPF** : Monitoring des agents eBPF
- **Artefacts** : Inventaire des clés cryptographiques et shellcodes extraits

### playbooks (YAML - Actions de Contre-Mesure)
- **Réponse Ransomware** : Neutralisation automatique des attaques ransomware
- **Provisionnement Leurres** : Déploiement automatisé de leurres
- **Extraction Artefacts** : Scraping mémoire et analyse d'artefacts
- **Isolation Réseau** : Confinement de processus hostiles
- **Durcissement Système** : Sécurisation post-incident

### scripts (Nix - Déploiement/Rollback)
- **deploy.sh** : Script de déploiement automatisé
- **rollback.sh** : Script de rollback automatisé
- **health-check.sh** : Vérification de santé du système
- **flake.nix** : Configuration Nix flake

## Technologies Utilisées

### Backend
- **Python 3.9+** : FastAPI, SQLAlchemy, Celery
- **Rust 1.70+** : eBPF avec aya-rs, tokio
- **SQLite** : Base de données pour leurres, événements, artefacts
- **ChromaDB** : Base de données vectorielle pour RAG

### Frontend
- **HTML5/CSS3** : Interface dashboard moderne
- **Vanilla JavaScript** : Mises à jour en temps réel via WebSocket
- **TailwindCSS** : Design system responsive

### Intelligence Artificielle
- **Sentence Transformers** : Embeddings pour RAG
- **ChromaDB** : Recherche de similarité vectorielle
- **Pattern Matching** : Détection d'artefacts basée sur regex

### Infrastructure
- **Conteneurisation** : Docker/Podman pour leurres
- **Nix** : Gestion des paquets et déploiement
- **Shell Scripts** : Déploiement et rollback automatisés

## Installation

### Prérequis Techniques

#### Obligatoires
- **Docker** ou **Podman** (pour conteneurs leurres)
- **Python 3.9+**
- **Rust 1.70+** (pour agent eBPF)
- **Nix** (optionnel, pour builds reproductibles)
- **Linux kernel 5.5+** (pour support eBPF)

#### Optionnels
- **Nix flakes** (pour environnement de développement reproductible)

### Installation Rapide

```bash
# Cloner le repository
git clone https://github.com/reyptz/shinra-defense.git
cd shinra-defense
```

### Installation Manuelle

```bash
# Installer les dépendances Python
cd src-engine
python -m venv venv
source venv/bin/activate  # Sur Windows: venv\Scripts\activate
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

## Cas d'Usage

### Défense Active / Opérations Leurres
- **Déploiement Leurres** : Provisionnement automatisé de leurres SMB, SSH et HTTP
- **Détection Temps Réel** : Surveillance eBPF des opérations de fichiers suspectes
- **Extraction Artefacts** : Extraction automatique de clés cryptographiques depuis la mémoire
- **Réponse Automatisée** : Playbooks de réponse aux incidents avec kill-switch

### Renseignement Menaces / RAG
- **Corrélation Artefacts** : Recherche de similarité vectorielle pour signatures de menaces connues
- **Analyse de Patterns** : Détection heuristique de clés AES/RSA et shellcodes
- **Base de Connaissances** : Base de données vectorielle locale pour renseignement hors-ligne

### Opérations SOC
- **Monitoring Temps Réel** : Flux live d'événements de sécurité via WebSocket
- **Analytics Dashboard** : Vue visuelle de l'état des leurres et santé système
- **Réponse Incidents** : Playbooks automatisés pour ransomware et isolation réseau

## Performance Cibles

| Composant | Langage | Cible | Statut |
|-----------|---------|--------|---------|
| Monitoring eBPF syscalls | Rust | < 200ms | Implémenté |
| Scraping mémoire | Rust | < 500ms | Implémenté |
| Réponse API | Python | < 100ms | Implémenté |
| Corrélation RAG | Python | < 300ms | Implémenté |
| Déploiement leurres | Shell | < 60s | Implémenté |
| Extraction artefacts | Python | < 1s | Implémenté |
| Streaming WebSocket | Python | Temps réel | Implémenté |

## Sécurité et Conformité

### Standards
- **ISO 27001** : Management de la sécurité de l'information
- **NIST Cybersecurity Framework** : Cadre de cybersécurité
- **GDPR** : Protection des données personnelles (détection automatique PII)

### Mesures de Sécurité
- **Isolation** : Agent eBPF exécute avec CAP_BPF et CAP_SYS_ADMIN
- **Minimisation Données** : Dumps mémoire parsés et détruits après extraction
- **Souveraineté** : 100% opérations on-premise (pas d'appels API externes)
- **Audit Logs** : Logs chiffrés avec monitoring temps réel

## Contribuer

Nous accueillons chaleureusement les contributions ! Voici comment participer :

### Guidelines de Contribution

1. **Fork** le projet
2. **Créer** une branche feature (`git checkout -b feature/AmazingFeature`)
3. **Commit** vos changements (`git commit -m 'Add AmazingFeature'`)
4. **Push** vers la branche (`git push origin feature/AmazingFeature`)
5. **Ouvrir** une Pull Request

### Standards de Code
- Suivre **PEP 8** pour Python
- Ajouter des **tests unitaires** pour les nouvelles fonctionnalités
- Documenter le code avec **docstrings**
- Respecter les **principes de sécurité**

## Licence

Ce projet est sous licence **AGPL v3**. Voir le fichier [LICENSE](LICENSE) pour plus de détails.

## Auteur & Contact

### Équipe de Développement
**Kamoshe Team**
- Projet Capstone en Cybersécurité
- Année : 2025

### Moyens de Contact
- **Email** : [reypotozy@gmail.com](mailto:reypotozy@gmail.com)
- **GitHub** : [reyptz](https://github.com/reyptz)

### Support
- **Issues** : [GitHub Issues](https://github.com/reyptz/Cyber-Universe-Capstone-v1/issues)
- **Discussions** : [GitHub Discussions](https://github.com/reyptz/Cyber-Universe-Capstone-v1/discussions)

## Statistiques du Projet

![GitHub stars](https://img.shields.io/github/stars/reyptz/Cyber-Universe-Capstone-v1?style=social)
![GitHub forks](https://img.shields.io/github/forks/reyptz/Cyber-Universe-Capstone-v1?style=social)
![GitHub issues](https://img.shields.io/github/issues/reyptz/Cyber-Universe-Capstone-v1)
![GitHub pull requests](https://img.shields.io/github/issues-pr/reyptz/Cyber-Universe-Capstone-v1)

---

**Si ce projet vous aide, n'hésitez pas à lui donner une étoile !**

Made with ❤️ by Kamoshe Team
