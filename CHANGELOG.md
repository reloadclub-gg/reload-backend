# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Checa alteração no CHANGELOG.md no workflow do GitHub (#251).
- Envia WS para lobbies quando encontra partida (#236).
- Novo modelo Matches no banco (#241).
- Cria os esquemas JSON do modelo de Partida.
- Envia WS para usuários da partida informando que partida está em configuração (#246).

### Changed

- Altera modelo de Matches removendo senha e modificando tipo de campo de game_type para refletir lógica do model Lobby.

## [f6c6b3e - 06/03/2023]

### Added

- Tarefa para encontrar times oponentes a partir de times prontos (https://github.com/3C-gg/reload-backend/pull/239)
- Sistema de pré-partida para que usuários confirmem que estão prontos antes de iniciar a partida (https://github.com/3C-gg/reload-backend/pull/240 e https://github.com/3C-gg/reload-backend/pull/247)
- Endpoint que recebe o lock in dos jogadores na partida (https://github.com/3C-gg/reload-backend/pull/248)
- Endpoint que recebe o ready dos jogadores na partida (https://github.com/3C-gg/reload-backend/pull/249)

## [a88d544 - 23/02/2023]

### Added

- Página do admin para renderizar templates de e-mails

### Fixed

- Imagem de fundo do e-mail de inativação do usuário com link quebrado
