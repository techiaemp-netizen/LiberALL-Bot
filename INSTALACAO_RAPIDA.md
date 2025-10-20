# Instalação Rápida - LiberALL Bot

## ✅ Repositório Limpo e Testado

Este é um repositório completamente novo, sem resíduos de versões antigas.

**Status:** ✅ Bot testado e funcional

## 🚀 Instalação em 5 Passos

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

### 4. Configurar .env

O arquivo `.env` já está incluído com as credenciais de produção. **Não é necessário configurar nada.**

Se precisar alterar, edite o arquivo `.env`:

```env
TELEGRAM_BOT_TOKEN=seu_token
FIREBASE_PROJECT_ID=seu_project_id
CLOUDINARY_CLOUD_NAME=seu_cloud_name
# ... etc
```

### 5. Executar Bot

```bash
python main.py
```

Você deve ver:

```
✅ Handlers inicializados
🔄 Iniciando polling...
Run polling for bot @liberalmatch_bot
```

## ✅ Verificação

### Teste de Conexão Rápido

```bash
python -c "from main import bot; import asyncio; print('✅ Bot OK' if asyncio.run(bot.get_me()) else '❌ Erro')"
```

### Teste Completo

1. Abra o Telegram
2. Procure por `@liberalmatch_bot`
3. Envie `/start`
4. Siga o onboarding

## 📋 Funcionalidades Testadas

- ✅ Conexão com Telegram
- ✅ Firebase Firestore
- ✅ Cloudinary
- ✅ Onboarding
- ✅ Sistema de postagem
- ✅ Interações (match, favorite, comments)
- ✅ Navegação de mídia
- ✅ Menu principal
- ✅ Idempotência e Antispam

## 🔧 Solução de Problemas

### Erro: "ModuleNotFoundError"

```bash
pip install -r requirements.txt
```

### Erro: "Firebase credentials not found"

O arquivo `firebase_credentials.json` já está incluído. Se removido, recrie com:

```json
{
  "type": "service_account",
  "project_id": "liberall-galery",
  "private_key": "...",
  "client_email": "firebase-adminsdk-fbsvc@liberall-galery.iam.gserviceaccount.com"
}
```

### Erro: "Bot token invalid"

Verifique se `TELEGRAM_BOT_TOKEN` no `.env` está correto.

## 📁 Estrutura

```
LiberALL-Bot/
├── main.py                    # ✅ Arquivo principal
├── config.py                  # ✅ Configurações
├── requirements.txt           # ✅ Dependências
├── .env                       # ✅ Variáveis (incluído)
├── firebase_credentials.json  # ✅ Credenciais (incluído)
├── services/                  # ✅ Todos os serviços
├── handlers/                  # ✅ Todos os handlers
├── constants/                 # ✅ Callbacks normalizados
├── core/                      # ✅ UI Builder V2
├── models/                    # ✅ Modelos Firebase
└── utils/                     # ✅ Utilitários
```

## 🎯 Próximos Passos

1. **Testar no Telegram:** `/start` no bot
2. **Criar posts:** Usar menu principal
3. **Interagir:** Match, favoritar, comentar
4. **Configurar grupos:** Adicionar bot aos grupos Lite e Premium

## 📞 Suporte

- **Repositório:** https://github.com/techiaemp-netizen/LiberALL-Bot
- **Issues:** https://github.com/techiaemp-netizen/LiberALL-Bot/issues

## ⚠️ Importante

- Este bot usa **aiogram 3.3.0** (não pyTelegramBotAPI)
- Firebase e Cloudinary já estão configurados
- Não é necessário criar arquivo `.env` (já incluído)
- Não é necessário criar `firebase_credentials.json` (já incluído)

---

**Desenvolvido e testado em:** 2025-01-18  
**Versão:** 1.0.0  
**Status:** ✅ Produção

