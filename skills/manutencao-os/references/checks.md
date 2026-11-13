# O catálogo de checks

Divisão que vale para qualquer OS: **o que é comparação de string não gasta modelo, e o que é
julgamento não vira script.**

## O que `scripts/audit.py` responde sozinho

Rode uma vez e trabalhe em cima da saída. Cada check só dispara quando o retrato mostra que ele
se aplica.

| Achado | O que pega | Só dispara se |
|---|---|---|
| `link_quebrado` | wikilink e link relativo sem alvo, já decodificando `%20` e resolvendo profundidade | sempre |
| `wikilink_ambiguo` | `[[nome]]` que resolve para mais de um arquivo | sempre |
| `orfa` | nota com **zero link de entrada** | o OS de fato usa links |
| `indice_incompleto` | arquivo existe e o índice da pasta não lista | a pasta tem índice |
| `resumo_ausente` | item indexado sem frase útil ao lado | há índice, e o OS usa campo de resumo ou blocos gerados |
| `roteador_fantasma` | roteador citando comando ou arquivo que não existe | há roteador e há rituais |
| `sem_frontmatter` | falta de metadado | o OS usa frontmatter em mais de metade das notas |
| `tipo_orfao` | valor de tipo usado uma vez só enquanto outros são usados muito | há enum de fato |
| `entidade_sem_estado` | entidade com eventos e sem nota de estado | o OS tem pasta de entidades |
| `estado_sem_timeline` | estado sem camada de histórico separada | idem |
| `estado_sem_data_de_revisao` | estado sem campo de revisão | idem |
| `estado_defasado` | revisão mais velha que o último evento | idem, e há campo de revisão |
| `nome_datado_colidindo` | nome só de data repetido em pastas diferentes | o OS usa wikilink |
| `bloco_auto_vazio` | bloco gerado vazio | o OS usa blocos gerados |
| `captura_represada` | item cru parado no inbox | há inbox |
| `mesmo_nome_em_pastas` | mesmo nome de arquivo em lugares diferentes | sempre |
| `stub` | nota muito curta **em relação à mediana do próprio OS** | sempre |

Três decisões de projeto que fazem esse diagnóstico ser lido em vez de ignorado:

- **O script nunca escreve.** Diagnóstico que conserta esconde a causa.
- **Órfã é medida por links de ENTRADA**, não por "a nota tem links". A confusão entre as duas
  arestas é o erro clássico: escrever `relacionados: [[X]]` na nota liga na direção saída e não
  coloca a linha na lista de X.
- **Todo limiar é relativo ao OS**, nunca absoluto. Limiar fixo envelhece e vira falso positivo
  permanente, e falso positivo permanente mata o relatório inteiro.

## O que exige julgamento (é o seu trabalho)

| Achado | Por que script não resolve |
|---|---|
| **Fato vencido escrito no presente** | Exige comparar o conteúdo com a data de hoje e entender o que a frase afirma |
| **Contradição entre notas** | Exige ler as duas e aplicar a precedência de fonte |
| **Duplicação de verdade** | A mesma regra em dois lugares parece redundância inofensiva até divergir |
| **Escrever a frase de índice que falta** | Redação. O script aponta onde falta; a frase é sua |
| **Duplicata de conteúdo** | Mesmo assunto com palavras diferentes. Nome igual o script pega; assunto igual, não |
| **Compilar um estado que não existe** | Síntese a partir dos eventos. Nunca invente: o que a leitura não sustentar fica de fora |
| **Pasta fora do mapa declarado** | Exige comparar o disco com o que o roteador promete |
| **Entregável final morando no OS** | Exige saber para onde aquilo deveria ir |
| **Deriva de fábrica** | Exige memória entre rodadas e saber quem gera cada arquivo |

## A regra de crescimento

Sempre que você encontrar, no julgamento, um defeito que **dê para verificar por comparação de
string**, o conserto certo é escrever o check no script, não melhorar a instrução da skill.

É a única forma de a parte de julgamento encolher com o tempo em vez de crescer: cada check que
desce para a camada determinística sai da conta do julgamento para sempre. Se o OS tiver camada
de script própria, o check vai para lá; se não tiver, e o padrão se repetir, é sinal de que vale
recomendar uma.

## Prioridade

Alto, e nesta ordem, porque são os que quebram a navegação e a maioria é invisível a olho nu:

1. **Link relativo quebrado.** Não aparece no grafo de nenhuma ferramenta: só falha no clique.
2. **Entidade com eventos e sem estado.** Faz "como está isso?" custar a leitura de tudo.
3. **Item indexado sem frase útil.** Devolve o índice ao estado de lista de nomes, que é onde o
   ganho de contexto evapora.
4. **Roteador prometendo o que não existe.** É a primeira coisa que o modelo lê, então a
   promessa falsa gasta turno e cria ilusão de capacidade.
5. **Wikilink ambíguo.** Resolve para o arquivo errado sem avisar.

Médio: órfã, frontmatter inconsistente, estado defasado, captura represada. Baixo: cosmético,
e agrupe numa linha só.
