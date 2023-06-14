# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Chamadas websocket sempre que houver alterações no lobby (queue, etc) [#439](https://github.com/3C-gg/reload-backend/issues/439).
- Chamadas websocket sempre que houver alterações na lista de jogadores de um lobby [#434](https://github.com/3C-gg/reload-backend/issues/434).

### Changed

- Websocket `ws_friend_update` agora receber objeto `User` ao invés de `user_id: int`.

## [848718f - 12/6/2023]

### Added

- Endpoint para coletar assuntos de tickets válidos: `GET /support/tickets/subjects/` [#427](https://github.com/3C-gg/reload-backend/issues/427).
- Endpoint para criação de tickets no Freshdesk via e-mail: `POST /support/tickets/` [#427](https://github.com/3C-gg/reload-backend/issues/427).
- Config `SUPPORT_EMAIL` para gravar e-mail de suporte para onde serão enviados solicitações de suporte.
- Endpoint de criação de convite [#425](https://github.com/3C-gg/reload-backend/issues/425).
- Arquivos relacionados a envio de websocket em seus respectivos pacotes (`friends`, `lobbies` e `notifications`).

### Changed

- Client api de teste passa a receber campo `content_type` para alterar o tipo da solicitação quando necessário.
- Client api de teste passa a receber campo `**extra` para receber headers customizados.
- Alteramos alguns endpoints relacionados ao `Lobby`.
- Movemos toda parte de lobbies que ficavam em `matchmaking` para seu pacote exclusivo `lobbies`.

### Fixed

- O endpoint de logout retornava o usuário, e isso demorava muito, pois ia na Steam pegar todos os amigos, etc. Consertamos para que o endpoint `/accounts/logout/` retorne apenas um objeto (`{detail: "ok"}`) já que o client não vai mais usar o objeto do usuário para nenhuma ação, uma vez que o usuário solicitou o logout [#422](https://github.com/3C-gg/reload-backend/issues/422).

## [9cd6628 - 5-6-2023]

## [ae47465 - 29-5-2023]

### Added

- Campos de estatísticas no esquema `MatchPlayerStatsSchema` [#412](https://github.com/3C-gg/reload-backend/issues/412)
- Endpoints para a aplicação de perfis (`Profiles`) [#406](https://github.com/3C-gg/reload-backend/issues/406).
- Rotina que decrementa o nível dos usuários após um período de inatividade [#389](https://github.com/3C-gg/reload-backend/issues/389).
- API `Friends` para endpoints relativos a amigos [#402](https://github.com/3C-gg/reload-backend/issues/402).
- Método `check_friendship` para testar se duas contas são amigas na Steam.
- Rotas de API de Notificações [#378](https://github.com/3C-gg/reload-backend/issues/378).
- Campos `latest_matches_results` e `last_results` nos esquemas `FriendAccountSchema` e `AccountSchema` [#395](https://github.com/3C-gg/reload-backend/issues/395).
- Esquema `MatchPlayerProgressSchema` para enviar o progresso do jogador em uma partida [#393](https://github.com/3C-gg/reload-backend/issues/393).
- Método `calc_level_and_points` para calcular nível e pontos de nível a ganhar separado do modelo `Account`.

### Changed

- Chamada para aplicar os pontos ganhos dos players na finalização de uma partida. Alteramos o método chamado para refletir o novo método `calc_level_and_points`.

### Removed

- Migrations antigas devido ao novo campo `username` adicionado no modelo `Accounts`.
- Método `set_level_points` que possuía uma lógica muito grande e complicada, misturando cálculos e operações de banco de dados no mesmo método.

## [25a9fb5 - 8-5-2023]

### Added

- Endpoint de listagem de partidas de um usuário (https://github.com/3C-gg/reload-backend/issues/388).
- Adiciona rota (`accounts/profiles/`) e esquema (`ProfileSchema`) para API de perfil (https://github.com/3C-gg/reload-backend/issues/331).
- Adiciona método para encontrar o time de um usuário recebido no modelo `Match`.
- Novas propriedades e métodos no modelo `Account` relacionados as partidas do jogador e algumas estatísticas.
- Modelo `Match` passa a retornar resultados de QuerySet ordenados pelo campo `end_date` decrescente.
- Novo campo no modelo `Account` que guarda o maior level que o player já chegou.
- Notificação via websocket quando um amigo se cadastra e valida sua conta na plataforma (https://github.com/3C-gg/reload-backend/issues/371).
- Notificação via websocket ao aceitar um convite para um lobby (https://github.com/3C-gg/reload-backend/issues/371).
- Notificação via websocket ao recusar um convite para um lobby (https://github.com/3C-gg/reload-backend/issues/371).
- Notificação via websocket ao receber um novo convite para um lobby (https://github.com/3C-gg/reload-backend/issues/371).
- Método `online_users` no modelo `Users` para trazer todos os usuários online.
- Envio de notificações de sistema para usuários ativos ou online pelo admin (https://github.com/3C-gg/reload-backend/issues/372).
- Modelo `SystemNotification` para salvar notificações de sistema enviadas para usuários da plataforma.
- Método `create_system_notifications` no modelo `Notification` para criar notificações de sistema.
- Adiciona esquema de notificações no esquema de conta.
- Esquema de notificações `NotificationSchema`.
- Propriedade `notifications` e método `notify` ao modelo `Account`.
- Ícone de broadcast aos arquivos estáticos.
- App de notificações, incluindo modelo de cache `Notification` e testes (https://github.com/3C-gg/reload-backend/issues/355).
- Novo AppSettings e Config (`MAX_NOTIFICATION_HISTORY_COUNT_PER_PLAYER`) que limita a quantidade de notificações de cada usuário que guardamos no Redis.
- Campos `level` e `level_points` no esquema `MatchPlayerSchema` refletindo os dados históricos do modelo `MatchPlayer` (https://github.com/3C-gg/reload-backend/issues/364).
- Campos `level` e `level_points` no modelo `MatchPlayer` para refletir esses dados do usuário no momento histórico daquela partida.
- Nova carga de dados referentes a partidas e jogadores no `seed.json`.
- Campos de pontos na visualização do admin no modelo `MatchPlayer`.
- Limite no cálculo da quantidade de pontos que um jogador pode perder (https://github.com/3C-gg/reload-backend/issues/367).
- Novo AppSettings e Config (`PLAYER_MAX_LOSE_LEVEL_POINTS`) que limitam a quantidade de pontos que um jogador pode perder.
- Campo `create_date` no modelo `LobbyInvite` do Redis. Adiciona também esse campo no esquema `LobbyInviteSchema` (https://github.com/3C-gg/reload-backend/issues/363).
- Método de marcar a partida como cancelada no modelo `Match` (https://github.com/3C-gg/reload-backend/issues/360).
- Método de marcar a partida como pronta no modelo `Match` (https://github.com/3C-gg/reload-backend/issues/358).
- Adiciona algumas traduções faltantes.
- Método de iniciar partida no modelo `Match` (https://github.com/3C-gg/reload-backend/issues/356).
- Adiciona ação de finalizar partida no admin do modelo `Match`.
- Adiciona método de finalizar partida no modelo `Match` (https://github.com/3C-gg/reload-backend/issues/353).
- Adiciona testes faltantes para modelo `Match`.
- Novo arquivo `tasks` no package de websocket que expõe as tarefas como middleware para que o código possa chamar os eventos WS tanto como tarefas quanto como métodos normais dependendo do caso.
- Serviço do _Celery_ no _Kubernetes_.
- Serviço do _Celery_ no Github Workflow (https://github.com/3C-gg/reload-backend/issues/317).
- Dois novos serviços/configs ao AppSettings que ditam os limites de partidas nos servidores: `matches_limit_per_server` e `matches_limit_per_server_gap`.
- Três novas configuações default: `MATCHES_LIMIT_PER_SERVER`, `MATCHES_LIMIT_PER_SERVER_GAP` e `APP_INVITE_REQUIRED`.
- Nova propriedade `name` na entidade `Team` que é salva no Redis. Com essa prop podemos identificar os times mais facilmente e separá-los na criação da partida.
- Modelo `Server` para guardar informações sobre os servidores FiveM.
- Modelo `MatchTeam` para salvar dados relativos aos times de uma partida.
- Item de carga inicial local no banco de um servidor para testes.
- Docstrings para campos calculados do modelo `MatchPlayer`.
- Propriedades adicionadas ao modelo `Match`: `team_a`, `team_b`, `teams`, `winner`.
- Adiciona campo `server_ip` ao esquema API de `Match` (https://github.com/3C-gg/reload-backend/issues/321).
- Chamada websocket para client ao criar `Match` (https://github.com/3C-gg/reload-backend/issues/326).
- Adiciona admin para modelos de `matches`.
- Adiciona `__str__` para modelos de `matches` para que sejam mais facilmente identificados no admin.
- Adiciona método que adiciona Pontos de Nível (PNs) numa conta de usuário. Esse cálculo permite determinar se o jogador deve subir ou cair de Nível, ou se ele permanece no Nível atual alterando apenas seus PNs (https://github.com/3C-gg/reload-backend/issues/298).
- Adiciona cálculo de Pontos de Nível (PNs) ganhos no modelo `MatchPlayer`. Esse cálculo determina a quantidade de PNs que esse player deve ganhar em uma partda.
- Adiciona dois serviços no `AppConfig` e suas respectivas configs padrão do sistema: `PLAYER_MAX_LEVEL` e `PLAYER_MAX_LEVEL_POINTS`.
- Adiciona modelos do sistema de report (https://github.com/3C-gg/reload-backend/issues/338).
- Adiciona teste no Redis para garantir que o método retornado pela transação funcione.
- Cria modelo de `Player` no Redis.
- Adiciona sistema de penalidade/restrição de fila por dodges (https://github.com/3C-gg/reload-backend/issues/275).
- Cria modelo `MatchPlayerStats` no db para salvar as estatísticas do jogador.
- Adiciona endpoint de detalhe de partida (https://github.com/3C-gg/reload-backend/issues/342).
- URL `/health-check` para o health check do Ingress do GKE .
- Adiciona middleware para permitir que `/health-check` seja aberta para o Mundo ("`ALLOWED_HOSTS` excempt").

### Fixed

- Ajusta envio de websockets para client e cria testes para garantir o funcionamento ideal (https://github.com/3C-gg/reload-backend/issues/380).
- Alguns campos de esquemas da API estavam com valor tipado em `datetime`. Isso fazia com que o parseador da biblioteca de tarefas (Celery) não conseguisse converter esses valores em strings. Sendo assim, passamos a converter esses valores em strings (https://github.com/3C-gg/reload-backend/issues/379).
- Corrige token errada sendo enviada no e-mail de verificação (https://github.com/3C-gg/reload-backend/issues/352).
- Ajusta retorno do `controlller` e `route` de recusar convite para que não tenha nenhum retorno visto que existe uma deleção.
- Adiciona uma proteção que previne uma partida de ser finalizada se não tiver sido iniciada.
- Corrigimos os métodos do modelo `Server` para garantir que os métodos que definem se o servidor está quase cheio ou cheio filtrem apenas partidas em andamento.
- Corrigimos o cálculo de pontos (`points_earned`) de uma partida que estava retornando negativo mesmo que o usuário estivesse no nível 0 e com 0 pontos de nível.
- Código de verificação de e-mail estava _hardcoded_ no template de e-mail. Substituímos pelo código certo, individual e único para cada usuário (https://github.com/3C-gg/reload-backend/issues/299).
- Em um caso específico, onde tinham 2 players em um lobby e o player convidado (que não é o dono) sai ou é expulso, o dono do lobby não estava tendo seu status de "Em grupo" para "Online" atualizado para seus amigos. Uma vez que ele estava em grupo, e com a saída do convidado ele ficou num lobby vazio, começamos a disparar esse evento para o dono do lobby (https://github.com/3C-gg/reload-backend/issues/301).
- Ajusta string de conexão do Celery com o Redis quando a conexão for via SSL.
- Evento de recusado não estava sendo enviado para quem convidou, fazendo com que o convite ficasse "vivo" no client até o próximo carregamento do banco (https://github.com/3C-gg/reload-backend/issues/315).
- Evento que atualiza status do usuário não estava sendo disparado ao sair de um lobby (https://github.com/3C-gg/reload-backend/issues/319).
- AppSettings não era capaz de atualizar valores nos métodos de `set`. Com essa correção, ele atualiza os valores de uma config caso a encontre. Caso não encontre, ele cria uma nova com os valores recebidos.
- Impede que usuários iniciem uma busca por partidas caso já estejam em uma partida. Além disso, também protege a marcação de `lockin` e `ready` em pré partidas, além da mudança de modo/tipo de lobby (https://github.com/3C-gg/reload-backend/issues/329).
- Estávamos entrando em deadlock de transação ao tentar deletar convites dos usuários enquanto tentávamos mover eles para seus antigos lobbies. Consertamos esse problema, de maneira a não usar uma transação dentro de outra.
- Método `get_all` no modelo `PreMatch` estava pegando todas as chaves existentes com o pattern fornecido. Corrigido para que o método traga somente as chaves de `PreMatch` e não as de apoio.
- Corrige teste `matchmaking.tests.test_tasks.MMTasksTestCase.test_clear_dodges` que não estava passando pois estava setando datas hardcoded. Agora o teste roda com datas dinâmicas.

### Changed

- Altera link de convite do Discord nos e-mails (https://github.com/3C-gg/reload-backend/issues/377).
- Atualiza bilbioteca redis-py para última release.
- Altera manifestos do k8s para usar Ingress e Nginx ao invés do webserver padrão do Django (https://github.com/3C-gg/reload-backend/issues/304).
- Altera alguns termos "gta-mm" pra "reload".
- Controllers de API passam a enviar chamadas de WS em segundo plano usando tarefas do _Celery_ (https://github.com/3C-gg/reload-backend/issues/310).
- Celery agora está configuração `CELERY_ALWAYS_EAGER` ligada para testes.
- Esquema API de `Match` agora devolve um _JSON_ adequado com os valores aninhados: Partida > Times > Jogadores.
- Altera campo `leg_shots` para `other_shots` que simboliza tiros em outras partes do corpo que não peitoral/tórax e cabeça.
- Altera campo `team` do modelo `MatchPlayer` deixando de ser uma string e passando a ser uma relação com o novo model `MatchTeam`.
- Altera propriedade `rounds` do modelo `Match` para refletir mudanças incorporadas pelo modelo `MatchTeam`.
- Criação de partida no controller API de `matchmaking` para refletir novos modelos.
- Altera campo `status` no esquema API de `Match` para retornar uma string correspondente ao valor inteiro.
- Com a criação do modelo `MatchPlayerStats` o modelo `MatchPlayer` agora possui menos campos e cálculos, restando apenas a propriedade `points_earned`.
- Altera GH workflow `build_and_push.yaml` para que reflita repositórios de imagens do Docker do GCP ao invés da Digital Ocean.

### Removed

- Remove lib `django_object_actions` que estava causando erro nas actions do Github.
- Remove migrations velhas que foram _squashed_ via `squash_migrations`.
- Django Jazzmin foi removido devido a falta de suporte na renderização de ícones e imagens, o que tornava a utilização do admin mais difícil (https://github.com/3C-gg/reload-backend/issues/303).
- Removido level debug da lib Sentry.
- Remove campo `match` do modelo `MatchPlayer`.
- Remove campos de pontuação dos times (`team_a_score` e `team_b_score`) do modelo `Match`.
- Remove campo `winner_team` do modelo `Match`, que agora passa a ser um campo calculado.
- Remove etapa do deploy que aplicava instrução do `Deployment`.
- Remove arquivos antigos de instruções de cluster na Digital Ocean.

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
