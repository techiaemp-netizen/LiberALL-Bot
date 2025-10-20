# LiberALL Bot

Bot Telegram para plataforma de matches e conteúdo adulto com monetização.

## 🚀 Funcionalidades

- ✅ Onboarding completo com cadastro de perfil
- ✅ Sistema de postagem (texto, foto, vídeo, álbum)
- ✅ Monetização de conteúdo com blur no grupo Lite
- ✅ Sistema de matches e salas de chat
- ✅ Favoritos e comentários
- ✅ Navegação de mídia
- ✅ Limites de plano (Lite: 5 posts/mês, Premium: ilimitado)
- ✅ Idempotência e Antispam
- ✅ Callbacks normalizados
- ✅ Renderização dual (carousel/album+panel)

## 📋 Requisitos

- Python 3.11+
- Conta Telegram Bot (via @BotFather)
- Firebase Project
- Cloudinary Account

## 🛠️ Instalação

### 1. Clonar Repositório

```bash
git clone https://github.com/techiaemp-netizen/LiberALL-Bot.git
cd LiberALL-Bot
```

### 2. Criar Ambiente Virtual

```bash
python -m venv venv
source venv/bin/activate  # No Windows: venv\Scripts\activate
```

### 3. Instalar Dependências

```bash
pip install -r requirements.txt
```

### 4. Configurar Variáveis de Ambiente

Copie `.env.example` para `.env` e preencha:

```env
TELEGRAM_BOT_TOKEN=seu_token_aqui
BOT_USERNAME=seu_bot_username
FIREBASE_PROJECT_ID=seu_project_id
FIREBASE_PRIVATE_KEY="sua_private_key"
FIREBASE_CLIENT_EMAIL=seu_client_email
CLOUDINARY_CLOUD_NAME=seu_cloud_name
CLOUDINARY_API_KEY=sua_api_key
CLOUDINARY_API_SECRET=seu_api_secret
FREEMIUM_GROUP_ID=-1001234567890
PREMIUM_GROUP_ID=-1001234567891
```

### 5. Executar Bot

```bash
python main.py
```

## 📁 Estrutura do Projeto

```
LiberALL-Bot/
├── main.py                 # Arquivo principal
├── config.py              # Configurações
├── requirements.txt       # Dependências
├── .env                   # Variáveis de ambiente (não versionado)
├── services/              # Serviços do bot
│   ├── firebase_service.py
│   ├── post_service_v2.py
│   ├── user_service.py
│   ├── match_service.py
│   ├── media_service.py
│   ├── idempotency_service.py
│   └── antispam_service.py
├── handlers/              # Handlers de eventos
│   ├── onboarding_handler.py
│   ├── posting_handler.py
│   ├── post_interaction_handler_v2.py
│   ├── media_navigation_handler_v2.py
│   └── menu_handler.py
├── constants/             # Constantes
│   ├── callbacks.py
│   └── normalized_callbacks.py
├── core/                  # Componentes core
│   └── ui_builder_v2.py
└── utils/                 # Utilitários
    ├── error_handler.py
    └── validators.py
```

## 🎯 Uso

### Comandos Principais

- `/start` - Iniciar bot e onboarding
- Menu principal - Acessar todas as funcionalidades

### Fluxo do Usuário

1. **Cadastro:** `/start` → Preencher perfil (codinome, idade, categoria, etc.)
2. **Galeria:** Adicionar fotos/vídeos ao perfil (opcional)
3. **Postar:** Criar posts na comunidade
4. **Interagir:** Match, favoritar, comentar em posts
5. **Matches:** Conversar em salas de match

## 🔧 Configurações Avançadas

### Modo de Renderização

```env
POST_RENDER_MODE=carousel  # ou album+panel
```

- **carousel:** 1 mensagem com navegação inline
- **album+panel:** Álbum + painel separado

### Blur para Conteúdo Monetizado

```env
BLUR_PREVIEW_FOR_MONETIZED=true
```

### Limites de Rate Limiting

```env
COMMENT_RATE_LIMIT_SECONDS=10
MATCH_RATE_LIMIT_SECONDS=30
FAVORITE_RATE_LIMIT_SECONDS=5
NAVIGATION_RATE_LIMIT_PER_SECOND=5
```

## 🧪 Testes

```bash
# Teste de conexão
python -c "from main import bot; import asyncio; asyncio.run(bot.get_me())"

# Testes unitários (quando disponíveis)
pytest tests/
```

## 📊 Monitoramento

Logs são salvos em `bot.log` e exibidos no console.

Eventos importantes:
- `post.created`
- `match.created`
- `favorite.added`
- `comment.added`
- `error.rate_limit`

## 🔒 Segurança

- ✅ Idempotência para prevenir ações duplicadas
- ✅ Rate limiting para prevenir abuso
- ✅ Validações de permissão
- ⚠️ Firebase Rules devem ser configuradas manualmente

## 📝 Licença

Proprietário - Todos os direitos reservados

## 🤝 Suporte

Para dúvidas ou problemas, abra uma issue no GitHub.

## 🚧 Roadmap

- [ ] Sistema de pagamentos (Mercado Pago)
- [ ] WebApp externo
- [ ] Painel administrativo
- [ ] Moderação automática
- [ ] Multi-match (até 10 participantes)

---

**Desenvolvido com ❤️ usando aiogram 3.3.0**

