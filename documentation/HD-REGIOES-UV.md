# Regiões HD em uma única página de VRAM (P1)

Atualização incremental do carregador TTKPACK1. Antes, a mesma página/profundidade
e CLUT só podia aparecer uma vez; agora aceita até oito regiões UV que não se
sobrepõem, como parede, piso ou placas presentes no mesmo atlas do PS1.

## Segurança da seleção

1. O empacotador Python rejeita retângulos UV conflitantes com a mesma
   combinação de página, profundidade e CLUT. Regiões adjacentes são válidas.
2. O leitor C valida novamente a mesma regra, inclusive para pacotes gerados
   por terceiros, sem confiar apenas na ferramenta Python.
3. O renderer compara a página, profundidade, CLUT **e o intervalo completo
   das coordenadas UV dos três vértices**. Só ativa uma imagem HD quando
   todos os vértices estão dentro da região selecionada.
4. Triângulos que atravessam duas regiões, ou usam wrapping/texture window,
   permanecem com a textura original. Esse comportamento evita trocas erradas
   e preserva a lógica de blending, paleta e transparência do PlayStation.
5. A verificação D16 da VRAM e CLUT continua sendo obrigatória e é invalidada
   com upload, alteração de paleta, troca de estado e savestate.

## Exemplo de captura

Para dois atlas adjacentes na mesma página e paleta, capture regiões
u=0..39 e u=40..79 (em 4bpp, w deve ser múltiplo de 4). Ambas poderão
estar no mesmo arquivo JSON, com nomes de entrada diferentes. Não faça
pacotes que sobreponham pixels da região original.

O sistema conserva o limite de oito texturas, não gera pinturas automaticamente
e não inclui arquivos do disco no repositório.

## Testes

O arquivo `recomp/tests/local/test_texture_pack.py` testa duas regiões
adjacentes, rejeição de sobreposição, paletas distintas, integridade dos
dados originais e carregamento C do pacote com o mesmo atlas.

## Pendente antes da certificação gráfica

A substituição visual nas fases precisa ser testada no executável compilado a
partir de uma cópia própria USA SLUS-00583. Ainda não há texturas HD completas
para paredes e pisos da primeira fase, catálogo automático ou comparação real
de FPS/VRAM. A primeira fase é a próxima candidata para capturar superfícies
e comparar os perfis visuais.
