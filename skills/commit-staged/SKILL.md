---
name: commit-staged
description: Commita somente o que já está na staging area, seguindo o padrão de mensagem que o próprio repo usa. Use quando o usuário pedir "commita o que está no stage", "commit staged", ou quiser commitar só os arquivos que ele já adicionou com git add. Não roda testes nem lint e não mexe no que está fora do stage; para o fluxo completo de verificação e divisão de commits, o usuário usa /generate-commit-msg.
---

# Commit do stage

## Passos

1. **Ler o stage, só ele.**
   - `git diff --cached --stat` e `git diff --cached`.
   - Se não houver nada no stage, diga isso e pare. Não rode `git add`.

2. **Descobrir o padrão do repo.**
   - `git log -20 --format=%s` no próprio repo: prefixo (`feat:`, `fix(scope):`...), escopo,
     idioma, tamanho, modo verbal.
   - Se `~/.claude/shared/commit-structure.md` existir, a tabela de prefixos por tipo de arquivo
     vale.
   - O padrão do repo vence a preferência genérica. Repo da House Numbers: sempre em inglês.

3. **Checar se o stage mistura tipos.** Se o stage tiver teste e código de produção, ou código
   e docs, ou `package.json` e código, avise e proponha a divisão (quais arquivos em qual commit).
   Não reorganize o stage sem ele concordar.

4. **Propor a mensagem.** Uma linha de até 100 caracteres, descrevendo a intenção, não os
   arquivos. Sem travessão (em dash) e sem buzzword. Mostre a mensagem e a lista de arquivos.

5. **Commitar só depois do "pode".** `git commit -m "<mensagem>"`. Depois, `git log -1 --stat`
   para mostrar o resultado.

## Regras
- Nunca `git add`, `git commit -a`, `--amend`, `--no-verify` nem push.
- Se um hook de pre-commit falhar, mostre o erro e pare. Não contorne.
