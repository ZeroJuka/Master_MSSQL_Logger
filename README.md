# Master MSSQL Logger

## Descrição
Este projeto é um script Python para validar e monitorar bancos de dados MSSQL, gerando relatórios HTML e enviando-os por e-mail. Ele executa validações definidas em `reports.py`, gera um relatório com destaques de status (sucesso, erro, aviso) e envia o relatório via SMTP.

O script principal é `LOG/log.py`, que se conecta ao banco de dados usando configurações de `config.py`, executa consultas de validação, constrói um relatório HTML e o envia por e-mail.

## Requisitos
- Python 3.x
- Bibliotecas: `pandas`, `pyodbc`, `smtplib`, `email` (instale via `pip install -r requirements.txt`)
- Acesso a um servidor MSSQL
- Configuração SMTP para envio de e-mails

## Configuração
1. **config.py**: Configure as credenciais do banco de dados e SMTP.
   - `SERVER`, `DATABASE`, `USERNAME`, `PASSWORD`: Detalhes de conexão MSSQL.
   - `SMTP_SERVER`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD` (opcional), `SMTP_USE_TLS` (opcional, defina como False se não usar TLS).
   - `EMAIL_FROM`, `EMAIL_TO`: Endereços de e-mail.
   - `REPORT_TITLE`, `REPORT_SUBJECT`: Títulos personalizados.

2. **reports.py**: Defina as validações como uma lista de dicionários com `name`, `description`, `query`, `status_check_column` e opcionalmente `multi_row`.

Exemplo em `config_example.py` e `reports_example.py`.

## Uso
Execute o script a partir da raiz do projeto:
- `python -m LOG.log` (recomendado)
- Ou `python "LOG/log.py"`

O script:
- Conecta ao banco de dados.
- Executa validações.
- Gera relatório HTML. Foco nas falhas: quando o status é `TRUE` o sucesso é mostrado de forma resumida (sem descrição e sem tabela de detalhes); para `FALSE`, `WARNING` ou `ERROR`, são exibidos os detalhes.
- Envia o relatório por e-mail.

## Fluxo de Execução
1. **Conexão ao Banco**: Usa `pyodbc` com `DATABASE_URL` de `config.py`.
2. **Validações**: Executa consultas de `reports.py`. Para cada:
   - Se multi-row: Retorna DataFrame com destaque na coluna de status.
   - Se single-row: Retorna dicionário com destaque no valor de status.
   - Status: TRUE (verde), FALSE/ERROR (vermelho), WARNING (amarelo).
3. **Geração de Relatório**: Cria HTML com CSS embutido e blocos `<details>/<summary>` para colapsar.
4. **Envio de E-mail**: Usa `smtplib`. Suporta sem autenticação/TLS (configure em `config.py`).

## Personalizações
- Adicione validações em `reports.py`.
- Ajuste CSS em `log.py` para estilos.
- Para SMTP sem autenticação: Omita `SMTP_PASSWORD` e defina `SMTP_USE_TLS = False`.

## Problemas Comuns e Soluções
- Erros de módulo: Certifique-se de executar da raiz ou adicione o diretório pai ao `sys.path`.
- Erros de importação: Instale dependências.
- Erros SMTP: Verifique configurações e porta (ex.: 25 para sem TLS).

Para mais detalhes, consulte o código em `LOG/log.py` e `reports.py`.