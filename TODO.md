# TODO

## Deploy
- [ ] Simplifier les composes (garmin-bridge, garmin-jade, garmin-adrien) : retirer les variables `GARMIN_*_DB_PATH`, le port/route 8000 et le volume `garmindb_data`

## CI/CD
- [x] Configurer les secrets Docker Hub (`DOCKERHUB_USERNAME`, `DOCKERHUB_TOKEN`)
- [x] Ajouter le push vers Docker Hub dans le workflow `.github/workflows/docker.yml`
- [x] Ajouter le webhook n8n pour le redéploiement automatique (`N8N_WEBHOOK_ID`)
