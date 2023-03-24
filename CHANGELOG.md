# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Novo arquivo `tasks` no package de websocket que expõe as tarefas como middleware para que o código possa chamar os eventos WS tanto como tarefas quanto como métodos normais dependendo do caso.
- Serviço do _Celery_ no _Kubernetes_.
- Serviço do _Celery_ no Github Workflow (https://github.com/3C-gg/reload-backend/issues/317).

### Fixed

- Código de verificação de e-mail estava _hardcoded_ no template de e-mail. Substituímos pelo código certo, individual e único para cada usuário (https://github.com/3C-gg/reload-backend/issues/299).
- Em um caso específico, onde tinham 2 players em um lobby e o player convidado (que não é o dono) sai ou é expulso, o dono do lobby não estava tendo seu status de "Em grupo" para "Online" atualizado para seus amigos. Uma vez que ele estava em grupo, e com a saída do convidado ele ficou num lobby vazio, começamos a disparar esse evento para o dono do lobby (https://github.com/3C-gg/reload-backend/issues/301).
- Ajusta string de conexão do Celery com o Redis quando a conexão for via SSL.

### Changed

- Atualiza bilbioteca redis-py para última release.
- Altera manifestos do k8s para usar Ingress e Nginx ao invés do webserver padrão do Django (https://github.com/3C-gg/reload-backend/issues/304).
- Altera alguns termos "gta-mm" pra "reload".
- Controllers de API passam a enviar chamadas de WS em segundo plano usando tarefas do _Celery_ (https://github.com/3C-gg/reload-backend/issues/310).
- Celery agora está configuração `CELERY_ALWAYS_EAGER` ligada para testes.

### Removed

- Django Jazzmin foi removido devido a falta de suporte na renderização de ícones e imagens, o que tornava a utilização do admin mais difícil (https://github.com/3C-gg/reload-backend/issues/303).
- Removido level debug da lib Sentry.

## [023c3eb - 19/03/2023]

### Added

- Checa alteração no CHANGELOG.md no workflow do GitHub (https://github.com/3C-gg/reload-backend/issues/251).
- Envia WS para lobbies quando encontra partida (https://github.com/3C-gg/reload-backend/issues/236).
- Novo modelo Matches no banco (https://github.com/3C-gg/reload-backend/issues/241).
- Cria os esquemas JSON do modelo de Partida.
- Envia WS para usuários da partida informando que partida está em configuração (https://github.com/3C-gg/reload-backend/issues/246).
- Evento match_cancel (ws_matchCanceled) no controller de websocket.
- Método estático `delete` para o model PreMatch.
- Tarefa que cancela partida, deletando ela do Redis, caso `countdown` para que fique pronta chegue ao final sem que todos os players se marquem como prontos e envia chamada WS para usuários da partida informando que partida foi cancelada (https://github.com/3C-gg/reload-backend/issues/257).
- Chamada para tarefa que cancela partida ao iniciar `countdown`.
- Novo settings para quantidade mínima de players para que o time seja considerado pronto (`ready`).
- Schema de Pré Partida (`PreMatch`) para ser enviado ao encontrar uma partida.
- Chamada WS quando houver atualização na Pre Partida (https://github.com/3C-gg/reload-backend/issues/265).
- Adiciona 2 novos eventos ao controller de websocket: `match_cancel_warn` que envia um pedido ao client para notificar o lobby em que algum player não aceitou a partida e `restart_queue` que avisa ao client que pode re-startar a queue caso todos os players de um lobby tenham aceitado a partida (https://github.com/3C-gg/reload-backend/issues/263).
- Adiciona 2 métodos de apoio ao model `PreMatch`: `get_all` e `get_by_player_id`.
- Adiciona o campo `pre_match` ao esquema `AccountSchema`.
- Adiciona campo `user_ready` no `pre_match` em `AccountSchema` (https://github.com/3C-gg/reload-backend/issues/279).
- Envia WS de atualização de usuário ao cancelar ou iniciar uma pré partida (https://github.com/3C-gg/reload-backend/issues/283).
- Endpoints `match_player_lock_in` e `match_player_ready` agora passam a retornar `PreMatchSchema` (https://github.com/3C-gg/reload-backend/issues/286).
- Para que o client consiga redirecionar os usuários para o perfil da Steam de outros usuários, adicionamos o campo `steam_url` nos esquemas: `AccountSchema`, `LobbyPlayerSchema` e `FriendAccountSchema`. Esse campo representa o campo `profileurl` da API da Steam (https://github.com/3C-gg/reload-backend/issues/261).
- Controller de mover jogadores, para que não tenhamos que fazer um `leave` e um `enter` (https://github.com/3C-gg/reload-backend/issues/295).

### Changed

- Altera modelo de Matches removendo senha e modificando tipo de campo de game_type para refletir lógica do model Lobby.
- Propriedade `state` de PreMatch agora retorna `canceled` para pre partidas que não ficam prontas até que o `countdown` acabe.
- Altera chamada WS de match_found para pre_match. (https://github.com/3C-gg/reload-backend/issues/262)
- Altera forma como modelo de PreMatch guarda os players marcados como `ready` (https://github.com/3C-gg/reload-backend/issues/267).
- JSON de PreMatch agora é retornado com uma nova propriedade `user_ready` para indicar se o usuário autenticado foi marcado como `ready` (https://github.com/3C-gg/reload-backend/issues/270).
- Altera maneira de detecção de grupos de envio do WS para o evento `pre_match`.
- Altera namespace do parâmetro `match_id` nos controllers de match pre_match.
- Método `match_cancel` do controller de websocket agora recebe `pre_match` como parâmetro.
- Tarefa `cancel_match_after_countdown` que cancela a partida depois que acaba o countdown para que os players fiquem prontos agora faz um fetch dos times antes, quando eles são requisitados pela primeira vez.
- Settings de countdown de pré partida (`MATCH_READY_COUNTDOWN`) agora tem valor diferente quando está em `TEST_MODE`.
- Aumenta tempo de gap de countdown para ficar pronto na pré partida (`MATCH_READY_COUNTDOWN_GAP`): 2 -> 4.

### Fixed

- Campo `user_ready` estava enviando informaçãono WS relativa ao jogador recebido pela chamada da API fazendo com que o client não carregasse corretamente os jogadores que estavam prontos. Corrigimos para que esse campo carregue uma informação diferente para cada jogador da partida (https://github.com/3C-gg/reload-backend/issues/273).
- Evento WS de `pre_match` estava sendo chamado somente quando todos os players se marcavam como `ready`. Corrigimos para que o evento seja disparado a cada `ready` de player (https://github.com/3C-gg/reload-backend/issues/277).
- Método `players_ready` do model `PreMatch` estava retornando players que ficaram prontos somente no estado `lock_in`. Corrigimos para que esse método passe a retornar os players mesmo quando não estiver nesse estado (https://github.com/3C-gg/reload-backend/issues/282).
- Campo `level` do `LobbyPlayerSchema` que estava retornando uma _string_ quando na verdade deveria retornar um _integer_.
- Processo de aceitar convites que estava apenas lidando com o método do model `Lobby` quando. Mas para o funcionamento ideal, precisamos seguir o processo de sair do lobby atual e entrar em um novo, disparando os devidos eventos websockets e tratando da maneira correta, tanto a saída quanto a entrada (https://github.com/3C-gg/reload-backend/issues/289).
- Algumas situações onde não era disparado evento websocket para o client para atualizar a lista de convite ou o status dos usuários, tanto logado quanto do lobby, fazendo com que alguns status ficassem defasados e alguns convites fantasmas aparecessem (https://github.com/3C-gg/reload-backend/issues/290).
- Lobby cheio não permitia que dono saísse, pois a saída move ele pra um novo lobby, que é o mesmo do qual ele saiu. Adicionamos uma checagem para garantir que nesse caso específico, a verificação de lobby cheio não seja interpretada (https://github.com/3C-gg/reload-backend/issues/293).

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
