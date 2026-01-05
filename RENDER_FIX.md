# 🔧 Solução para "missing python run server" no Render

## Problema:
O Render não está encontrando o comando para iniciar o servidor.

## Solução:

### Opção 1: Usar Start Command diretamente (RECOMENDADO)

No Render, no campo **"Start Command"**, cole:

```bash
gunicorn server:app --bind 0.0.0.0:$PORT --timeout 120
```

**Deixe o Build Command como:**
```bash
pip install -r requirements.txt
```

### Opção 2: Verificar se o Procfile está correto

O Procfile deve ter apenas uma linha (sem linhas vazias extras):

```
web: gunicorn server:app --bind 0.0.0.0:$PORT --timeout 120
```

### Opção 3: Usar script de inicialização

Se ainda não funcionar, crie um arquivo `start.sh`:

```bash
#!/bin/bash
gunicorn server:app --bind 0.0.0.0:$PORT --timeout 120
```

E no Start Command do Render:
```bash
bash start.sh
```

---

## ✅ Checklist:

- [ ] `requirements.txt` tem `gunicorn>=21.2.0`
- [ ] `Procfile` existe e tem o comando correto
- [ ] Start Command no Render está preenchido OU Procfile está no repositório
- [ ] Build Command: `pip install -r requirements.txt`
- [ ] Environment: Python 3

---

## 🚨 Se ainda não funcionar:

1. **Verifique os logs do Render:**
   - Vá em "Logs" no dashboard do Render
   - Veja qual é o erro exato

2. **Teste localmente primeiro:**
   ```bash
   pip install gunicorn
   gunicorn server:app --bind 0.0.0.0:5000
   ```

3. **Simplifique o comando:**
   No Start Command, use apenas:
   ```bash
   gunicorn server:app
   ```
   (O Render define a porta automaticamente)

