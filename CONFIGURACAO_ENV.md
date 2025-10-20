# Configuração do .env

## 📋 Arquivo .env Necessário

O bot precisa de um arquivo `.env` na raiz do projeto com as credenciais.

## 🚀 Opção 1: Usar .env.production (Recomendado)

O arquivo `.env.production` já está incluído no repositório com todas as credenciais de produção.

**Basta renomear:**

```bash
cp .env.production .env
```

## 🔧 Opção 2: Criar Manualmente

Se preferir criar do zero, crie um arquivo `.env` com:

```env
# Telegram Bot
TELEGRAM_BOT_TOKEN=7652219810:AAG_Lv8jN40ZHNq4dK9agQxcZ7fF1yp-sYI
BOT_USERNAME=liberalmatch_bot

# Firebase
FIREBASE_PROJECT_ID=liberall-galery
FIREBASE_DATABASE_URL=https://liberall-galery-default-rtdb.firebaseio.com
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQDBsSeVqTEQsywz\nEynTWKpD6SUSYSB6UhZ/Fa1qmYOCQqzhS007hyPn5iUefxWmsQOD5V/zkK74QDcP\nZvC9CdiCKHg3I/xmaAo+XMdJu5dvp3xmt9qSOWC2q3UOty9FR28SI0L3jb/7FbGr\nLtNt9iJBN5/4y1PnHvJh0BdURI8dTHPwyHG492KMQpd46Kpn2qrpY9bh0tdwJGNt\njVdEAvb0faK4YZenVvQeV6yR1kKg6xysuC1asZCnKwFL5PPIz0tTpdgkStb5L6uh\nPwCfwrs/3LHrDyASf3SNcPy2T09/7O5kI0lhzm6cESnd0im2jYIzWrbAwUq2DOjn\gk2CVWMxAgMBAAECggEAAayAmmz5UW2l9Yfzl/nTk1rff6mZlpsGNR68e6/0JIHD\ntWj23nYYvdFbJjjBjh9S8nk+tM0eA6N87P1LZMEnTFp8jaKaH4RZcdAQEWjddQ5e\nyf204KfTUv13dBCKKC8W9HJ78BBwWDjIAGIQcKTkfK6Au41TcNtEwOqud+4a0+1J\nn4YgylZIIqyFWPQERvfQ9NUWs2srMWODRl2McUmViCKGhpkAcXJ/71eXlGw84Ky8\nil+enhjutpppSWpG++60/Ej5gAvUqeblZPJj2yuW/2udUEfx8DEXn8FMCmamabRc\nnJvQhauLqdiJug83vVdJAT3brglIWzMURtBgC4uuoQKBgQDvrq3TVjEsK9MtBIx2\nahYL5L3y3YJWOozX+Xz//aEr0NOUCBSwYhCpGSOE3gzfjVEpu3Hb2KSMHs+iKKjy\nRa0w5Isoxwd3Ewkelibpir/YHRIWhOuZUxZGY1JrXlFbVPzpv9lcKt2PIRtR6faC\nCYjGMtcKVpHDCaVO0pQHBNjR0QKBgQDO4O4JugcF3wNiXh9IwzffLx3xHzietwd8\nSmXz2XZ9K+gPtN/Ad7DG2XWLR6ZB/ySqxK3OLNoSoe7+mR1752AHUji8yJINdh5H\n4YCwSZxOxsskQXmB9WJtR7IyEU6P88fczXSSyl7VrePtjHdQX3o7yZTM/4SV33R3\ngP9AfV1zYQKBgQCX1/M5sx493JnRqFMQZc8Hw+duqFR9KmS2ItHFH7pulsKjwqbQ\nw5/IcSumbkJ7kfy8Uoske1BrkM177wRxUCETm4Zp1AVvs3iQjxGh3QwC7w/ZgmX7\n4b53406AxOUH1oTP1YHvuRxaI+A5+d34re+fmO/RFd0MUd0PXar382MlMQKBgG6x\nF2yI5t0TWII3jlGmcqyuTz0G0YrKr+ym+iohfy62YXKV+urGoAWlsSkW6zSAyiO9\nHKomgYBauL/tOUNkp5MDQWxxfQRK4STg2bR5jnLwFx2NEvCgVUvXgtcbP4fyjkvs\neqVYNqnqYvxlnimZDJQU5dNSHKT8bRrMIMdmzKvBAoGAVzudfd9CqbnMp3zFzkny\nHL9eq7TSb/c8Oq02kqgr9A159IsrSUeMh80k0tzSIt2c5tGTGSxnxmx9l+hmeJjN\nqy0jax3QqWi6f4l3lxNRrupF8jok0MPM1aUuI8ByfWnxOjqkhrW9K4F7HbUFEcb7\nz5qc3RJjxeHLODS/ImezlF4=\n-----END PRIVATE KEY-----\n"
FIREBASE_CLIENT_EMAIL=firebase-adminsdk-fbsvc@liberall-galery.iam.gserviceaccount.com

# Cloudinary
CLOUDINARY_CLOUD_NAME=dudum2hbv
CLOUDINARY_API_KEY=335884984813725
CLOUDINARY_API_SECRET=pgS6Gti79MZo-oUAolv3_YK3B00

# Grupos Telegram
FREEMIUM_GROUP_ID=-1002620620239
PREMIUM_GROUP_ID=-1002680323844

# Configurações
POST_RENDER_MODE=carousel
BLUR_PREVIEW_FOR_MONETIZED=true
LITE_MONTHLY_POST_LIMIT=5

# Security
ENCRYPTION_KEY=UHJvZHVjdGlvbl9FbmNyeXB0aW9uX0tleV8zMl9CeXRlcw==
JWT_SECRET=production_jwt_secret_key_very_secure_32_chars_min
FERNET_KEY=F1E18EDOL8qQPphlm7jmGmc-SS9nIxvUNQ4w9hlajR4=
```

## ✅ Verificação

Após criar o `.env`, teste:

```bash
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('✅ .env OK' if os.getenv('TELEGRAM_BOT_TOKEN') else '❌ .env não encontrado')"
```

## 📋 Checklist

- [ ] Arquivo `.env` existe na raiz do projeto
- [ ] `TELEGRAM_BOT_TOKEN` está preenchido
- [ ] `FIREBASE_PROJECT_ID` está preenchido
- [ ] `CLOUDINARY_CLOUD_NAME` está preenchido
- [ ] Grupos Telegram configurados

## ⚠️ Importante

- O arquivo `.env` não é versionado no Git (está no `.gitignore`)
- Use `.env.production` como base
- Nunca commite o `.env` para repositórios públicos

---

**Dica:** Se já tem um `.env` da versão anterior, pode copiar diretamente para o novo repositório.

