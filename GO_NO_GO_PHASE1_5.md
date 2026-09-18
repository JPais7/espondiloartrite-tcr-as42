# Decisão go/no-go — Phase 1.5

## Decisão

**NO-GO para iniciar agora uma campanha de desenho de binders contra a família ampla TRAV21/TRBV9–`Y/FSTDTQ`.**

**GO apenas para preparar um piloto mínimo de negative design**, com positivos e negativos definidos antes de gerar designs.

## Porquê

Os critérios de acessibilidade continuam satisfeitos: o CDR3β de AS4.2 é exposto e geometricamente contactável. O problema é seletividade.

A inclusão de negativos humanos reais revelou miméticos difíceis:

- 8CX4: TRAV21/TRBV9 com `VGTYSTDTQ`, RMSD local 0,512 Å;
- 9PBG: TRAV21/TRBV9 com `PATYSTDTQ`, RMSD local 0,470 Å;
- 9PBH: TRAV21/TRBV9 com `PATYSTDTQ`, RMSD local 0,433 Å;
- 7N2S: TRAV21/TRBV9 com `VGLYSTDTQ`, RMSD local 0,639 Å.

Estes valores são da mesma ordem, ou melhores, que a variação observada entre as duas estruturas AS4.2. Logo, a superfície pretendida não é distintiva por forma, exposição ou cauda `STDTQ`.

## Critérios avaliados

| Critério | Resultado |
|---|---|
| Epítopo acessível | Passa |
| Vários resíduos CDR3β podem participar | Passa geometricamente |
| Seletividade não explicada por contactos TRAV21/TRBV9 germinais | Ainda não demonstrado |
| Negativos realistas não revelam mimético estrutural óbvio | Não passa |
| Incertezas documentadas | Passa |

## Regra para qualquer piloto

Um piloto só é justificável se for pequeno e configurado como negative design desde o início:

1. Positivos: 7N2O e 7N2N; opcionalmente decidir se 7N2S/8CX4/9PBG/9PBH são positivos de família ou negativos.
2. Negativos obrigatórios: 7N2P, 7N2Q, 7N2S, 8CX4, 9PBG, 9PBH, 8RYP, 8RYQ, 5KS9, 5KSA, 9J4S, 6ZKW e 9YIR.
3. Métrica primária: seletividade, não afinidade isolada.
4. Rejeitar designs cujo score venha sobretudo de superfícies conservadas TRAV21/TRBV9.
5. Rejeitar designs que não dependam de vários resíduos CDR3β.
6. Parar se os melhores candidatos não separarem AS4.2 dos miméticos `TYSTDTQ` por margem maior que a incerteza do método.

## Alternativa barata

Antes de GPU em volume, a alternativa mais barata e informativa é modelar explicitamente um pequeno conjunto de mutantes/contrafactuais:

- F98Y, F98A;
- S99A, T100A, D101A;
- troca do segmento `VGLFSTDTQ` por `VGTYSTDTQ` e `PATYSTDTQ`.

Se uma interface candidata não perder score nesses testes, deve ser abandonada.

