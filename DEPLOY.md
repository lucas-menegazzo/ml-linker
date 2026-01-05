# Como Deixar o Servidor Acessível

## Opção 1: Rede Local (Mesma Wi-Fi)

O servidor já está configurado para aceitar conexões da rede local.

### Passos:

1. **Inicie o servidor:**
   ```bash
   python server.py
   ```

2. **Veja o IP local:**
   O servidor mostrará o IP local, exemplo: `http://192.168.1.100:5000`

3. **Acesse de outros dispositivos:**
   - No mesmo Wi-Fi, acesse: `http://SEU_IP:5000`
   - Exemplo: `http://192.168.1.100:5000`

4. **Configurar Firewall (Windows):**
   - Abra o Firewall do Windows
   - Clique em "Permitir um aplicativo pelo Firewall"
   - Adicione Python ou permita a porta 5000

### Comando rápido para abrir porta no Firewall (Windows):
```powershell
# Execute como Administrador
netsh advfirewall firewall add rule name="Flask Server" dir=in action=allow protocol=TCP localport=5000
```

---

## Opção 2: Internet (Acesso de Qualquer Lugar)

### 2.1 Usando ngrok (Mais Fácil)

1. **Instale o ngrok:**
   - Baixe em: https://ngrok.com/download
   - Ou use: `choco install ngrok` (se tiver Chocolatey)

2. **Inicie o servidor:**
   ```bash
   python server.py
   ```

3. **Em outro terminal, inicie o ngrok:**
   ```bash
   ngrok http 5000
   ```

4. **Use a URL fornecida:**
   - Exemplo: `https://abc123.ngrok.io`
   - Esta URL funciona de qualquer lugar!

### 2.2 Usando Cloudflare Tunnel (Gratuito)

1. **Instale cloudflared:**
   - Baixe em: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/

2. **Inicie o servidor:**
   ```bash
   python server.py
   ```

3. **Crie o tunnel:**
   ```bash
   cloudflared tunnel --url http://localhost:5000
   ```

4. **Use a URL fornecida pelo Cloudflare**

### 2.3 Usando localtunnel (Gratuito)

1. **Instale:**
   ```bash
   npm install -g localtunnel
   ```

2. **Inicie o servidor:**
   ```bash
   python server.py
   ```

3. **Crie o tunnel:**
   ```bash
   lt --port 5000
   ```

---

## Opção 3: Servidor VPS/Cloud (Produção)

Para uso em produção, considere:

1. **Render.com** (Gratuito):
   - Conecte seu repositório GitHub
   - Deploy automático

2. **Railway.app** (Gratuito):
   - Deploy simples
   - HTTPS automático

3. **Heroku** (Pago):
   - Plataforma confiável
   - Fácil deploy

4. **VPS próprio:**
   - DigitalOcean, AWS, etc.
   - Use gunicorn + nginx

---

## Segurança

⚠️ **IMPORTANTE**: O servidor atual está em modo debug e não é seguro para produção!

### Para produção, use:

```python
# No final do server.py, mude para:
app.run(debug=False, host='0.0.0.0', port=5000)
```

### Ou use gunicorn:

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 server:app
```

---

## Teste de Acesso

1. **Do mesmo computador:**
   - http://localhost:5000 ✅

2. **De outro dispositivo na mesma rede:**
   - http://SEU_IP:5000 ✅

3. **De qualquer lugar (com ngrok/tunnel):**
   - https://sua-url.ngrok.io ✅

---

## Solução de Problemas

### "Não consigo acessar de outro dispositivo"

1. Verifique se está na mesma rede Wi-Fi
2. Verifique o firewall do Windows
3. Verifique se o IP está correto: `ipconfig` (Windows) ou `ifconfig` (Linux/Mac)

### "Porta já em uso"

Mude a porta no `server.py`:
```python
app.run(debug=True, host='0.0.0.0', port=8000)  # Use outra porta
```

### "Conexão recusada"

- Verifique o firewall
- Certifique-se de que o servidor está rodando
- Verifique se está usando o IP correto

