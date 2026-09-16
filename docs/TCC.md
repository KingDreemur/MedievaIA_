# MedievaIA: um sistema de Recuperação Aumentada por Geração aplicado a regras de Dungeons & Dragons

> **Nota de formatação.** Este documento organiza o conteúdo técnico segundo a
> estrutura da ABNT NBR 14724. A formatação física exigida pela norma (margens
> de 3 cm à esquerda e superior, 2 cm à direita e inferior; fonte Arial ou Times
> New Roman 12; espaçamento entrelinhas 1,5; recuo de parágrafo de 1,25 cm;
> citações diretas com mais de três linhas em fonte 10 e recuo de 4 cm) deve ser
> aplicada no editor de texto final. As referências seguem a ABNT NBR 6023 e as
> citações, a ABNT NBR 10520.

---

## RESUMO

Este trabalho apresenta o MedievaIA, um sistema de perguntas e respostas sobre
as regras do jogo de interpretação de papéis *Dungeons & Dragons*, construído
sobre a arquitetura de Recuperação Aumentada por Geração (RAG). O sistema indexa
o *System Reference Document* 5.2.1, distribuído sob licença Creative Commons
Attribution 4.0, e permite a incorporação de regras não oficiais criadas pelos
próprios jogadores, denominadas *homebrews*, mantendo-as distinguíveis do
conteúdo oficial durante a recuperação e a geração da resposta. O principal
desafio técnico identificado não residiu na infraestrutura de busca vetorial,
mas na recuperação da estrutura semântica do documento-fonte a partir de um
arquivo PDF diagramado em duas colunas. Demonstra-se que abordagens baseadas em
heurísticas textuais sobre fragmentos de tamanho fixo são inadequadas para essa
tarefa, e propõe-se, em substituição, a utilização dos metadados estruturais do
próprio PDF — sumário interno e hierarquia tipográfica. A solução reduziu o
código do analisador sintático de 2.298 para 169 linhas e eliminou integralmente
duas classes de erro de metadados que persistiam nas versões anteriores.

**Palavras-chave:** Recuperação Aumentada por Geração. Processamento de
Linguagem Natural. Bancos de dados vetoriais. Extração de informação.

---

## 1 INTRODUÇÃO

### 1.1 Contextualização

Modelos de linguagem de grande porte (LLMs) demonstram desempenho expressivo em
tarefas de linguagem natural, mas apresentam duas limitações relevantes quando
solicitados a responder sobre corpos normativos específicos: a tendência à
geração de conteúdo factualmente incorreto, fenômeno descrito na literatura como
alucinação, e a impossibilidade de incorporar informações posteriores ao seu
treinamento ou restritas a um contexto privado.

A arquitetura de Recuperação Aumentada por Geração, proposta por Lewis *et al.*
(2020), mitiga ambas as limitações ao acoplar um mecanismo de recuperação de
documentos a um modelo generativo: em vez de responder a partir de sua memória
paramétrica, o modelo recebe, junto à pergunta, os trechos mais relevantes de
uma base de conhecimento controlada, e é instruído a fundamentar a resposta
exclusivamente neles.

O sistema de regras de *Dungeons & Dragons* constitui um domínio de aplicação
adequado para essa arquitetura. Trata-se de um corpo normativo extenso,
fortemente interdependente e frequentemente estendido pelos próprios jogadores
por meio de regras não oficiais — os *homebrews* —, que convivem com as regras
oficiais e, por vezes, as contradizem deliberadamente.

### 1.2 Problema de pesquisa

Como construir um sistema capaz de responder a dúvidas sobre as regras de
*Dungeons & Dragons* fundamentando-se no documento oficial, admitindo
simultaneamente a incorporação de regras não oficiais e preservando, na
resposta, a distinção entre ambas as origens?

### 1.3 Objetivos

**Objetivo geral:** desenvolver um sistema de perguntas e respostas baseado em
RAG sobre o *System Reference Document* 5.2.1, com suporte à ingestão de regras
não oficiais segregadas do conteúdo oficial.

**Objetivos específicos:**

a) extrair e estruturar semanticamente o conteúdo do documento oficial a partir
   de seu formato PDF;
b) representar os trechos extraídos como vetores densos e armazená-los em um
   banco de dados com suporte a busca por similaridade;
c) implementar a etapa de recuperação por similaridade semântica;
d) implementar a etapa de geração de resposta fundamentada nos trechos
   recuperados;
e) permitir a ingestão de regras não oficiais, preservando a identificação de
   origem em todas as etapas do processo;
f) avaliar a qualidade da estruturação obtida em relação às abordagens
   anteriormente implementadas.

### 1.4 Justificativa

A relevância do trabalho é dupla. Do ponto de vista aplicado, sistemas de
consulta a regras de jogos de interpretação de papéis enfrentam o problema
concreto da coexistência entre norma oficial e norma local, que os assistentes
generalistas não resolvem. Do ponto de vista técnico, o trabalho evidencia um
problema pouco discutido na literatura aplicada de RAG: a qualidade da
segmentação do documento-fonte condiciona o desempenho de todo o restante da
cadeia, e nenhum ajuste posterior no mecanismo de recuperação compensa uma
segmentação que destruiu a estrutura do documento.

---

## 2 FUNDAMENTAÇÃO TEÓRICA

### 2.1 Representação vetorial de textos

A representação de unidades textuais como vetores densos em um espaço de alta
dimensionalidade permite que a proximidade geométrica entre vetores aproxime a
similaridade semântica entre os textos correspondentes. Tais representações,
denominadas *embeddings*, são produzidas por modelos treinados de modo que
textos de significado próximo ocupem regiões próximas do espaço vetorial.

Neste trabalho adotou-se o modelo `text-embedding-3-small`, que produz vetores
de 1.536 dimensões. A medida de proximidade utilizada é a distância de cosseno,
definida, para dois vetores **u** e **v**, como:

```
d(u, v) = 1 - (u · v) / (||u|| · ||v||)
```

A distância de cosseno é invariante à magnitude dos vetores, considerando apenas
sua orientação, o que a torna apropriada para comparar textos de comprimentos
distintos.

### 2.2 Recuperação Aumentada por Geração

A arquitetura RAG opera em duas etapas encadeadas. Na etapa de recuperação, a
pergunta do usuário é convertida em um vetor pelo mesmo modelo utilizado na
indexação, e os *k* trechos de menor distância em relação a esse vetor são
selecionados da base. Na etapa de geração, esses trechos são inseridos no
contexto de um modelo de linguagem, acompanhados de instruções que o vinculam
ao conteúdo fornecido.

A separação entre as duas etapas é o que confere ao sistema suas propriedades
desejáveis: a base de conhecimento pode ser atualizada sem retreinamento do
modelo, e a resposta pode ser rastreada até os trechos que a fundamentaram.

### 2.3 Bancos de dados vetoriais

A busca pelos vizinhos mais próximos de um vetor de consulta exige estruturas de
indexação próprias. Neste trabalho utilizou-se a extensão `pgvector` do
PostgreSQL, que adiciona ao sistema gerenciador um tipo de dado vetorial e
operadores de distância, permitindo que a busca por similaridade seja expressa
em SQL e combinada, na mesma consulta, com filtros relacionais convencionais —
recurso diretamente explorado para restringir a busca por origem do conteúdo.

### 2.4 O documento-fonte

O *System Reference Document* 5.2.1 é a parcela das regras de *Dungeons &
Dragons* disponibilizada pela Wizards of the Coast sob licença Creative Commons
Attribution 4.0 International, o que autoriza seu uso, adaptação e redistribuição
mediante atribuição. O documento possui 364 páginas, diagramação em duas colunas
e sumário interno com 520 entradas hierarquizadas em quatro níveis.

---

## 3 METODOLOGIA

### 3.1 Classificação da pesquisa

Trata-se de pesquisa aplicada, de natureza exploratória, conduzida pelo método
de desenvolvimento experimental iterativo: cada versão do sistema foi submetida
à inspeção de seus artefatos intermediários, e os defeitos identificados
orientaram a versão seguinte.

### 3.2 Materiais

**Quadro 1 – Tecnologias utilizadas**

| Componente | Tecnologia | Versão |
|---|---|---|
| Linguagem de programação | Python | 3.14 |
| Extração de PDF | PyMuPDF | 1.28.2 |
| Geração de *embeddings* | OpenAI `text-embedding-3-small` | 1.536 dimensões |
| Geração de respostas | OpenAI `gpt-4o-mini` | — |
| Banco de dados | PostgreSQL + pgvector | 16 |
| Acesso ao banco | psycopg2 | 2.9.13 |
| Testes automatizados | pytest | 9.1.1 |

Fonte: elaborado pelo autor.

### 3.3 Procedimentos

O desenvolvimento seguiu quatro fases: (i) construção de um pipeline de ingestão
funcional, ainda que com estruturação deficiente; (ii) refinamento iterativo do
analisador sintático do documento; (iii) diagnóstico da causa-raiz dos defeitos
persistentes e reformulação da abordagem de extração; (iv) implementação da
etapa de geração e do suporte a regras não oficiais.

---

## 4 DESENVOLVIMENTO

### 4.1 Arquitetura do sistema

O sistema organiza-se em um pipeline de ingestão e um pipeline de consulta, que
compartilham o banco vetorial e o modelo de *embeddings*.

```
INGESTÃO
  PDF do SRD ──┐
               ├─> extração estruturada ─> segmentação ─> embeddings ─> PostgreSQL
  .md homebrew ┘

CONSULTA
  pergunta ─> embedding ─> busca por similaridade ─> montagem de contexto
                                                          │
                                                          v
                                                   modelo generativo ─> resposta citada
```

O código final distribui-se em oito módulos, apresentados no Quadro 2.

**Quadro 2 – Módulos do sistema**

| Módulo | Responsabilidade | Linhas |
|---|---|---|
| `srd.py` | Extração estruturada do PDF oficial | 169 |
| `cli.py` | Interface de linha de comando | 97 |
| `db.py` | Persistência e busca vetorial | 68 |
| `rag.py` | Recuperação e geração da resposta | 65 |
| `homebrew.py` | Extração de regras não oficiais | 56 |
| `chunking.py` | Segmentação respeitando limites de seção | 40 |
| `embeddings.py` | Geração de *embeddings* em lote | 31 |
| `config.py` | Configuração e caminhos | 27 |
| **Total** | | **554** |

Fonte: elaborado pelo autor.

A verificação automatizada é mantida em um conjunto de 27 testes (243 linhas),
executados com a ferramenta `pytest`, que cobrem a reconstrução de palavras
hifenizadas, a derivação de tipo a partir do capítulo, a integridade dos títulos
extraídos, a ausência de vazamento de seções entre capítulos, a segregação de
origem das regras não oficiais e a marcação de procedência no contexto entregue
ao modelo generativo.

### 4.2 O problema central: recuperação da estrutura do documento

A primeira implementação do pipeline adotou a estratégia convencional de
segmentação por janela fixa: o texto extraído do PDF foi dividido em fragmentos
de 1.000 caracteres com sobreposição de 200, e os metadados de cada fragmento —
título, capítulo, seção e tipo de conteúdo — foram inferidos *a posteriori* por
heurísticas aplicadas ao texto do próprio fragmento.

Essa decisão originou todos os defeitos subsequentes. Ao segmentar o texto por
contagem de caracteres antes de identificar sua estrutura, o processo destrói
justamente a informação que as heurísticas posteriores tentam reconstruir: o
limite do fragmento não coincide com o limite da unidade semântica, de modo que
um mesmo fragmento pode conter o final de uma regra e o início de outra, sem que
nenhum sinal textual permita distingui-las.

Foram desenvolvidas dez versões sucessivas do analisador sintático na tentativa
de corrigir os sintomas dessa decisão, sintetizadas no Quadro 3.

**Quadro 3 – Evolução das versões do analisador sintático**

| Versão | Linhas | Alteração introduzida | Resultado |
|---|---|---|---|
| `parser_srd` | 313 | Classificação por marcadores lexicais de tipo | Base inicial |
| `v4` | 355 | Filtro de páginas de cabeçalho | Filtro excessivo: 0 fragmentos |
| `v4_1` | 379 | Correção do filtro; tratamento de ruído | 363 fragmentos, com páginas de índice |
| `v4_2` | 164 | Descarte por densidade numérica da linha | Supressão excessiva: 56 fragmentos |
| `v4_3` | 179 | Critério conservador de descarte | 349 fragmentos |
| `v4_4` | 172 | Ajuste na detecção de títulos | Títulos ainda contaminados por texto corrido |
| `v4_5` | 163 | Rejeição de títulos com forma de oração | Aumento de títulos indeterminados |
| `v4_6` | 164 | Busca de padrões no corpo do fragmento | Atribuição de títulos incorretos |
| `v4_7` | 198 | Busca restrita ao início do fragmento | Redução parcial do erro |
| `v4_8` | 211 | Truncamento do título em palavras funcionais | Truncamento de títulos legítimos |
| **Total** | **2.298** | | |

Fonte: elaborado pelo autor.

O comportamento da versão `v4_8` é ilustrativo do limite dessa abordagem. O
título "Exceptions Supersede General Rules" era sistematicamente truncado para
"Exceptions Supersede". A inspeção das propriedades tipográficas do PDF revelou
a causa: esse título é composto em versalete, e o interpretador de PDF o
decompõe em fragmentos de texto independentes, com tamanhos de fonte distintos
para a inicial e para o restante de cada palavra. Nenhuma heurística aplicada à
cadeia de caracteres resultante poderia recuperar o título íntegro, porque a
informação que o delimita não está no texto, e sim nos atributos de formatação
descartados durante a extração.

Identificou-se ainda um segundo defeito estrutural: a atribuição de capítulo e
seção a um fragmento era herdada do último título encontrado, sem reinicialização
nas transições de capítulo. Disso resultavam combinações inconsistentes, como um
fragmento simultaneamente atribuído ao capítulo *Spells* e à seção *Rogue*.

### 4.3 Solução adotada: aproveitamento dos metadados estruturais do PDF

A reformulação partiu da constatação de que a estrutura que se tentava inferir
já estava codificada no arquivo de origem, em duas formas complementares.

A primeira é o sumário interno do documento, que fornece 520 entradas
hierarquizadas, das quais 13 correspondem a capítulos com seus intervalos exatos
de páginas. Esses intervalos passaram a determinar, de modo determinístico, o
capítulo de cada trecho e, por consequência, seu tipo de conteúdo — um trecho é
classificado como monstro por situar-se no capítulo *Monsters*, e não por conter
a expressão "Armor Class".

A segunda é a hierarquia tipográfica. A análise da distribuição de fontes
revelou separação inequívoca entre corpo de texto e títulos, sintetizada no
Quadro 4.

**Quadro 4 – Hierarquia tipográfica identificada no documento**

| Corpo (pt) | Fonte | Função estrutural |
|---|---|---|
| 26,0 | GillSans-SemiBold | Título de capítulo |
| 18,0 | GillSans-SemiBold | Título de seção |
| 14,8 | GillSans-SemiBold | Bloco de atributos de criatura |
| 14,0 | GillSans-SemiBold | Título de subseção |
| 12,0 / 10,5 | GillSans-SemiBold | Título de bloco |
| 10,0 | Cambria | Corpo de texto |

Fonte: elaborado pelo autor, a partir da análise do documento.

O algoritmo resultante percorre o documento linearmente e classifica cada linha
como título ou corpo a partir dos atributos tipográficos de seus fragmentos de
texto, mantendo uma pilha hierárquica dos títulos vigentes. A segmentação passa
a ocorrer nos limites de título, e não em posições arbitrárias; cada unidade
semântica herda os metadados reais de sua posição na hierarquia; e a pilha é
reinicializada nas transições de capítulo, eliminando a herança indevida.

Como os fragmentos de texto de uma mesma linha são reunidos antes da
classificação, o problema do versalete deixa de existir: o título "Exceptions
Supersede General Rules" é recuperado integralmente.

Duas correções complementares de qualidade textual foram incorporadas à mesma
etapa: a reconstrução de palavras hifenizadas na quebra de linha — de modo que
"at-\ntacks" seja indexado como "attacks" — e a normalização de caracteres
tipográficos, como aspas curvas e o sinal de subtração matemático, para suas
formas ASCII equivalentes.

### 4.4 Segregação de regras não oficiais

O suporte a *homebrews* foi implementado sobre a mesma cadeia de ingestão. Os
arquivos de regras não oficiais, redigidos em Markdown, têm sua hierarquia
extraída dos níveis de cabeçalho e são persistidos na mesma tabela do conteúdo
oficial, distinguidos pelos atributos `source_type` e `source_name`.

Essa decisão de modelagem permite que a distinção se propague por todas as
etapas subsequentes sem duplicação de código: a busca vetorial admite filtro por
origem na própria cláusula SQL, e o contexto entregue ao modelo generativo marca
cada trecho como oficial ou não oficial. As instruções do sistema determinam,
adicionalmente, que divergências entre uma regra da casa e a regra oficial
correspondente sejam explicitadas na resposta.

### 4.5 Correções de engenharia

Três defeitos operacionais foram corrigidos na reformulação:

a) **Duplicação de registros.** A carga anterior inseria registros sem remover
   os da execução precedente, o que produziu 1.938 registros onde se esperavam
   364 e exigia truncamento manual da tabela. A operação de carga passou a
   remover e reinserir os registros da origem correspondente em transação única,
   tornando a ingestão idempotente.

b) **Geração sequencial de *embeddings*.** As requisições eram emitidas
   individualmente, uma por fragmento. Passaram a ser emitidas em lotes de 100,
   reduzindo em duas ordens de grandeza o número de requisições.

c) **Exposição de credenciais.** O arquivo de variáveis de ambiente, contendo
   chave de API e senha do banco, encontrava-se sob controle de versão. Foi
   removido do rastreamento e substituído por um arquivo de exemplo sem valores,
   acompanhado da declaração de exclusões apropriada.

---

## 5 RESULTADOS E DISCUSSÃO

### 5.1 Resultados da estruturação

A Tabela 1 compara a estruturação obtida pela melhor versão da abordagem
heurística e pela abordagem baseada em metadados estruturais.

**Tabela 1 – Comparação entre as abordagens de estruturação**

| Métrica | Heurística (`v4_8`) | Metadados estruturais |
|---|---:|---:|
| Unidades semânticas extraídas | 349 | 2.171 |
| Fragmentos indexáveis | 349 | 2.377 |
| Títulos indeterminados | presentes | 0 |
| Inconsistências capítulo/seção | presentes | 0 |
| Linhas de código do analisador | 2.298 | 169 |
| Arquivos do analisador | 10 | 1 |
| Testes automatizados | 0 | 27 |

Fonte: elaborado pelo autor.

O aumento no número de unidades extraídas não decorre de fragmentação
adicional, mas de granularidade semântica: cada regra, magia ou bloco de
atributos de criatura passou a constituir uma unidade própria, ao passo que a
segmentação por janela fixa agregava indiscriminadamente conteúdos contíguos.

A distribuição das unidades por tipo, derivada dos capítulos do documento,
consta da Tabela 2.

**Tabela 2 – Distribuição das unidades semânticas por tipo**

| Tipo | Unidades |
|---|---:|
| Regra | 431 |
| Classe de personagem | 427 |
| Magia | 394 |
| Criatura | 368 |
| Item mágico | 314 |
| Equipamento | 191 |
| Origem de personagem | 32 |
| Talento | 14 |
| **Total** | **2.171** |

Fonte: elaborado pelo autor.

A consistência hierárquica pode ser verificada pela cardinalidade das seções: o
capítulo *Classes* produziu exatamente doze seções, correspondentes às doze
classes de personagem do documento, sem vazamento de seções de outros capítulos.

### 5.2 Discussão

O resultado central deste trabalho não é quantitativo, mas metodológico. As dez
versões do analisador sintático consumiram esforço de desenvolvimento
substancial e produziram, ao final, um artefato ainda defeituoso, porque todas
partiam de uma premissa equivocada: a de que a estrutura de um documento pode
ser reconstruída a partir de seu texto, depois de descartados os atributos que a
codificam.

A abordagem adotada em substituição é simultaneamente mais simples e mais
correta — reduziu o código do analisador em 93% e eliminou as duas classes de
defeito persistentes. Isso sugere uma diretriz aplicável a sistemas de RAG em geral: a
extração deve preservar a estrutura do documento-fonte, e a segmentação deve
respeitá-la, antes que qualquer esforço seja investido no ajuste do mecanismo de
recuperação.

### 5.3 Limitações

Três limitações devem ser registradas:

a) **Extração de tabelas.** Os blocos de atributos de criaturas são dispostos em
   tabelas cujo conteúdo é linearizado durante a extração, resultando em
   sequências de leitura difícil. A informação é preservada, mas sua precisão
   para consultas a valores numéricos específicos não foi verificada.

b) **Dependência de convenções tipográficas.** A detecção de títulos apoia-se nas
   fontes empregadas neste documento. A aplicação a outro PDF exige a
   reidentificação de sua hierarquia tipográfica.

c) **Ausência de avaliação end-to-end.** Foram medidas a qualidade estrutural da
   base e a consistência dos metadados. A qualidade das respostas geradas não
   foi submetida a avaliação sistemática, o que exigiria a construção de um
   conjunto de perguntas com respostas de referência.

---

## 6 CONSIDERAÇÕES FINAIS

O trabalho alcançou os objetivos específicos propostos: o documento oficial foi
estruturado semanticamente, representado vetorialmente e armazenado em banco com
suporte a busca por similaridade; as etapas de recuperação e de geração foram
implementadas; e a ingestão de regras não oficiais foi viabilizada com
segregação de origem preservada em todo o percurso.

A contribuição mais relevante situa-se no diagnóstico do problema de
estruturação. A constatação de que o insucesso de dez versões sucessivas do
analisador decorria de uma decisão arquitetural tomada na primeira delas — e não
da insuficiência das heurísticas — reorientou o desenvolvimento e produziu uma
solução substancialmente menor e mais correta.

Como trabalhos futuros, indicam-se: a construção de um conjunto de avaliação
com perguntas e respostas de referência, permitindo medir precisão e revocação
da recuperação; a extração estruturada das tabelas de atributos de criaturas; a
investigação de estratégias de recuperação híbrida, combinando busca vetorial e
busca lexical; e o desenvolvimento de uma interface web que dispense o uso da
linha de comando.

---

## REFERÊNCIAS

ASSOCIAÇÃO BRASILEIRA DE NORMAS TÉCNICAS. **NBR 6023**: informação e
documentação: referências: elaboração. Rio de Janeiro: ABNT, 2018.

ASSOCIAÇÃO BRASILEIRA DE NORMAS TÉCNICAS. **NBR 10520**: informação e
documentação: citações em documentos: apresentação. Rio de Janeiro: ABNT, 2023.

ASSOCIAÇÃO BRASILEIRA DE NORMAS TÉCNICAS. **NBR 14724**: informação e
documentação: trabalhos acadêmicos: apresentação. Rio de Janeiro: ABNT, 2011.

LEWIS, Patrick *et al.* Retrieval-augmented generation for knowledge-intensive
NLP tasks. In: CONFERENCE ON NEURAL INFORMATION PROCESSING SYSTEMS, 34., 2020.
**Advances in Neural Information Processing Systems**. [*S. l.*]: Curran
Associates, 2020. p. 9459-9474.

VASWANI, Ashish *et al.* Attention is all you need. In: CONFERENCE ON NEURAL
INFORMATION PROCESSING SYSTEMS, 31., 2017. **Advances in Neural Information
Processing Systems**. [*S. l.*]: Curran Associates, 2017. p. 5998-6008.

WIZARDS OF THE COAST. **System Reference Document 5.2.1**. [*S. l.*]: Wizards of
the Coast, 2025. Licenciado sob Creative Commons Attribution 4.0 International.

> **Observação.** As referências acima cobrem as fontes efetivamente utilizadas
> na fundamentação. Recomenda-se complementá-las conforme as exigências da
> instituição, verificando paginação e data de acesso das fontes eletrônicas.
