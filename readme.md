# Clips Processing for Computer Vision Pipelines

Este projeto tem como objetivo auxiliar no **recorte e divisão de vídeos** em conjuntos de frames/imagens úteis para pipelines de **visão computacional**. Ele automatiza a identificação de trechos com movimento relevante utilizando diferenças entre frames consecutivos, permite a revisão humana e o refinamento desses trechos por meio de uma interface interativa, e exporta os frames recortados e enquadrados.

---

## Estrutura do Projeto e Fluxo de Execução

O pipeline é composto por quatro etapas principais, que podem ser executadas de forma orquestrada (tudo junto) ou individualmente (passo a passo).

Ao processar um vídeo (ex: `clips/video.mp4`), o projeto cria uma pasta com os arquivos intermediários e resultados em `clips/video_processed/`.

---

## Como Executar

### 1. Fluxo Completo (Orquestrado)

Para executar todo o fluxo de uma vez, utilize o script principal:
```bash
uv run process_clip.py .\clips\seu_video.mp4
```
Este script executará o processamento de movimento, gerará os intervalos (ranges), perguntará se deseja iniciar a validação interativa e, caso concluído com sucesso, perguntará se deseja salvar os frames finais.

### 2. Execução das Etapas Separadamente

Se preferir rodar cada script individualmente para fins de depuração ou refazer uma etapa específica:

#### Passo A: Extração de Movimento
Mapeia o movimento ao longo do vídeo calculando as diferenças de pixel dentro de uma máscara de seleção poligonal.
```bash
uv run process_movement.py .\clips\seu_video.mp4
```
* **O que faz:** Abre uma janela para você clicar e selecionar um polígono da área de interesse (crop). Em seguida, salva os pontos em `points.pkl`, os dados de movimento em `movement.pkl` e as propriedades do vídeo em `cap_data.pkl`.

#### Passo B: Processamento e Segmentação de Ranges
Segmenta os pontos de movimento contínuo acima do limiar configurado.
```bash
uv run process_ranges.py .\clips\seu_video_processed\movement.pkl
```
* **O que faz:** Agrupa os trechos de movimento, gera o gráfico `movement.png` com as marcações dos limiares e salva os intervalos sugeridos em `ranges.pkl`.

#### Passo C: Validação Manual dos Ranges
Abre a interface interativa OpenCV para você analisar e aprovar/recortar as sequências.
```bash
uv run validate_ranges.py .\clips\seu_video.mp4
```
* **O que faz:** Permite navegar pelos intervalos propostos, recortá-los e aprová-los/rejeitá-los. Salva o progresso em `video_review_progress.json`.

#### Passo D: Salvando os Frames Recortados
Exporta os trechos aprovados e recortados (crop bounding box) como imagens JPG.
```bash
uv run save_frames.py .\clips\seu_video.mp4
```
* **O que faz:** Cria a pasta `frames/` e salva cada quadro relevante como `.jpg`, limitando a área de imagem ao retângulo delimitador do polígono selecionado.

---

## Controles da Validação Interativa

A interface de validação (`validate_ranges.py`) foi desenhada para ser rápida e intuitiva, operada **apenas usando a barra de espaço e as setas do teclado**:

* **Setas Esquerda / Direita (← / →):**
  - Pausam a reprodução automática, entram no **Modo Manual** e avançam/retrocedem o vídeo quadro a quadro.
* **Espaço:**
  - Alterna o modo de visualização entre **Modo Auto** (reprodução contínua e looping do range) e **Modo Manual** (pausa para análise detalhada).
* **Seta para CIMA (↑):**
  - **No Modo Auto (looping):** Valida e aprova o intervalo inteiro atual, avançando para o próximo.
  - **No Modo Manual:** Valida e aprova o intervalo do *início do range até o frame atual*. O restante do range vira um novo trecho e a visualização volta automaticamente para o **Modo Auto**.
* **Seta para BAIXO (↓):**
  - **No Modo Auto (looping):** Ignora e descarta o intervalo inteiro atual, avançando para o próximo.
  - **No Modo Manual:** Descarta o intervalo do *início do range até o frame atual*. O restante do range vira um novo trecho e a visualização volta automaticamente para o **Modo Auto**.
* **ESC:**
  - Salva o progresso atual no arquivo `video_review_progress.json` e encerra o programa antecipadamente.

---

## Configurações (`options.json`)

Edite o arquivo `options.json` para ajustar o comportamento da extração e segmentação de movimento:

### Processamento:
* `"skip_frames"`: Quantidade de frames pulados durante a extração de movimento para acelerar o processamento.
* `"low_threshold"`: Limiar de movimento mínimo para que o frame seja considerado ativo (normalizado com base na área da máscara de seleção).
* `"high_threshold"` (opcional): Limiar máximo de movimento considerado válido. Se for `null` ou omitido, nenhum limite superior é aplicado.
* `"skip_frames_save"`: Quantidade de frames pulados ao gerar os arquivos de imagem finais em `save_frames.py` (ex: salvar a cada 5 frames).

### Plot & Visualização:
* `"jump_seconds"`: Define o intervalo em segundos entre os marcadores do eixo X no plot `movement.png`.
* `"y_limit"`: Define o limite vertical do plot gráfico (ex: `[0, 100]`), ou vazio `[]` para escala automática.
* `"change_point_threshold"` e `"window_size"`: Parâmetros herdados da detecção antiga de pontos de mudança de média móvel (opcionais com a nova lógica de limiares).