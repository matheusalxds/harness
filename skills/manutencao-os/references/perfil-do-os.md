# Fase 1: reconhecer o OS antes de julgar

Auditar sem reconhecer é como revisar um texto sem saber o idioma. O retrato define **quais
checks fazem sentido** e **qual é a régua**.

```bash
python3 scripts/audit.py <raiz-do-os> --perfil
```

## O que o retrato diz, e o que cada linha implica

| Linha | Se tem | Se não tem |
|---|---|---|
| **roteadores** | O modelo desce por eles: cobre roteador que promete o que não existe | Recomende criar um. Sem roteador, toda pergunta vira varredura de pasta |
| **índices de pasta** | Cobre índice incompleto e frase de índice inútil | Recomende, mas só em pasta com muitas notas |
| **entidades** (pasta com nota homônima) | Cobre estado ausente, defasado e sem timeline | O OS não tem entidade repetida: pule o bloco inteiro |
| **blocos gerados (AUTO)** | Nunca edite dentro deles: corrija a fonte e rode o gerador | Índice é curadoria manual: cobre menos, e nunca "regenere" nada |
| **frontmatter (%)** | Acima de 50%, ausência vira inconsistência | Abaixo disso, **não é assunto**. Não cobre |
| **campo de resumo (%)** | Acima de 40%, cobre onde falta | Abaixo, vira recomendação, não defeito |
| **campo de data de revisão (%)** | É a única medida de frescor confiável | Recomende. Data de modificação de arquivo não serve |
| **notas com estado + timeline** | O OS separa síntese de histórico | Se há entidade com eventos, recomende |
| **inbox** | Cobre captura represada, que é sintoma de ritual parado | Recomende acima de ~20 notas |
| **rituais** | Cobre roteador citando comando inexistente | Recomende o par de abrir e fechar |
| **camada de script** | **Ela é a autoridade.** Rode a dela primeiro | `audit.py` faz o papel dela |

## A régua adaptativa, e por que ela existe

O script não pergunta "este OS segue a boa prática?". Ele pergunta **"este OS é consistente
consigo mesmo?"**. A diferença é o que separa um diagnóstico útil de um sermão.

Três exemplos do que isso muda na prática:

- **Nota órfã.** Num OS que linka, nota que ninguém cita está perdida. Num OS que não usa link
  nenhum, "zero links de entrada" descreve todas as notas e não é achado, é a forma dele. O
  script só cobra órfã quando a densidade de links passa de um mínimo.
- **Stub.** Vinte palavras é stub num vault de ensaios e é tamanho normal num diário. O limiar é
  relativo à **mediana do próprio OS**, nunca um número absoluto.
- **Frontmatter.** Cobrar metadado de quem escolheu não usar metadado é transformar o estilo da
  pessoa em defeito.

Toda vez que você for cobrar algo, faça a pergunta: **isso contradiz o que este OS já faz, ou
só contradiz o que eu acho bonito?** Se for a segunda, é recomendação.

## Ler o documento de convenções

Se o retrato apontar um documento de convenções, **leia inteiro antes de julgar**. Ele vence o
script e vence você. Anote as divergências: onde o script cobrar algo que a convenção
explicitamente dispensa, o achado é do script, e você registra isso no relatório em vez de
mandar a pessoa consertar a nota.

## Perguntar, quando ainda restar dúvida

Duas perguntas resolvem quase tudo que o retrato não responde, e valem o turno:

1. **"Tem alguma parte do OS que é assim de propósito e eu não devo mexer?"**
2. **"O que te incomoda hoje quando você vai usar isso?"**

A segunda costuma valer mais que metade dos checks: ela aponta a dor real, e a dor real deve
liderar o relatório.
