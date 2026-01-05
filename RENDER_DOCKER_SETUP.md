# Configuração do Render com Docker e Selenium

## ✅ O que foi configurado:

1. **Dockerfile** criado com:
   - Python 3.11
   - Google Chrome instalado
   - ChromeDriver instalado e configurado
   - Todas as dependências do sistema necessárias

2. **render.yaml** atualizado para usar Docker

3. **Código melhorado** para detectar Chrome automaticamente

## 📋 Passos para configurar no Render:

### 1. No painel do Render:

1. Vá em **Dashboard** → Seu serviço web
2. Clique em **Settings**
3. Em **Environment**, certifique-se de que está usando **Docker**
4. O Render deve detectar automaticamente o `Dockerfile`

### 2. Se precisar configurar manualmente:

- **Build Command**: (deixe vazio, o Dockerfile faz tudo)
- **Start Command**: (deixe vazio, o Dockerfile define o CMD)
- **Environment**: Docker

### 3. Variáveis de ambiente (opcionais):

O Render define automaticamente a variável `PORT`. Não precisa configurar nada.

## 🔍 Verificando se funcionou:

Após o deploy, verifique os logs:

1. Procure por: `Found Chrome binary at: /usr/bin/google-chrome`
2. Procure por: `[OK] Chrome driver created`
3. Teste gerar uma imagem - deve usar Selenium agora!

## ⚠️ Notas importantes:

- O primeiro build pode demorar mais (instala Chrome e dependências)
- O Dockerfile instala todas as dependências necessárias
- Se o Selenium falhar, o sistema usa automaticamente o fallback Pillow
- O Chrome roda em modo headless (sem interface gráfica)

## 🐛 Troubleshooting:

Se ainda não funcionar:

1. Verifique os logs do Render para erros
2. Certifique-se de que o `render.yaml` está configurado para usar Docker
3. Verifique se o Dockerfile está na raiz do projeto
4. O Render pode precisar de alguns minutos para fazer o build completo

