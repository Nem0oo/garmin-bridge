# TODO

## MCP
- [x] Ajouter un tool `trigger_sync` dans le MCP server
- [x] Ajouter un tool `get_sync_status` dans le MCP server
- [ ] Trouver un moyen d'exposer plus de tools (daily metrics, sleep, activity summary ?)

## API
- [x] Passer `/sync` de POST à GET pour uniformiser avec les autres endpoints

## CI/CD
- [x] Configurer les secrets Docker Hub (`DOCKERHUB_USERNAME`, `DOCKERHUB_TOKEN`)
- [x] Ajouter le push vers Docker Hub dans le workflow `.github/workflows/docker.yml`
- [x] Ajouter le webhook n8n pour le redéploiement automatique (`N8N_WEBHOOK_ID`)

## Docs
- [x] Peaufiner le README (captures d'écran ? exemples de réponses API ?)
