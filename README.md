# Gerenciador de Armazenamento

Aplicativo Windows em Python para localizar todos os e-mails recebidos de um remetente específico e excluí-los permanentemente pela API oficial do Gmail. Não usa Selenium, não movimenta o mouse e não precisa deixar o Gmail aberto.

## Configuração atual

- Contas autorizadas: usuários de teste cadastrados no projeto do Google Cloud.
- Remetente filtrado: `diligencia@mlradvogados.com`.
- Consulta exata: `from:diligencia@mlradvogados.com`.
- Ação: exclusão permanente, sem passar pela lixeira.

O programa sempre analisa primeiro. A exclusão só é habilitada depois que a pessoa seleciona a opção de exclusão permanente e marca a caixa confirmando que entende que os e-mails não poderão ser recuperados.

## Segurança

- O corpo e os anexos das mensagens não são baixados.
- A tela mostra apenas assunto, data e tamanho estimado para revisão.
- Todos os IDs são coletados antes da exclusão, evitando perder resultados durante a paginação.
- O log contém somente contagens e erros técnicos; não registra assuntos nem conteúdo.
- O Google permite a conexão apenas das contas cadastradas como usuários de teste.
- `client_secret.json` e o token OAuth não entram no Git.

> **Atenção:** a exclusão é imediata e irreversível. Valide cuidadosamente a lista exibida antes de confirmar.

## Configurar o Google Cloud para a conta pessoal

1. Acesse o Google Cloud Console e abra o projeto do aplicativo.
2. Ative a **Gmail API**.
3. Em **Google Auth Platform**, configure o público como **Externo** e mantenha o aplicativo em **Teste**.
4. Adicione cada conta de colaborador que utilizará o programa como usuária de teste.
5. Adicione o escopo restrito `https://mail.google.com/`, necessário para exclusão permanente.
6. Crie um cliente OAuth do tipo **Aplicativo para computador**.
7. Baixe o JSON, renomeie-o para `client_secret.json` e coloque-o na raiz do projeto durante o desenvolvimento.

No modo de teste, o Google pode mostrar um aviso de aplicativo não verificado. A autorização expira após sete dias; quando isso acontecer, basta clicar novamente em **Conectar conta Google** e autorizar a mesma conta. Não é necessário reinstalar o programa.

Por padrão, `expected_account` fica vazio e qualquer conta aceita pelo Google Cloud pode ser conectada. Para criar uma cópia restrita a uma única conta, informe o e-mail nesse campo.

## Executar pelo VS Code

Requer Python 3.12 ou superior.

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python main.py
```

Sem `client_secret.json`, o aplicativo abre normalmente, mas informa que a autorização do Google ainda precisa ser configurada.

## Testes locais

Os testes locais não acessam o Gmail e não excluem mensagens.

```powershell
python -m unittest discover -s tests -v
```

## Gerar o executável

```powershell
.\build.ps1
```

O resultado ficará em `dist\GerenciadorDeArmazenamento`. O arquivo `client_secret.json` deve ser colocado nessa pasta para o aplicativo conseguir abrir a autorização do Google.
