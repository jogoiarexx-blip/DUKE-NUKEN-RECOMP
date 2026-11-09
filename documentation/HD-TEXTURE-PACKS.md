# Pacotes HD — primeira integração no recompilador

O projeto D16 original só selecionava uma amostra de textura de cada vez.
Agora a versão do fork pode carregar até 8 amostras em uma sessão Modernized
com OpenGL, sem alterar os dados do disco nem a gravação de jogo.

## Recursos

- Entrada TTKPACK1, com nomes locais de arquivos TTKTX01.
- Cada textura é validada contra página PS1, profundidade, paleta e bytes
  reais da região na VRAM antes de aplicar a substituição.
- Ao trocar pixels, CLUT, região, savestate ou estado de renderização,
  a validação anterior é descartada e feita novamente quando necessário.
- Texturas ausentes, incompatíveis ou com arquivo inválido são ignoradas,
  mantendo a aparência original.
- O modo Vanilla e a renderização por software não carregam esses pacotes.

## Como usar

1. Utilize seu próprio disco original americano SLUS-00583.
2. Com o executável funcional, capture a área usando a ferramenta D16:
   recomp/tools/local/texture_sample.py capture
   (consulte documentation/278-d16-texture-foundation.md).
3. Crie pinturas melhoradas em PNG RGB sem transparência, com ampliação
   inteira uniforme do tamanho da textura original e no máximo 1024×1024.
4. Crie um arquivo JSON particular com o formato:

    {
      "schema": 1,
      "entries": [
        {"id":"parede_clube","capture":"capturas/clube/capture.json","image":"arte/parede_clube.png"},
        {"id":"piso_rua","capture":"capturas/rua/capture.json","image":"arte/piso_rua.png"}
      ]
    }

5. Gere o pacote (a partir da raiz do repositório):

    python recomp/tools/local/texture_pack.py /diretorio-privado/pack.json /diretorio-privado/pack-compilado

6. Execute, com o jogo já compilado:

    python recomp/tools/local/run.py --texture-pack /diretorio-privado/pack-compilado/pack.ttkpack

O caminho de pacote vale somente para esta inicialização. Não precisa
substituir texturas ou extrair novamente o jogo no GitHub.

## Limitações e proteção

- Limite inicial: oito texturas por pacote.
- Apenas um candidato por combinação de página, profundidade e CLUT.
  Várias regiões no mesmo estado de textura ainda precisam de seleção por UV.
- Ainda não existe um catálogo automático de todas as fases nem arte HD
  pronta; o sistema recebe pinturas que você fornecer.
- Esta integração teve testes com amostras sintéticas e teste de aplicação
  do patch; não houve teste visual no jogo completo nesta sessão.
- Nunca publique arquivos compilados TTKTX01, capturas, paletas, VRAM ou
  trechos de disco; eles podem conter material derivado do jogo comercial.
- Os pacotes compilados são ignorados pelo Git; mantenha capturas e arte
  particulares fora do repositório também.

## Próximas melhorias

P1: seleção por UV permitindo várias texturas dentro da mesma página e
CLUT, sem sobreposição de desenhos. P2: catálogo com IDs por fase e
captura assistida. P3: substituir texturas em paredes, pisos, armas e
personagens com regressão em saves, transparência, 60/120/180 FPS e memória.
P4: modelos 3D aprimorados e sombras cuidadosamente testadas.
