# Documentação do Projeto - Sistema Monarca Curva ABC

## Visão Geral
Sistema desenvolvido em Python + Streamlit para análise de Curva ABC e Sugestão de Compras baseada em regras personalizadas.

## Funcionalidades
1. **Sugestão de Compra** (Aba Principal)
   - Filtros hierárquicos (N1 a N4) com ordenação alfabética e visualização `Descrição (Código)`.
   - Filtro por Curva ABC (Multiseleção com destaque visual).
   - Cálculo de sugestão baseado em venda média e estoques.
   - **Tabela Zebrada**: Linhas alternadas em azul para facilitar leitura.
   - **Alertas**: Destaque amarelo para produtos que necessitam de atenção.
   - **Exportação Excel**: Arquivo com nome dinâmico (`Sugestao_AAAA-MM-DD_HH-MM-SS.xlsx`) e formatação idêntica à tela (Zebrado + Alertas).

2. **Calcular ABC** (Aba Secundária)
   - Define automaticamente o período de análise (Padrão: 2 anos atrás até hoje).
   - Processamento da Curva ABC por Nível 1.
   - Atualização automática de cadastros no banco de dados (Classe e Média).

3. **Configuração** (Aba Terciária)
   - Cadastro de Regras de Sugestão.
   - Interface amigável com filtros para localizar regras existentes.
   - Definição de Mês Mínimo e Máximo por combinação de Níveis e Classe ABC.

## Requisitos de Instalação

### 1. Dependências do Python
Caso vá executar pelo código fonte:
O sistema requer Python 3.9+ instalado.
Instale as bibliotecas listadas em `requirements.txt`:
```bash
pip install -r requirements.txt
```

### 2. Banco de Dados
O sistema conecta-se a um banco Firebird.
Execute o script `script_banco.sql` para criar a tabela de regras necessária:
- Tabela `SUGESTAO_NIVEL`

### 3. Configuração
Verifique o arquivo `src/config.py` ou `.env` para apontar para o caminho correto do banco de dados Monarca.

## Como Iniciar
**Método Recomendado (Usuário Final):**
Basta dar dois cliques no arquivo executável:
-> **MonarcaABC.exe**
*Nota: O sistema iniciará em modo silencioso (sem janelas pretas) e abrirá o navegador automaticamente.*

**Método Desenvolvedor (Logs):**
Via terminal na pasta raiz:
```bash
streamlit run app_ui.py
```

## Suporte
Desenvolvido para integração com Sistema Monarca.
