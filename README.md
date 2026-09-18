# Projeto: Espondiloartrite / AS4.2 TCR

## Objetivo ativo

Validar, com baixo custo e antes de gerar proteínas, se o TCR AS4.2 apresenta uma superfície estrutural suficientemente distinta e acessível para permitir o desenho de um ligante seletivo, avaliando simultaneamente os principais riscos de reação cruzada.

Estado atual: **Phase 1.5 completa; NO-GO para iniciar agora uma campanha de binders contra a família ampla.** Os controlos humanos realistas revelam miméticos estruturais difíceis, incluindo 8CX4 (`VGTYSTDTQ`) e 9PBG/9PBH (`PATYSTDTQ`), com geometria local semelhante à região AS4.2. Ver [PHASE1_5_REPORT.md](PHASE1_5_REPORT.md) e [GO_NO_GO_PHASE1_5.md](GO_NO_GO_PHASE1_5.md).

Decisão final da Phase 1: [GO_NO_GO.md](GO_NO_GO.md). Decisão atualizada da Phase 1.5: [GO_NO_GO_PHASE1_5.md](GO_NO_GO_PHASE1_5.md). Em resumo, a superfície é acessível, mas não suficientemente distintiva perante negativos humanos realistas; qualquer avanço deve ser apenas um piloto pequeno de negative design, não uma campanha ampla.

## Reprodutibilidade

Dependência Python:

```text
pip install -r requirements.txt
```

Auditoria Phase 1:

```text
python3 scripts/analyze_tcr_surface.py
python3 scripts/compare_natural_controls.py
python3 scripts/analyze_hotspot_chemistry.py
python3 scripts/analyze_interface_geometry.py
```

Phase 1.5:

```text
python3 scripts/build_phase1_5_panel.py
python3 scripts/analyze_phase1_5_negatives.py
```

Outputs principais:

- `data/phase1_5_negative_controls.csv`
- `data/provenance/tcr3d_alpha_records.json`
- `data/provenance/tcr3d_beta_records.json`
- `results/phase1_5/negative_control_comparison.csv`
- `results/phase1_5/negative_control_comparison.json`

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
