# Phase 1.5 — painel de controlos negativos realistas

## Pergunta

Depois da Phase 1, a pergunta deixou de ser "o AS4.2 tem uma superfície exposta?" e passou a ser mais exigente:

> A superfície centrada em `Y/FSTDTQ` continua suficientemente distinta quando comparada com TCRs humanos reais que partilham TRAV21, TRBV9 ou motivos CDR3β parecidos?

Esta fase não assume que estes TCRs sejam causalmente patogénicos em espondiloartrite axial. A associação à doença e a relevância terapêutica continuam a ser hipóteses.

## Auditoria da Phase 1

Os quatro scripts originais foram relidos e executados de novo:

```text
python3 scripts/analyze_tcr_surface.py
python3 scripts/compare_natural_controls.py
python3 scripts/analyze_hotspot_chemistry.py
python3 scripts/analyze_interface_geometry.py
```

Com um ambiente Python contendo `numpy`, os ficheiros em `results/` foram reproduzidos sem diferenças no Git. Isto verifica os valores já reportados para SASA, RMSD, cadeias D/F, motivo CDR3β e conclusão F98/Y98.

Ponto operacional: o `python3` do sistema local não tinha `numpy`; foi adicionado `requirements.txt` para tornar a dependência explícita.

## Proveniência do painel

Foi criado um painel com entradas humanas reais de TCR3d e estruturas RCSB PDB. A tabela rastreável está em `data/phase1_5_negative_controls.csv`; os registos brutos TCR3d usados estão em:

- `data/provenance/tcr3d_alpha_records.json`
- `data/provenance/tcr3d_beta_records.json`

Fontes:

- TCR3d alpha: `https://tcr3d.ibbr.umd.edu/tcra`
- TCR3d beta: `https://tcr3d.ibbr.umd.edu/tcrb`
- RCSB PDB para cada estrutura listada.

Nenhuma sequência, gene V, cadeia ou anotação biológica foi inventada. Quando TCR3d marca uma atribuição como aproximada, isso permanece registado na tabela.

## Controlos incluídos

O painel cobre:

| Classe | Estruturas | Razão |
|---|---|---|
| Positivos | 7N2O, 7N2N | AS4.2 TRAV21/TRBV9 `VGLFSTDTQ` |
| Negativos naturais próximos | 7N2P, 7N2Q, 7N2S | AS4.3/AS3.1 com `Y/FSTDTQ` relacionado |
| Negativos de motivo próximo | 8CX4, 9PBG, 9PBH | TRAV21/TRBV9 com `VGTYSTDTQ` ou `PATYSTDTQ` |
| Negativos germinais difíceis | 8RYP, 8RYQ | TRAV21/TRBV9 mas CDR3β não relacionado |
| TRBV9 com outra alfa | 5KS9, 5KSA, 9J4S | Testa reconhecimento dominado por TRBV9 |
| TRAV21 com outro beta | 6ZKW, 9YIR | Testa reconhecimento dominado por TRAV21 |

As estruturas novas foram descarregadas para `data/raw/`.

## Comparação computacional

O script `scripts/analyze_phase1_5_negatives.py` calcula:

- sequência CDR3β e melhor janela de nove resíduos contra `VGLFSTDTQ`;
- presença de cauda `STDTQ`;
- presença de F/Y na posição equivalente a F98;
- RMSD do framework beta contra 7N2O;
- RMSD Cα da melhor janela de nove resíduos quando comparável;
- SASA do CDR3β e da janela local no TCR isolado.

Os resultados estão em:

- `results/phase1_5/negative_control_comparison.csv`
- `results/phase1_5/negative_control_comparison.json`

## Resultados principais

Os novos negativos tornam o problema mais difícil, não mais fácil.

| Estrutura | CDR3β | Melhor 9-mer | Identidade vs AS4.2 | RMSD local vs AS4.2 | SASA do 9-mer |
|---|---|---|---:|---:|---:|
| 7N2O | `CASSVGLFSTDTQYF` | `VGLFSTDTQ` | 1,000 | 0,000 Å | 487,71 Å² |
| 7N2N | `CASSVGLFSTDTQYF` | `VGLFSTDTQ` | 1,000 | 0,501 Å | 509,76 Å² |
| 7N2S | `CASSVGLYSTDTQYF` | `VGLYSTDTQ` | 0,889 | 0,639 Å | 487,47 Å² |
| 8CX4 | `CASSVGTYSTDTQYF` | `VGTYSTDTQ` | 0,778 | 0,512 Å | 460,18 Å² |
| 9PBG | `CASSPATYSTDTQYF` | `PATYSTDTQ` | 0,556 | 0,470 Å | 459,84 Å² |
| 9PBH | `CASSPATYSTDTQYF` | `PATYSTDTQ` | 0,556 | 0,433 Å | 445,06 Å² |
| 8RYP | `CASSPGGGHNEQFF` | `PGGGHNEQ` | n/a | n/a | 339,45 Å² |
| 9J4S | `CASSVSGGAYNEQFF` | `VSGGAYNEQ` | 0,222 | 1,355 Å | 418,44 Å² |

Interpretação:

- A acessibilidade do epítopo pretendido continua confirmada.
- Múltiplos resíduos CDR3β podem, em princípio, participar numa interface.
- Mas há miméticos humanos reais com TRAV21/TRBV9 e variantes `TYSTDTQ` que têm geometria local praticamente indistinguível da região-alvo.
- 8CX4, 9PBG e 9PBH são particularmente importantes: o RMSD local fica entre 0,433 e 0,512 Å, ou seja, igual ou menor que a variação AS4.2 7N2O/7N2N.
- Portanto, forma, exposição e presença de cauda `STDTQ` não bastam para seletividade.

## Impacto sobre a hipótese

Para um binder seletivo contra a família ampla TRAV21/TRBV9–`Y/FSTDTQ`, a Phase 1.5 revela que a fronteira do alvo ainda não está suficientemente definida. Existem TCRs humanos reais com motivos muito próximos (`VGTYSTDTQ`, `PATYSTDTQ`) que provavelmente seriam difíceis de excluir se a interface reconhecer sobretudo a forma e a cauda `STDTQ`.

Para AS4.2 estrito, a decisão continua negativa para campanha ampla: a seletividade dependeria de discriminações finas de cadeia lateral, sobretudo F98 contra Y98, e agora também contra variantes `TYSTDTQ` adicionais.

Para um piloto pequeno, a única hipótese cientificamente defensável é um desenho explicitamente seletivo, com positivos e negativos simultâneos. Otimizar afinidade contra AS4.2 isolado seria pouco informativo.

## Limitações

- Esta análise usa estruturas experimentais disponíveis; não cobre todo o repertório humano.
- RMSD e SASA não são energia de ligação.
- TCR3d fornece genes por melhor correspondência de sequência; algumas entradas podem ter atribuição aproximada.
- Nem todos os negativos têm a mesma qualidade estrutural, estado ligado ou contexto antigénico.
- A análise ainda não faz docking nem perturbação energética de designs, porque essa fase só é justificada após a decisão go/no-go.

## Conclusão

A Phase 1.5 enfraquece a justificação para lançar já uma campanha de design, mesmo pequena, sem uma formulação de seletividade muito explícita.

Decisão: **NO-GO para campanha de binder contra a família ampla neste momento. GO apenas para preparar um piloto mínimo de negative design**, se o objetivo for testar se uma interface consegue depender de vários resíduos CDR3β e rejeitar simultaneamente os miméticos 7N2S, 8CX4, 9PBG e 9PBH.

