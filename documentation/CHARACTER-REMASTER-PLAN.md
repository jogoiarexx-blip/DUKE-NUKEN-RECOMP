# Duke Nukem: Time to Kill — Projeto de substituição dos personagens (P0)

Status: primeira etapa técnica implementada no fork. **Há validador de malhas GLB
e testes de contrato; ainda não há substituição de personagem no jogo.**
Este projeto prioriza a fidelidade das animações nativas, do gameplay e dos
figurinos. O piloto é Duke, grupo DB00, hierarquia 1.

## 1. Evidência do projeto original

O projeto já possui um pipeline de animação comprovado na documentação
[184-d08k1-animation-pipeline.md](184-d08k1-animation-pipeline.md).
O Duke do grupo DB00 tem **19 articulações** no arquivo HIE, com geometria
nos modelos MOD e poses nas tabelas ANM/FRM/ROT.

- HIE: cabeçalho de 0x44 bytes, registros de junta com 0x28 bytes, tabela
  de parte/ROT no cabeçalho +0x24. A árvore é determinada pela profundidade
  dos registros e os offsets entre juntas.
- MOD: malhas com vértices e polígonos; o Duke analisado usa polígonos
  texturizados do tipo 0x24 (triângulos) e 0x2c (quadriláteros).
- ANM: até 2048 registros de clipe por grupo.
- FRM: eventos, duração, primeiro comando e contagem.
- ROT: quaternions compactos de 14/13 bits e translação da raiz. O runtime
  interpola as poses e compõe as matrizes hierarquicamente.
- A lógica de animação é **independente do formato visual**; não precisamos
  substituir os clipes para mostrar novas malhas.

As quatro camadas de animação são: 0 = raiz/pernas, 1 = braço direito,
2 = braço esquerdo, 3 = peito/cabeça/acessórios. O método de composição
e os quatro canais constam na nota D08K1. Não devemos criar animações de
caminhada ou tiro como pré-requisito para um upgrade de polígonos.

O código [duke_model.inc](../recomp/src/ttk/duke_model.inc) confirma que o
Duke possui 19 juntas, mas **a ordem dos registros muda de figurino para
figurino**: o pescoço está na posição de registro 9 em alguns temas e em
15 no cenário de faroeste. Sempre mapear pelo ROT/part ID e verificar a
tabela reversa; jamais ligar uma malha por índice de registro.

## 2. Abordagem escolhida

**Rigid parts first:** exportar um GLB 2.0 com uma malha por parte rígida.
O novo modelo não pode conter clipes, skinning, morph targets nem uma
segunda animação. Cada malha fica no seu espaço local, com seu pivô na
origem da peça. As matrizes de cada articulação continuam vindo do PS1.

Fluxo planejado:

1. O jogo executa normalmente suas quatro camadas de animação.
2. O renderer verifica a identidade real do ator, do HIE carregado, o
   número de juntas, a parte e a geração do nível.
3. Para cada parte reconhecida, busca a nova malha GLB equivalente.
4. Aplica à malha a matriz **já calculada** para aquela parte pelo jogo.
5. Mantém attachments (arma, tiro, brilho, jetpack e itens) presos às
   mesmas juntas e renderiza colisões usando o caminho original.
6. Em qualquer erro, desconhecimento de variante, incompatibilidade
   ou sobrecarga, utiliza o modelo original daquele ator sem travar.

A camada de override deve ser apenas visual: não alterar HIE, ANM, FRM,
ROT, tabela de colisão, memória do jogo ou save state. O modo Vanilla
permanece sem alterações. O modo Remasterizado será opt-in no Modernized
com OpenGL/Polymorph, após testes.

**Estado real do fork:** os passos de validação em disco (3, antes de executar
o jogo) foram adicionados; os hooks de draw de 1-6 ainda não foram
integrados. Um GLB aprovado pelo validador ainda não aparecerá no jogo.

## 3. Contrato de 19 partes do piloto DB00

Rot ID -> nome do nó GLB. O grupo inicial tem HIE=1; o número à esquerda
é a identidade de animação, não a posição do registro na memória.

| ROT | Nome de nó (prefixo part_NN_) | Função |
| --- | --- | --- |
| 0 | pelvis | raiz |
| 9 | chest | peito |
| 10 | left_shoulder | ombro esquerdo |
| 11 | left_forearm | antebraço esquerdo |
| 12 | left_hand | mão esquerda |
| 13 | right_shoulder | ombro direito |
| 14 | right_forearm | antebraço direito |
| 15 | right_hand | mão/arma direita |
| 20 | jetpack_mount | acessório dorsal |
| 16 | head | cabeça/pescoço |
| 1,2,3,4 | leg_a_1 .. leg_a_4 | primeira cadeia de perna |
| 5,6,7,8 | leg_b_1 .. leg_b_4 | segunda cadeia de perna |
| 21 | leg_attachment | ponto adicional na perna |

A/B das pernas evita presumir esquerda/direita sem verificar o mapeamento
do figurino. O arquivo GLB terá exatamente os nomes literais, por exemplo
part_00_pelvis, part_09_chest e part_16_head.

**Requisito de rig:** os 19 nós devem existir, diretamente na cena
principal, sem translação/rotação/escala de objeto e sem hierarquia
redundante. Os vértices precisam estar em coordenadas locais já
centralizadas no pivô correto. Não confundir bone pose com object transform:
um arquivo com vértices em coordenadas de mundo seria desenhado deslocado.
Articulações exclusivamente de attachment podem não ter malha visível.

## 4. Manifesto de modelo

Arquivo particular model.json ao lado de duke.glb:

```json
{
  "schema": 1,
  "asset_id": "duke-db00-hero",
  "target": {"group": "DB00", "hierarchy": 1, "joints": 19},
  "model": {
    "file": "duke.glb",
    "sha256": "<SHA256 real de 64 caracteres hexadecimais>",
    "max_triangles": 12000
  },
  "rig": {
    "mode": "rigid-parts",
    "parts": {
      "0": "part_00_pelvis",
      "9": "part_09_chest",
      "10": "part_10_left_shoulder",
      "11": "part_11_left_forearm",
      "12": "part_12_left_hand",
      "13": "part_13_right_shoulder",
      "14": "part_14_right_forearm",
      "15": "part_15_right_hand",
      "20": "part_20_jetpack_mount",
      "16": "part_16_head",
      "1": "part_01_leg_a_1",
      "2": "part_02_leg_a_2",
      "3": "part_03_leg_a_3",
      "4": "part_04_leg_a_4",
      "5": "part_05_leg_b_1",
      "6": "part_06_leg_b_2",
      "7": "part_07_leg_b_3",
      "8": "part_08_leg_b_4",
      "21": "part_21_leg_attachment"
    }
  }
}
```

O SHA-256 será preenchido após a exportação do GLB. O validador verifica
a integridade exata; não baixa modelos da internet. O limite de 12 mil
triângulos é uma **meta experimental conservadora para o Duke herói**
e não uma medição de desempenho, nem um teto definitivo para inimigos.
A validação atual exige pelo menos dez nós com geometria; não afirma
que o modelo contém animações válidas no runtime.

## 5. Preparação e validação do modelo

1. Obtenha o seu próprio dump original americano SLUS-00583.
2. Use `recomp/tools/local/ttk_anim.py` e seu exportador Blender para
   inspecionar a pose e posições das juntas; os arquivos derivados do
   disco permanecem fora do GitHub.
3. Modele e pinte peças novas **originais** (não distribuídas a partir
   de pixels comerciais) em Blender. Mantenha pivôs e coordenadas locais.
4. Exporte **glTF Binary 2.0 (.glb)** com os nós do contrato; não exporte
   armature, skins ou animações duplicadas nesta primeira fase.
5. Gere o SHA-256 do GLB e preencha model.json.
6. Rode, na raiz:

   python recomp/tools/local/character_model.py /caminho/privado/model.json --json

O resultado informará número de juntas, peças desenhadas, triângulos
e se há hook ativo. Atualmente `runtime_override_active` é sempre
`false`: isso é intencional e impede apresentar validação de asset
como gameplay implementado.

O validador também recusa SHA inválido, modelo de outro tema, cenas sem
partes esperadas, transformações incompatíveis, arquivos externos,
animações duplicadas, modelos grandes demais e travessia de diretório.

## 6. Proposta visual dos personagens: imagens de produção

Cada personagem terá uma **prancha de turnaround** e um GLB final:

- **Referência:** frente, costas, lateral e ângulo 3/4, postura neutra,
  com silhueta fiel, lado a lado com captura original do próprio jogo.
- **T-pose de modelagem:** braços abertos e pernas afastadas o suficiente
  para inspeção, mas o arquivo de runtime terá cada peça no espaço do
  pivô original, e não a T-pose como animação ativa.
- **Wireframe:** quadriláteros bem distribuídos no rosto e nas articulações;
  evita malha hiper-densa e preserva o estilo PS1/PS2.
- **Textura atlas:** pintura em 512² ou 1024² como meta inicial, com
  detalhes de tecido, botas, cinto, pele e óculos sem excesso de brilho.
- **Preview animado:** idle, corrida, salto, tiro, recarga, dano, morte,
  agachamento e interações com portas, escadas e armas.
- **Antes/depois de gameplay:** mesmo cenário, mesmo movimento, câmera,
  pose, iluminação e taxa de apresentação.

**Direção artística recomendada para Duke:** musculatura e silhueta de
herói de ação dos anos 1990, cabelo loiro, óculos escuros, rosto/mandíbula
mais nítidos, mãos arredondadas, roupa e botas mais bem definidas,
proporções e vestuário preservados. Aumentar a qualidade sem adotar
realismo fotográfico que destoaria das paredes e inimigos do jogo.

É preciso extrair referências dos próprios figurinos do jogo: não usar
a roupa de DB00 como prova de que os figurinos de faroeste, medieval e
outros grupos compartilham a mesma geometria. Cada tema será tratado
como variante identificada.

## 7. LOD, materiais e custos

Valores iniciais de projeto, a validar na GPU e nas cenas reais:

| Categoria | LOD0 aproximado | LOD1 aproximado | LOD2 |
| --- | --- | --- | --- |
| Duke | 8-12 mil triângulos | 3-5 mil | original PS1 |
| Inimigo humano | 2-5 mil | 800-1800 | original PS1 |
| Boss | 6-15 mil | 2-5 mil | original PS1 |

Esses valores são orçamentos propostos, não contagens medidas dos modelos
originais. Para vários inimigos simultâneos, impor **orçamento total de
triângulos, draw calls e texturas visíveis** antes de ativar LOD0.
Evitar sobrecarregar o renderer com 20 cópias do herói.

Materiais de primeira entrega: albedo customizado, iluminação do Polymorph,
alpha/cutout compatível, sem PBR ou normal map obrigatório. Técnicas
avançadas e sombras dependem de protótipo posterior.

## 8. Plano de implementação no renderer

P0 (concluído em código no fork): esquema de manifesto GLB, hash,
19 IDs ROT, validação estrutural, limite de triângulos e testes sintéticos.

P1: **integração do renderer ainda pendente**. Auditar
`recomp/src/ttk/near_clip.cpp:object`,
`recomp/src/ttk/duke_model.inc` e os hooks de desenho de actor/joint.
Mapear modelo ativo, geração do nível, part ID, matriz da junta, geometria
e tpage da peça. Fazer captura diagnóstica da hierarquia com o disco
original antes de esconder qualquer geometria de PS1.

P2: substituir uma única peça inicialmente (por exemplo a mão ou o
torso) com um primitivo sintético, preservando original nas demais.
Testar transformação, espelhamento, clipping e câmera.

P3: modelo Duke completo, upload do GLB em host memory/GPU, buffers,
materiais simples, cache e invalidação no load/unload. Rejeitar
hashes/identidades incompatíveis e restaurar tudo após device reset.

P4: adaptar **um figurino de cada vez**, depois inimigos e chefes.
Nenhuma variante deve assumir que registro 9 representa sempre pescoço.

P5: orçamento por LOD, integração com opções Remastered, comparação
objetiva com frames originais, compatibilidade entre 60/120/180
apresentações e save/load, teste em Windows e Linux.

## 9. Critérios de aceitação para afirmar que funciona

- Todas as 19 juntas mapeadas no grupo DB00 e em poses diferentes.
- Idle, caminhar/correr, girar, pular, atirar, agachar, sofrer dano,
  morrer, trocar de arma, salvar/carregar e mudança de área.
- Posição da mão e da arma inalterada; muzzle flash preso no mesmo ponto.
- Head hiding, primeira e terceira pessoa, espelho, jetpack, transparência
  e cutscene testados.
- Velocidade do jogo, colisão, inimigos, hitbox e inventário iguais.
- Vanilla visualmente idêntico ao baseline.
- Quando faltam arquivos, GLB está inválido ou nível muda, o original
  volta sem falha ou vestígio de buffers.
- Captura de frame real com Duke remasterizado e comparativo antes/depois.
- FPS, picos de draw calls, RAM/VRAM e regressões nos saves anotados.

O teste do validador **não** é substituto para esses ensaios visuais.
As imagens do turnaround e os próprios modelos artísticos ainda
precisam ser criados; este documento define exatamente como produzi-los.

## 10. Referências e limites

- [D08K1 — animação e formato HIE/MOD/ANM/FRM/ROT](184-d08k1-animation-pipeline.md)
- [D36 — primeira pessoa, armas e ownership das partes](257-d36-first-person-presentation-audit.md)
- [D08A28 — estética aceita da Bio Mask](265-native-mesh-art-style.md)
- [D17BA — limites do culling de modelos](366-d17ba-open-models.md)
- Código do mapeamento de Duke: `recomp/src/ttk/duke_model.inc`.
- Validador: `recomp/tools/local/character_model.py`.
- Testes sintéticos: `recomp/tests/local/test_character_model.py`.

Documentação e validação independem de arquivos comerciais. Não foi
concluída a substituição de malha em tempo real ou a certificação do
Duke remasterizado no jogo nesta etapa.
