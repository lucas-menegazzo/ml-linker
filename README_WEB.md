# Interface Web - Gerador de Posts Instagram

Interface web para gerar posts do Instagram com links de afiliado do Mercado Livre.

## Como Usar

### 1. Instalar Dependências

```bash
pip install -r requirements.txt
```

### 2. Iniciar o Servidor

```bash
python server.py
```

### 3. Acessar a Interface

Abra seu navegador em: **http://localhost:5000**

## Funcionalidades

### ✅ Gerador de Links de Afiliado
- Cole seu **Social Code** (link de afiliado do Mercado Livre)
- Cole o **link do produto**
- Gera automaticamente o **link de afiliado** combinando ambos

### ✅ Adicionar ao CSV
- Adiciona automaticamente o link de afiliado ao `input/products.csv`
- Visualiza o CSV atual
- Baixa o CSV atualizado

### ✅ Gerar Imagem
- Gera automaticamente a imagem do post Instagram
- Preview da imagem gerada
- Baixar ou copiar a imagem

### ✅ Copiar Links
- Copia o link de afiliado com um clique
- Copia a imagem para área de transferência

## Padrão de Links de Afiliado

O sistema identifica automaticamente:
- **ID do Produto**: Extrai `MLB-XXXXXXXXX` do link do produto
- **Social Code**: Seu link de afiliado do Mercado Livre
- **Link Final**: Combina ambos seguindo o padrão do Mercado Livre

### Exemplo:
- **Produto**: `https://produto.mercadolivre.com.br/MLB-4049279695-...`
- **Social Code**: `https://www.mercadolivre.com.br/social/lm-vendas?matt_word=...`
- **Link Gerado**: `https://www.mercadolivre.com.br/social/lm-vendas?matt_word=...&mlm=4049279695`

## Estrutura

```
web_interface.html  - Interface web (frontend)
server.py          - Servidor Flask (backend)
input/products.csv - CSV com links de produtos
output/images/     - Imagens geradas
```

## Notas

- O servidor roda na porta **5000** por padrão
- As imagens são salvas em `output/images/`
- O CSV é atualizado automaticamente
- Você pode usar a interface ou continuar usando `python main.py`

