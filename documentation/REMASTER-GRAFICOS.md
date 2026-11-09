# Duke Nukem: Time to Kill — Remaster gráfico (etapa 1)

O repositório original já possui correção de geometria, precisão de textura,
resolução interna até 4×, renderização Polymorph, visão 16:9, distância ampliada
e iluminação dinâmica. Nossa primeira etapa organiza essas opções em três
perfis **opt-in**. O jogo padrão não é alterado até o usuário escolher um perfil.

## Perfis de qualidade

| Opção | Original | Equilibrado | Remasterizado |
| --- | --- | --- | --- |
| Nome do perfil | original | balanced | remastered |
| Resolução interna | 1× | 2× | 4× |
| FPS apresentados | 60 | 60 | Auto (até o limite suportado) |
| Widescreen | Desligado | 16:9 | 16:9 |
| Geometria | Original | Corrigida | Corrigida |
| Texturas/perspectiva | Original | Corrigida | Corrigida |
| Renderer de mundo | Classic | Polymorph | Polymorph |
| Distância de desenho | Original | Ampliada | Ampliada |
| Luzes dinâmicas | Desligadas | Ligadas | Ligadas |
| Filtro de apresentação | Nearest | Nearest | Linear |

A escolha modifica somente opções visuais do Modernized, sem tocar em
controles, som, saves, inventário ou em Vanilla. Ela respeita preferências
explícitas posteriores, permitindo reduzir qualidade sem perder as demais
melhorias.

## Como ativar

Execute uma vez na raiz do repositório (Windows: usar py ou python):

    python3 recomp/tools/local/run.py --graphics-preset remastered --show-settings

O comando salva as preferências e termina sem lançar o jogo. Depois use:

    python3 recomp/tools/local/run.py

Alternativas:

    python3 recomp/tools/local/run.py --graphics-preset balanced --show-settings
    python3 recomp/tools/local/run.py --graphics-preset original --show-settings

Se o computador não alcançar a taxa desejada:

    python3 recomp/tools/local/run.py --graphics-preset remastered --internal-scale 2 --frame-rate 60 --show-settings

O modo Vanilla original continua acessível por --vanilla. O parâmetro
--graphics-preset só funciona no Modernized.

## O que isto AINDA não significa

- Não instalamos texturas de alta resolução para o jogo inteiro.
- Nenhum modelo comercial foi substituído nem extraído para o repositório.
- Nenhuma nova sombra, ray tracing, efeito de pós-processamento ou PBR foi
  implementado nesta etapa.
- A recompilação completa para Windows e a campanha completa continuam sem
  certificação. A melhoria requer um build do jogo com a própria cópia americana
  do disco SLUS-00583 para validação visual dentro das fases.

## Roteiro de remasterização real

1. **P0 — comparativos com o executável jogável:** capturar pontos idênticos
   em Original, Equilibrado e Remasterizado; medir FPS, GPU, memória, geometria,
   áudio e transições de fases.
2. **P1 — sistema generalizado de texturas HD:** estender o teste D16 de uma
   parede para pacotes opcionais por região e identidade do conteúdo/CLUT
   originais. Invalidar caches na VRAM, troca de nível, savestate e FMV.
   Preservar fallback original quando uma substituição não corresponder.
3. **P2 — iluminar com cuidado:** expandir luzes D41 com teto de custo por
   fragmento, configuração de intensidade e sombras apenas onde testadas.
4. **P3 — objetos e modelos:** criar substituições estilizadas compatíveis com
   o projeto, preservando animações, colisões e identidade visual PS1.
5. **P4 — regressão:** testes em 60/120/180 FPS, comparações de transparência,
   névoa, água, céu e áudio; nunca afirmar campanha completa por teste parcial.

### Referências originais

- [D15 — geometria e perspectiva](96-d15-accepted-precision.md)
- [D16 — prova inicial de substituição de textura](278-d16-texture-foundation.md)
- [D17 — qualidade em altas frequências](86-d17-acceptance-and-regression-baseline.md)
- [D41 — iluminação](413-d41-lighting-case-study.md)
