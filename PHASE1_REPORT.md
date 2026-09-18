# Validação estrutural de baixo custo — AS4.2

## Estado da decisão

**Resultado provisório: GO para completar a triagem computacional barata; ainda NÃO-GO para gerar binders.** Há agora um alerta forte: os negativos naturais próximos têm praticamente a mesma geometria e área exposta do hotspot.

O AS4.2 apresenta uma superfície CDR3β ampla e geometricamente consistente nas duas estruturas experimentais analisadas. Contudo, ainda não há evidência suficiente de que essa superfície seja distinta de TCRs próximos, sobretudo AS4.1, AS4.3 e outros TCRs TRAV21/TRBV9. A condição de seletividade do objetivo permanece, por isso, por demonstrar.

## Dados e identificação

- Estruturas experimentais: 7N2O (2,30 Å) e 7N2N (2,60 Å).
- Cadeia α do TCR: D; cadeia β: F, na nomenclatura de autor dos ficheiros PDB.
- CDR3β completo observado: `ASSVGLFSTDTQYF` (F92–F105).
- Motivo característico avaliado: `VGLFSTDTQ` (F95–F103).

Os ficheiros originais foram descarregados do RCSB PDB e estão em `data/raw/`. O artigo primário é Yang et al., *Nature* (2022), DOI 10.1038/s41586-022-05501-7.

## Resultados

### Exposição ao solvente

SASA calculada por Shrake–Rupley, sonda de 1,4 Å e 480 pontos por átomo:

| Estrutura | Motivo no TCR isolado | Motivo no complexo pMHC | Fração ainda exposta no complexo |
|---|---:|---:|---:|
| 7N2O | 487,71 Å² | 180,31 Å² | 37,0% |
| 7N2N | 509,76 Å² | 207,10 Å² | 40,6% |

A repetição independente com 960 pontos deu 487,56/180,45 Å² (7N2O) e 508,28/203,67 Å² (7N2N). A diferença é pequena e não altera a interpretação.

No TCR isolado, os principais contribuintes expostos são F98 (~131–145 Å²), T100 (~75–83 Å²), L97 (~73–84 Å²), V95 (~64–68 Å²) e D101 (~45–65 Å²). G96 e Q103 oferecem pouca superfície própria. F98, S99 e T100 ficam fortemente ocupados pelo pMHC no estado ligado.

### Estabilidade geométrica

Após alinhar 94 Cα do arcabouço variável da cadeia β, excluindo CDR3β:

- RMSD do arcabouço: 0,241 Å.
- RMSD Cα do motivo F95–F103: 0,501 Å.
- Maior deslocamento individual: L97, 0,767 Å.

Isto apoia a existência de uma geometria relativamente estável em dois complexos com péptidos diferentes. Não prova rigidez no TCR livre nem cobre toda a diversidade conformacional em solução.

### Possível superfície composta

Existem resíduos expostos das duas cadeias a menos de 8 Å do motivo, incluindo regiões em D32, D47, D50, D52 e, na cadeia β, F26, F28, F30, F50 e F55. Assim, é geometricamente plausível desenhar uma interface que use o CDR3β para especificidade e contactos vizinhos para orientação/área. A lista integral está em `results/analysis.json`.

### Comparação com controlos naturais experimentais

O mesmo estudo disponibiliza estruturas que funcionam como negativos difíceis: AS4.3 em 7N2P/7N2Q/7N2R e AS3.1 com o motivo `VGLYSTDTQ` em 7N2S. A comparação quantitativa usou 7N2P, 7N2Q e 7N2S; 7N2R foi conservado como dado bruto, mas excluído desta passagem porque a sua numeração de autor está deslocada em um resíduo e requer alinhamento por sequência explícito.

| Estrutura | TCR/motivo | Substituições vs AS4.2 | RMSD Cα do motivo | SASA do motivo |
|---|---|---|---:|---:|
| 7N2P | AS4.3 `VATYSTDTQ` | G96A, L97T, F98Y | 0,612 Å | 486,67 Å² |
| 7N2Q | AS4.3 `VATYSTDTQ` | G96A, L97T, F98Y | 0,597 Å | 504,75 Å² |
| 7N2S | AS3.1 `VGLYSTDTQ` | F98Y | 0,639 Å | 487,47 Å² |

Estas diferenças de backbone são da mesma ordem de grandeza que a variação do próprio AS4.2 entre 7N2O e 7N2N (0,501 Å). A área acessível também é quase igual. Logo, **forma e área por si só não distinguem AS4.2**. A hipótese de seletividade estrita depende de reconhecer a química das cadeias laterais, sobretudo a diferença Phe/Tyr em F98/Y98; isso é possível em princípio, mas é um problema de discriminação fino e de maior risco.

### O “gancho” químico F98/Y98

Uma análise por átomo, repetida com 960 pontos de esfera, mostrou:

| Estrutura | Resíduo 98 | SASA da cadeia lateral | SASA do OH de Tyr | Distância OH(Tyr)–CZ(Phe de 7N2O) |
|---|---|---:|---:|---:|
| 7N2O | Phe | 114,60 Å² | — | — |
| 7N2N | Phe | 123,78 Å² | — | — |
| 7N2P | Tyr | 132,92 Å² | 51,79 Å² | 1,97 Å |
| 7N2Q | Tyr | 131,19 Å² | 51,56 Å² | 1,76 Å |
| 7N2S | Tyr | 139,79 Å² | 52,23 Å² | 1,85 Å |

O OH adicional da tirosina está claramente exposto e ocupa uma posição consistente. Portanto, existe uma diferença química real que um binder poderá explorar. A estratégia mais plausível seria uma cavidade hidrofóbica e geometricamente apertada em torno de Phe98: deve complementar o anel de fenilalanina, mas penalizar simultaneamente a extensão polar de Tyr98 por conflito estérico e/ou dessolvatação desfavorável. Uma interface aberta ou plana não oferece razão suficiente para rejeitar Tyr98.

Isto altera a avaliação de “impossível” para **tecnicamente plausível, mas de alto risco**. Não constitui ainda prova de seletividade energética, porque essa só aparece quando existir uma interface candidata que possa ser testada contra ambos os estados.

### Geometria de uma interface compacta

Os centroides da superfície exposta de F98, S99, T100 e D101 estão separados por ~6–10 Å em ambas as estruturas AS4.2. As respetivas direções de exposição diferem no máximo ~17°, mostrando que os quatro resíduos podem ser abordados pela mesma face de um binder.

Numa pegada geométrica de 12 Å centrada em F98:

- a área total é ~836–841 Å²;
- 56–59% pertence ao motivo CDR3β F95–Q103;
- 35–40% pertence especificamente a F98/S99/T100/D101;
- 15–20% pertence à cadeia α.

Assim, o critério de uma interface composta é geometricamente satisfeito: a ligação pode ser ancorada por contactos vizinhos sem que a superfície seja dominada por regiões germinais. Estes números descrevem uma possibilidade espacial, não uma energia de ligação.

## Risco de reação cruzada

O risco dominante é um binder reconhecer sobretudo elementos germinais TRAV21/TRBV9 ou a forma geral da superfície, em vez do clonótipo AS4.2. O artigo primário confirma vizinhos naturais muito difíceis no mesmo doente: AS4.1 `VGLYSTDTQ` e AS4.3 `VATYSTDTQ`. Estes são controlos obrigatórios, não opcionais. A estrutura 7N2S fornece evidência experimental para um TCR AS3.1 com o mesmo motivo beta de AS4.1, mas não substitui perfeitamente AS4.1 porque a cadeia α/CDR3α é diferente.

Foi criado um painel inicial em `data/negative_controls.csv`, contendo:

- AS4.1 e AS4.3 como negativos naturais próximos;
- mutações alanina em F98, S99, T100, D101 e Q103;
- um TCR TRAV21/TRBV9 com CDR3 não relacionado;
- um TCR TRBV9 com outra cadeia α;
- um TCR não relacionado como controlo fácil.

Os últimos três exigem seleção de sequências de repertório. AS4.3 já dispõe de estruturas experimentais; o AS3.1 de 7N2S cobre a substituição beta F98Y, mas o AS4.1 exato e as mutações alanina continuam a exigir modelos comparáveis.

## Critérios go/no-go antes de design de proteínas

Avançar para RFdiffusion/BindCraft apenas se todos os pontos seguintes forem satisfeitos:

1. O patch candidato mantiver pelo menos ~400 Å² de SASA no TCR livre em 7N2O e 7N2N, sem depender de uma única conformação cristalina.
2. O motivo mantiver RMSD Cα ≤ 1,0 Å entre estados experimentais após alinhamento do domínio variável.
3. AS4.1, AS4.3 e o negativo TRAV21/TRBV9 mostrarem diferenças químicas locais exploráveis pelo binder, sobretudo em torno de F98/Y98 e resíduos adjacentes; diferenças de forma global não contam como satisfeitas.
4. A interface proposta conseguir reservar contactos diretos a pelo menos três resíduos do CDR3β, incluindo F98 e pelo menos um de S99/T100/D101, sem ser dominada por contactos germinais. Para seletividade AS4.2 estrita, F98 deve entrar numa cavidade apertada que penalize explicitamente o OH de Y98; uma interface plana deve ser rejeitada.
5. A definição biológica de seletividade estiver fechada: AS4.2 estrito ou família patogénica Y/FSTDTQ. Para este relatório, assume-se **AS4.2 estrito**.

Os critérios 1 e 2 estão satisfeitos. O critério 3 revelou risco elevado: há uma diferença química explorável, mas não separação apreciável por forma ou área. O critério 4 está geometricamente satisfeito, embora falte demonstrar seletividade energética numa interface real. O critério 5 determina a decisão final: AS4.2 estrito é NO-GO para campanha ampla; a família Y/FSTDTQ é GO estrutural condicional.

## Limitações

- SASA mede acessibilidade geométrica, não afinidade nem imunogenicidade.
- Duas estruturas do mesmo TCR não representam a dinâmica completa em solução.
- O estado ligado ao pMHC enterra grande parte do hotspot; um binder dirigido a TCR já ligado poderá competir estericamente.
- Não foram ainda avaliados contactos de cristal, glicosilação, contexto de membrana ou um repertório humano amplo.
- A especificidade terapêutica e a segurança só podem ser sustentadas mais tarde por ensaios experimentais e uma triagem de off-targets muito mais ampla.

## Reprodutibilidade

Executar a partir da raiz do projeto:

```text
python3 scripts/analyze_tcr_surface.py
```

Outputs principais:

- `results/cdr3b_sasa.csv`: SASA por resíduo do motivo.
- `results/analysis.json`: métricas de estrutura, RMSD e patch vizinho.
- `results/convergence_960/`: repetição com amostragem mais densa.
- `results/natural_control_comparison.csv`: comparação quantitativa com AS4.3 e AS3.1.
- `results/hotspot_chemistry.csv`: química e exposição atómica de F98/Y98.
- `results/interface_geometry.json`: orientação e composição de uma pegada compacta.
- `RISK_REGISTER.csv`: matriz de riscos e mitigação mínima.
- `GO_NO_GO.md`: decisão executiva final desta fase.
