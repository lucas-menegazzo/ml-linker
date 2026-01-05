# 🚀 Deploy Rápido - Render.com (GRATUITO)

## Passo a Passo (5 minutos)

### 1. Prepare o código no GitHub

```bash
# Se ainda não tem git
git init
git add .
git commit -m "Deploy ready"
git remote add origin https://github.com/SEU_USUARIO/SEU_REPO.git
git push -u origin main
```

### 2. Crie conta no Render

1. Acesse: https://render.com
2. Clique em "Get Started for Free"
3. Faça login com GitHub

### 3. Deploy

1. No Render, clique em **"New"** → **"Web Service"**
2. Conecte seu repositório GitHub
3. Configure:
   - **Name**: `gerador-posts-instagram`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn server:app`
   - **Plan**: Free
4. Clique em **"Create Web Service"**

### 4. Pronto! 🎉

Você receberá uma URL permanente:
- Exemplo: `https://gerador-posts-instagram.onrender.com`
- ✅ Funciona 24/7
- ✅ HTTPS automático
- ✅ Não precisa rodar na sua máquina

---

## ⚠️ Nota sobre Selenium

O Selenium pode não funcionar em serviços gratuitos. Se der erro, você pode:
1. Usar apenas o scraper HTML (sem Selenium)
2. Ou usar serviços que suportam Selenium (mais caros)

---

## 🔄 Atualizações

Sempre que fizer push no GitHub, o Render faz deploy automático!

```bash
git add .
git commit -m "Atualização"
git push
```

