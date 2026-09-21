# Projeto: Espondiloartrite / AS4.2 TCR

## Objetivo ativo

Executar um piloto computacional mínimo e pré-registado de *negative design* para testar se é possível desenhar um binder de novo que reconheça seletivamente o TCR AS4.2, com foco no motivo CDR3β `VGLFSTDTQ`, distinguindo-o dos TCRs humanos estruturalmente mais semelhantes.

Estado atual: **Phase 1 e Phase 1.5 completas; NO-GO para uma campanha ampla de geração de binders.** Os controlos humanos realistas revelaram miméticos estruturais difíceis: 7N2S (`VGLYSTDTQ`), 8CX4 (`VGTYSTDTQ`) e 9PBG/9PBH (`PATYSTDTQ`). Ver [PHASE1_5_REPORT.md](PHASE1_5_REPORT.md) e [GO_NO_GO_PHASE1_5.md](GO_NO_GO_PHASE1_5.md).

O piloto mínimo está pré-registado e congelado em [PILOT_DESIGN_SPEC.md](PILOT_DESIGN_SPEC.md), com quatro backbones RFD3, três sequências ProteinMPNN por backbone e um máximo de 12 candidatos científicos. O objetivo não é maximizar afinidade prevista isoladamente, mas procurar separação de AS4.2 face aos negativos e contrafactuais obrigatórios por uma margem superior à incerteza do método.

Os outputs RFD3/ProteinMPNN/RF3 produzidos localmente foram **apenas smoke tests do pipeline**. Estão excluídos do ranking científico e da decisão GO/NO-GO; os três designs locais falharam os filtros pré-registados e não são candidatos a binder.

O próximo passo de execução é exclusivamente o **Stage 0 numa GPU cloud**, após autorização explícita do utilizador. O Stage 0 valida CUDA, checkpoints, inputs, ambiente e reprodutibilidade com um único backbone descartável e termina sem iniciar o piloto científico. O plano e o comando de execução estão em [CLOUD_RUN_PLAN.md](CLOUD_RUN_PLAN.md) e [PRE_CLOUD_AUDIT.md](PRE_CLOUD_AUDIT.md). Nenhum recurso cloud pago foi lançado durante a preparação ou auditoria.

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

O repositório, os inputs, os manifests e as análises leves permanecem locais. Não é necessário contratar armazenamento cloud permanente para o piloto. Um host com 64 GiB de RAM é permitido apenas para o Stage 0 de calibração, que exige pelo menos 60 GiB visíveis e é marcado `CALIBRATION_ONLY`; os Stage 1–3 mantêm a exigência de pelo menos 96 GiB de RAM, GPU NVIDIA ≥80 GB VRAM e 40 GB de disco livre.

Esta distinção operacional não altera seeds, thresholds, candidate caps ou critérios GO/NO-GO.

O Stage 0 é o único passo atualmente preparado para execução. Não existe transição automática para Stage 1: os seus logs e outputs têm de ser inspecionados por uma pessoa antes de qualquer nova autorização. GPUs deixadas ativas depois do teste continuam a ser o principal risco de custo.
