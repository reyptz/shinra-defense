# Scripts Shinra Defense

Automatisation du déploiement et rollback avec Nix.

## Structure

- `flake.nix` - Configuration Nix flake pour la gestion des dépendances
- `deploy.sh` - Script de déploiement automatisé
- `rollback.sh` - Script de rollback automatique
- `health-check.sh` - Script de vérification de santé du système

## Utilisation

```bash
# Déploiement complet
./scripts/deploy.sh

# Rollback complet
./scripts/rollback.sh

# Vérification de santé
./scripts/health-check.sh
```

## Prérequis

- Nix package manager
- Nix flakes activés
- Docker ou Podman
- Python 3.9+
- Rust 1.70+

## Configuration

Les variables d'environnement peuvent être définies dans `.env`:
- `DEPLOY_ENV`: environnement de déploiement (dev, staging, prod)
- `DOCKER_REGISTRY`: registry Docker pour les images
- `BACKUP_DIR`: répertoire pour les sauvegardes
