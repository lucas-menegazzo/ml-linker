# Configuração Render.com

## Start Command (Cole no Render):

```
gunicorn server:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120
```

## Build Command:

```
pip install -r requirements.txt
```

## Environment Variables (Opcional):

- `PYTHON_VERSION`: `3.12.0` (ou deixe em branco para usar o padrão)

## Health Check Path:

```
/api/test
```

## Notas:

- O Render detecta automaticamente o Python
- O `$PORT` é definido automaticamente pelo Render
- Se o Procfile estiver no repositório, você pode deixar o Start Command em branco

