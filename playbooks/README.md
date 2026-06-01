# Playbooks Shinra Defense

Fichiers YAML définissant les actions de contre-mesure pour la plateforme Shinra Defense.

## Structure

- `ransomware_response.yml` - Réponse automatique aux attaques ransomware
- `honeypot_provisioning.yml` - Provisionnement et gestion des leurres
- `artifact_extraction.yml` - Extraction et analyse des artefacts
- `network_isolation.yml` - Isolation réseau des processus hostiles
- `system_hardening.yml` - Durcissement système post-incident

## Utilisation

```bash
# Exécuter un playbook avec ansible-playbook
ansible-playbook playbooks/ransomware_response.yml

# Ou avec le moteur Python
python -m src-engine.playbook_executor playbooks/ransomware_response.yml
```

## Format des Playbooks

Les playbooks suivent le format YAML standard avec:
- `name`: Description de l'action
- `triggers`: Conditions de déclenchement
- `actions`: Liste des actions à exécuter
- `rollback`: Actions de rollback si nécessaire
