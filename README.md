# Projeto: Espondiloartrite / AS4.2 TCR

## Objetivo ativo

Validar, com baixo custo e antes de gerar proteínas, se o TCR AS4.2 apresenta uma superfície estrutural suficientemente distinta e acessível para permitir o desenho de um ligante seletivo, avaliando simultaneamente os principais riscos de reação cruzada.

Estado atual: **GO provisório apenas para completar a triagem estrutural barata; ainda não avançar para geração de binders.** Os controlos naturais próximos têm forma e área muito semelhantes ao AS4.2. Existe um possível gancho químico — o OH exposto de Y98 — mas a seletividade estrita exige uma cavidade que aceite F98 e penalize Y98. Ver [PHASE1_REPORT.md](PHASE1_REPORT.md).

Decisão final da fase estrutural: [GO_NO_GO.md](GO_NO_GO.md). Em resumo, AS4.2 estrito é NO-GO para campanha ampla; família Y/FSTDTQ é GO condicional.

## Nota operacional: armazenamento e cloud

Para a fase inicial de validacao estrutural, nao e necessario alugar armazenamento na cloud. Esta fase deve ser feita localmente, porque envolve ficheiros pequenos: estruturas PDB/mmCIF, alinhamentos, medicoes de acessibilidade, analise de interfaces, figuras e resultados leves.

Recomendacao pratica para comecar:

- Trabalhar localmente.
- Manter cerca de 5-20 GB livres para ficheiros, resultados e iteracoes leves.
- Organizar desde cedo as pastas e os criterios de retencao, para evitar acumular lixo computacional.

So faz sentido usar cloud quando o projeto passar para geracao ou avaliacao em lote, por exemplo:

- RFdiffusion / BindCraft com muitas tentativas.
- ColabFold / AlphaFold em lote para candidatos.
- Triagens grandes contra muitos negativos ou repertorios TCR.
- Simulacoes MD ou qualquer workflow que gere muitas trajetorias/intermedios.

Nessa fase, a melhor estrategia nao e "alugar espaco" isoladamente, mas sim alugar uma instancia com GPU/CPU e disco temporario rapido, correr os jobs, e depois guardar apenas os outputs importantes num bucket barato.

Estimativa de armazenamento:

- Fase barata/local: poucos MB a algumas centenas de MB; 5-20 GB livres e confortavel.
- Campanha real de design: apontar para 200-500 GB livres, idealmente em disco rapido.
- MD longa ou datasets grandes: pode subir para centenas de GB ou TB.

Politica de retencao recomendada:

- Guardar estruturas finais dos melhores candidatos.
- Guardar configs, seeds, versoes de parametros e rankings.
- Guardar metricas resumidas e logs essenciais.
- Apagar outputs intermedios volumosos que possam ser regenerados.

Risco principal da cloud:

- O armazenamento costuma ser barato.
- O custo real aparece em GPUs deixadas ligadas, grandes volumes de outputs intermedios, e transferencias repetidas de dados.

Decisao atual:

Comecar localmente. Passar para cloud apenas quando houver um lote claro de geracao/avaliacao em GPU, com regras de limpeza e arquivo ja definidas.
