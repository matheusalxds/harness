# Relatório e modo de correção

## O relatório

Mostre no chat um resumo priorizado e, se o OS tiver onde, salve o detalhado em uma pasta
temporária ignorada pelo versionamento.

```markdown
# Saúde do OS, AAAA-MM-DD
N notas · o que este OS usa: {resumo de uma linha do retrato}

## O que mais dói agora
1. {achado alto}: {o que quebra na prática}

## Defeitos (o OS contradiz a si mesmo)
### Alto
### Médio
### Baixo

## Recomendações (boa prática que este OS ainda não tem)
Não são defeitos. Cada uma com o custo de não ter.

## Falsos positivos descartados, e por quê
## Divergências entre o script e a convenção declarada do OS
```

As duas últimas seções não são enfeite. **Achado descartado que não fica registrado volta na
próxima rodada**, e alguém gasta o mesmo tempo de novo para chegar à mesma conclusão.

Regras de tom: achado que não gera ação é ruído, não liste. Se está tudo bem, diga em uma linha
e siga. Nunca invente urgência para o relatório parecer útil.

## Modo de correção

Só depois da pessoa pedir. Nunca como parte da auditoria.

1. Rode a auditoria completa.
2. Imprima o **dry-run numerado**, uma linha por ação planejada, e pergunte:
   `"Aplicar essas N mudanças? [tudo / nenhuma / escolher por número]"`.
3. **Backup antes da primeira escrita.** Copie cada arquivo que será tocado para uma pasta
   datada, preservando o caminho relativo. Se o OS não estiver em git, este é o único desfazer.
   Se o backup falhar, aborte sem escrever nada.
   > Em macOS, `cp -R` não preserva a data de modificação. Use `cp -Rp` ou `rsync -a`.
4. Aplique só o aprovado, e registre arquivo por arquivo no relatório.

### Pode corrigir, depois de aprovado
- Link quebrado com match óbvio e único (renome, acento, maiúscula). Sem match óbvio, não force.
- Wikilink ambíguo virando link relativo.
- Campo de frontmatter faltando, **inferido do caminho e do conteúdo**. Se não der para deduzir,
  é achado, não correção.
- Campo de resumo **ausente**, escrevendo uma frase do que a nota responde. Nunca sobrescreva um
  resumo que já existe: quem escreveu escolheu aquilo.
- Entrada de `relacionados:` apontando para nota inexistente.
- Heading vazio que não tem conteúdo nem subheading abaixo (heading seguido de subheading é
  hierarquia, não seção vazia).
- Regenerar bloco gerado, se o OS tiver gerador.

### Nunca automatize
- Apagar nota, seja qual for o motivo.
- Mergear duplicata.
- Mover arquivo entre áreas.
- Alterar status de uma nota.
- Reescrever conteúdo.
- Compilar um estado que não existe. Síntese sem supervisão inventa: proponha o texto, mostre de
  onde tirou cada afirmação, e espere aprovação.
- Qualquer coisa dentro de pasta de arquivo morto. Histórico congelado não se altera.

### Duas armadilhas com custo real

- **Renomear em lote quebra quem apontava para o nome antigo, e ninguém percebe**, porque link
  relativo quebrado não aparece em grafo nenhum. Toda renomeação termina com uma varredura de
  quem referenciava o nome antigo.
- **Edição em massa destrói a data de modificação como medida de frescor.** Uma limpeza de
  formatação que toca centenas de arquivos faz o OS inteiro parecer atualizado hoje. Se for
  fazer algo assim, faça só no que já está sendo tocado por outro motivo, e prefira que o OS
  tenha um campo de revisão declarado.

## Ao terminar

1. Rode o script de novo e mostre o antes e depois em uma linha. Achado resolvido tem que sair
   da contagem; se não saiu, o conserto não pegou.
2. Se o mesmo padrão apareceu em várias notas, a raiz é o gerador (template, ritual, rotina),
   não as notas. **Corrija a fábrica, senão o problema volta a acumular amanhã.** Não mexa no
   gerador sozinho: mudar a fábrica muda o comportamento futuro de tudo, e é decisão da pessoa.
3. Se algo que você julgou à mão dá para virar código, diga: virou camada determinística e sai
   da conta do julgamento para sempre.
4. Diga em uma linha quando faz sentido rodar de novo. Padrão: mensal, ou depois de mudança
   estrutural grande.
