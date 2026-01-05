# Deploy Permanente - Serviços Gratuitos

Guia para hospedar o servidor em serviços gratuitos (não precisa rodar na sua máquina).

## 🚀 Opção 1: Render.com (RECOMENDADO - Mais Fácil)

### Passos:

1. **Crie uma conta em:** https://render.com (grátis)

2. **Conecte seu repositório GitHub:**
   - Faça push do código para o GitHub
   - No Render, clique em "New" → "Web Service"
   - Conecte seu repositório

3. **Configure o deploy:**
   - **Name**: `gerador-posts-instagram``
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn server:app`
   - **Plan**: Free

4. **Deploy automático:**
   - Render faz deploy automaticamente
   - Você recebe uma URL: `https://seu-app.onrender.com`
   - ✅ Pronto! Funciona 24/7

### Vantagens:
- ✅ Gratuito
- ✅ HTTPS automático
- ✅ Deploy automático do GitHub
- ✅ Sem precisar rodar na sua máquina

---

## 🚂 Opção 2: Railway.app

### Passos:

1. **Crie uma conta em:** https://railway.app (grátis com créditos)

2. **Conecte GitHub:**
   - Clique em "New Project"
   - "Deploy from GitHub repo"
   - Selecione seu repositório

3. **Configure:**
   - Railway detecta automaticamente Python
   - Adicione variável de ambiente se necessário
   - Deploy automático!

4. **URL gerada:**
   - Exemplo: `https://seu-app.up.railway.app`

### Vantagens:
- ✅ Muito fácil
- ✅ HTTPS automático
- ✅ Deploy rápido

---

## ☁️ Opção 3: Fly.io

### Passos:

1. **Instale o Fly CLI:**
   ```bash
   # Windows (PowerShell)
   iwr https://fly.io/install.ps1 -useb | iex
   ```

2. **Login:**
   ```bash
   fly auth login
   ```

3. **Deploy:**
   ```bash
   fly launch
   ```

4. **URL gerada:**
   - Exemplo: `https://seu-app.fly.dev`

---

## 📦 Preparação do Código

### 1. Ajustar server.py para produção:

O arquivo já está configurado, mas para produção você pode mudar:

```python
# No final do server.py, mude para:
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
```

### 2. Criar arquivo .gitignore (se não existir):

```
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
.venv
temp/
*.log
.DS_Store
output/images/*.jpg
output/data/*.json
```

### 3. Fazer push para GitHub:

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin SEU_REPOSITORIO_GITHUB
git push -u origin main
```

---

## 🔧 Configurações Importantes

### Variáveis de Ambiente (se necessário):

No Render/Railway, você pode adicionar variáveis de ambiente:
- `PYTHON_VERSION=3.12.0`
- `PORT=5000` (geralmente automático)

### Limitações dos Planos Gratuitos:

- **Render**: Pode "dormir" após 15min de inatividade (primeira requisição é mais lenta)
- **Railway**: Créditos limitados (mas suficiente para uso moderado)
- **Fly.io**: 3 apps grátis

---

## 📝 Checklist de Deploy

- [ ] Código no GitHub
- [ ] `requirements.txt` atualizado
- [ ] `Procfile` criado (para Heroku/Render)
- [ ] `runtime.txt` criado (opcional)
- [ ] Conta criada no serviço escolhido
- [ ] Repositório conectado
- [ ] Deploy realizado
- [ ] URL testada

---

## 🎯 Recomendação

**Use Render.com** - É o mais fácil e confiável para começar:
1. Crie conta
2. Conecte GitHub
3. Deploy automático
4. Pronto! URL permanente funcionando 24/7

---

## 🆘 Problemas Comuns

### "Build failed"
- Verifique se `requirements.txt` está correto
- Certifique-se de que todas as dependências estão listadas

### "App sleeping"
- Render free plan "dorme" após inatividade
- Primeira requisição pode demorar ~30s
- Upgrade para plano pago remove isso

### "Port error"
- Render/Railway definem a porta automaticamente
- Use `os.environ.get('PORT', 5000')` no código

