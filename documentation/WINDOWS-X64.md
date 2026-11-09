# Preparacao Windows x64 — sem distribuicao do jogo

Este espelho acompanha o codigo-fonte do projeto de recompilacao nativa
[Duke Nukem: Time to Kill](https://github.com/MusicMonsterMod/duke-nukem-time-to-kill-recomp).

## O que a verificacao automatica cobre

A rotina [Windows x64 - recompiladores](../.github/workflows/windows-source-smoke.yml)
usa um runner Windows com Visual Studio 2022, restaura os submodulos fixados
e aplica os patches locais. Compila **sem arquivos comerciais**:

- `sector_check.exe` — ferramenta de verificacao do disco;
- `psxrecomp-game.exe` — recompiler PS1 para C;
- `psxrecomp-bios.exe` — emissor da BIOS.

Se a compilacao passar, o artefato das ferramentas aparecera em **Actions**.
Esses executaveis sao ferramentas de desenvolvimento e **nao sao o jogo**.

## O que continua necessario para um EXE jogavel

- Um dump proprio do disco americano `SLUS-00583`, colocado em `game/`
  e validado pela ferramenta de importacao (nao incluir no GitHub);
- Configurar dependencias graficas SDL3/OpenGL e a cadeia de compilacao
  nativa Windows x64;
- Executar a geracao do codigo do jogo e o build completo;
- Validar abertura do jogo, controles, audio, saves e estabilidade em
  Windows real.

**Nao confunda CI de ferramentas com certificacao do EXE do jogo**.
Os requisitos, limites e passos originais permanecem documentados em
[Build and run](04-build-and-run.md). GitHub Pages mostra a pagina de
projeto, mas nao executa diretamente um EXE Windows.
