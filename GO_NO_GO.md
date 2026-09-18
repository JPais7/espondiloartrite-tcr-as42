# Decisão estrutural go/no-go — TCR AS4.2

## Pergunta

O AS4.2 tem uma superfície suficientemente acessível e distinta para justificar o desenho de um ligante seletivo antes de gastar recursos numa campanha de geração?

## Resposta curta

**Acessível e contactável: sim. Distinta por forma: não. Distinta por química: apenas de forma estreita e arriscada.**

Para um ligante **estritamente seletivo para AS4.2**, a decisão é **NO-GO para uma campanha ampla**. Só se justifica, no máximo, um pequeno piloto de negative design centrado numa cavidade para F98 que rejeite Y98, com critérios de abandono pré-definidos.

Para um ligante dirigido à **família patogénica TRAV21/TRBV9–Y/FSTDTQ**, a decisão estrutural é **GO condicional**, porque a semelhança que impede seletividade clonal passa a ser parte do alvo pretendido. Continuam obrigatórios controlos contra TCRs não patogénicos com os mesmos segmentos V.

## Evidência que sustenta a decisão

| Requisito | Evidência | Resultado |
|---|---|---|
| Superfície exposta | 488–510 Å² para `VGLFSTDTQ` no TCR isolado | Passa |
| Estabilidade entre estados | RMSD Cα do motivo 0,501 Å entre 7N2O e 7N2N | Passa |
| Contacto simultâneo do hotspot | F98/S99/T100/D101 separados por ~6–10 Å e orientados na mesma face | Passa |
| Pegada não dominada por regiões germinais | 56–59% da pegada geométrica de 12 Å pertence ao motivo CDR3β | Passa geometricamente |
| Distinção de controlos naturais | AS4.3 e AS3.1 têm RMSD ~0,60–0,64 Å e SASA semelhante | Não passa por forma |
| Gancho químico específico | OH de Y98 exposto (~52 Å²), ausente em F98 | Passa apenas como hipótese de cavidade seletiva |
| Cobertura de repertório | Ainda não existe triagem ampla de TCRs humanos semelhantes | Não demonstrado |

## Regra para um eventual piloto

Um piloto só deve prosseguir se for configurado desde o início para:

1. Enterrar F98 numa cavidade hidrofóbica apertada; interfaces planas são eliminadas.
2. Contactar diretamente pelo menos dois de S99, T100 e D101, além de F98.
3. Avaliar simultaneamente AS4.2 e negativos Y98 — nunca otimizar AS4.2 isoladamente.
4. Incluir AS4.3, 7N2S/AS3.1, AS4.1 modelado, um TRAV21/TRBV9 com CDR3 não relacionado e um TRBV9 com outra cadeia α.
5. Abandonar candidatos cuja margem prevista AS4.2–Y98 seja comparável à incerteza do método de scoring.

## Conclusão

A validação barata cumpriu o seu propósito: evitou interpretar uma superfície exposta como automaticamente específica. O hotspot é tecnicamente utilizável, mas a seletividade AS4.2 estrita depende de uma única discriminação fina Phe/Tyr e não está robustamente garantida pela estrutura. A opção cientificamente mais defensável é escolher explicitamente entre:

- um piloto pequeno e de alto risco para AS4.2 estrito; ou
- reformular o alvo para a família patogénica, onde a evidência estrutural é mais favorável.

Não é recomendável iniciar uma campanha de milhares de designs enquanto esta escolha biológica não estiver fechada.
