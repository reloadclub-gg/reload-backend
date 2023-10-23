# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Filtro de "disponível" para usuários que estão online mas não estão em nenhum time, fila ou partida.

### Changed

- Filtro de online no admin agora reflete todos os usuários que estão com sessão ativa, independente de estarem nos outros estados de MM (em fila, em time, em partida, etc) [#703](https://github.com/3C-gg/reload-backend/issues/703).
- Métodos de login e logout no admin para atualizar campo `status` dependendo da ação do usuário.
- Altera a maneira como verificamos o status do usuário. Ao invés de verificar se usuário tem partida, time ou lobby, agora nós atualizamos um campo `status` no model `User` [#734](https://github.com/3C-gg/reload-backend/issues/734).

### Fixed

- Corrige método que move usuário entre lobbies, adicionando proteção caso o `from_lobby_id` não exista.
- Adiciona proteção no websocket `ws_friend_update_or_create` e em alguns pontos do código que chamam esse WS para usuários que não possuem conta [#732](https://github.com/3C-gg/reload-backend/issues/732).
- Corrige tarefa de montar times no mm que estava fazendo com que o mesmo lobby fosse adicionado a vários times diferentes [#730](https://github.com/3C-gg/reload-backend/issues/730).

### Removed

- Arquivo `WORKFLOW.md` do websockets, uma vez que já possuímos o `/ws/docs` que lista todos os endpoints de websocket, suas propriedades e retornos.
- Múltiplos workers do Celery. Estavam criando problemas de concorrência, atropelando um ao outro enquanto realizavam as tarefas, causando _race conditions_ [#727](https://github.com/3C-gg/reload-backend/issues/727).

## [e13e4c0 - 21/10/2023]

### Added

- Comando de sistema para enviar emails de verificação de conta para usuários não verificados [#714](https://github.com/3C-gg/reload-backend/issues/714).
- Endpoint de criação de convite.
- Métodos e background tasks para envio de email de convite para convidados.
- Campos `invites` e `invites_available_count` no `UserSchema` [#720](https://github.com/3C-gg/reload-backend/issues/720).
- Adiciona lógica para que todo usuário logado seja colocado em um grupo global de websocket.
- Método `resetlocust` no Makefile para facilitar os testes de performance.
- Função `scan_keys` no `RedisClient` que faz o scan baseado em um pattern recebido.

### Changed

- Altera docs de bootstrap.
- Altera maneira como comandos de start/restart de serviços são rodados no deploy e nos docs de bootstrap.
- Quantidade de convites que um usuário pode criar `4 -> 5`.
- Altera documentação de bootstrap de server para staging e prod para refletir mudanças de infra e performance [#716](https://github.com/3C-gg/reload-backend/issues/716).
- Altera comandos do script de deploy para funcionar com novas aplicações separadas (gunicorn, uvicorn e celery workers).
- Altera algumas configs de infra, como por exemplo, a quantidade de `burst` em que o NGINX deve se proteger no caso de um DDoS. Também renomeia e cria alguns scripts no `Pipfile` para ajudar na manutenção.
- Refatora lógica do Locust para representar, de maneira mais fiel, a utilização do sistema em um ambiente estressado.
- Altera configurações de infra da aplicação para reproduzir um ambiente de produção. Adiciona melhorias nessas configurações para melhorar a performance e reduzir latência.
- Remove a obrigatoriedade do parâmetro (`user_id`) no websocket `ws_create_toast`, fazendo com que o toast seja enviado para todos os usuários que estão conectados a um websocket.
- Adiciona parâmetro de timeout (`socket_timeout`) pool de conexões do Redis.
- Altera chave de autenticação (`auth token`) no Redis. Diminui o tamanho da string (128 -> 6) e adiciona o `id` do usuário na chave, tornando cada chave única.
- Refatora lógica de criação de usuário fake, utilizando um parâmetro para criar token na criação da sessão e não depois dela. Também remove a atualização do campo `last_login`, que não é necessário.
- Altera configs do Nginx para melhorar performance e segurança [#709](https://github.com/3C-gg/reload-backend/issues/709).
- Altera quantidade de workers locais do Uvicorn para permitir maior número de conexões simultâneas.
- Altera bootstrap de aplicação pra refletir novas configs do Nginx [#711](https://github.com/3C-gg/reload-backend/issues/711).
- Todos os `cache.keys({PATTERN})` foram alterados para usar a nova função `scan_keys` que tem uma performance muito melhor e não "trava" a conexão com o Redis [#704](https://github.com/3C-gg/reload-backend/issues/704).
- Alteramos a maneira como instanciávamos o `RedisClient`. Antes, estávamos abrindo um pool de conexão por acesso. Agora, estamos usando sempre o mesmo pool [#704](https://github.com/3C-gg/reload-backend/issues/704).

### Fixed

- Adiciona `id` correto de item e caixa no esquema `UserInventorySchema`. O campo `id` estava o do item ou caixa originais (`Item`/`Box`), fazendo com que o backend retornasse `404`, pois o `id` correto é o do `UserItem`/`UserBox` [#707](https://github.com/3C-gg/reload-backend/issues/707).

## [04/10/2023 - 69f2c75]

### Added

- API para sistema de iventário/itens [#694](https://github.com/3C-gg/reload-backend/issues/694).
- Novas traduções.
- Novas configs de loja: `STORE_LENGTH`, `STORE_FEATURED_MAX_LENGTH` e `STORE_ROTATION_DAYS`.
- Campo de porta de API do servidor FiveM [#681](https://github.com/3C-gg/reload-backend/issues/681).
- Ping websocket de 7 em 7 segundos para manter conexão ativa sem que browsers derrubem a conexão quando o aplicativo estiver em background (`alt+tab`) [#667](https://github.com/3C-gg/reload-backend/issues/667).
- Adiciona campo `thumbnail` no modelo `Map`.
- Adiciona método de apoio que monta URL de arquivos estáticos.

### Changed

- Desbloqueia adição/remoção de itens e caixas de usuário via admin para superusuários, deixando somente a opção de alteração bloqueada [#679](https://github.com/3C-gg/reload-backend/issues/697).
- Métodos que usavam `15` "hardcoded" para determinar vitória de um dos times agora usam a configuração de rounds necessários para vencer (`MATCH_ROUNDS_TO_WIN`).
- Configuração da quantidade de rounds necessários a ganhar por um dos times para que a partida seja considerada finalizada (15 -> 13) [#689](https://github.com/3C-gg/reload-backend/issues/689).
- Esquema `MatchListItemSchema` agora possui 3 novos campos: `map_image`, `game_type` e `start_date`.
- Campo `score` do esquema `MatchListItemSchema` agora é exibido da seguinte forma "X - Y" ao invés de "X:Y" [#671](https://github.com/3C-gg/reload-backend/issues/671).

### Fixed

- Ajusta dados do arquivo `seed.json` que era carregado ao iniciar a aplicação.
- Ajusta quantidade de pontos perdidos ao estrapolar quantidade de pontos atuais do jogador [#673](https://github.com/3C-gg/reload-backend/issues/673).

## [08/09/2023 - 2f353fd8]

### Added

- Campo para porta de servidor Fivem.
- Novo comando de admin que simula um update de partida vindo do FiveM.
- Nova config `DOCKER_SITE_URL` que expõe a "url dockerizada" da aplicação (ex: `http://django:8000`).
- Mixin para testes de partidas finalizadas.
- Campo `steam_url` no esquema `MatchPlayerSchema` [#650](https://github.com/3C-gg/reload-backend/issues/650).
- Campo `status` nos esquemas `ProfileSchema`, `MatchPlayerSchema` e `LobbyPlayerSchema` [#644](https://github.com/3C-gg/reload-backend/issues/644).
- Endpoint de alteração de `social_handles` em `profiles` [#645](https://github.com/3C-gg/reload-backend/issues/645).
- Campo `social_handles` no modelo `Account`.
- Tarefa agendada para rodar diariamente que deleta partidas canceladas que já tenham terminado a mais de um dia [#622](https://github.com/3C-gg/reload-backend/issues/622).
- Nova config para escolher se o mock do FiveM vai enviar um pedido para cancelar ou para iniciar a partida.
- Tarefa para simular chamada de cancelamento de partida do FiveM.
- Tarefa para simular chamada de start de partida do FiveM.
- Comando de manutenção `create_some_matches` que cria a quantidade de partidas informada por parâmetro na linha de comando.
- Admin com times, players e chats na partida.
- Chats de partida no `seed.json`.
- Scripts no `Pipfile` para iniciar django e celery em modo de desenvolvimento local (`dev` e `celery_dev`).
- Campo `chat` no modelo `Match` [#615](https://github.com/3C-gg/reload-backend/issues/615).
- Comando de manutenção `create_fivem_match` que cria um servidor com o IP fornecido e tenta criar uma partida nesse servidor via HTTP [#600](https://github.com/3C-gg/reload-backend/issues/600).
- Campo `report_user_id` no esquema `TicketSchema`.

### Changed

- Move função de pegar amigos da steam do controller de Friend para model Account.
- Altera namespace de url do websocket para um nome mais adequado (`ws_auth -> ws_app`).
- Ajusta estatísticas do modelo `MatchPlayerStats` para que fique mais fácil de agregar os resultados de todas as partidas.
- Refatora lista de partidas de perfil para entregar somente o que é necessário ao FE [#634](https://github.com/3C-gg/reload-backend/issues/634).
- Envia websocket `matches/delete` ao receber um cancelamento de partida do FiveM [#626](https://github.com/3C-gg/reload-backend/issues/626).
- Altera "cancled" com "L" para "cancelled" com 2 "L"s.
- Altera esquema `MatchUpdateSchema` para receber um campo `status`, que deve atualizar o status da partida quando recebido.
- Altera nome de configurações relativas aos mocks do FiveM.
- Altera campo `status` do modelo `Match` para texto e passa a utilizar status `loading` [#620](https://github.com/3C-gg/reload-backend/issues/620).
- Altera nome da configuração de rounds necessários para vencer uma partida de `WIN_ROUNDS` para `MATCH_ROUNDS_TO_WIN`.
- Quantidade padrão de rounds para ganhar (16 -> 15) [#618](https://github.com/3C-gg/reload-backend/issues/618).
- Template de email de verificar conta agora não tem mais link no código de verificação [#603](https://github.com/3C-gg/reload-backend/issues/603).
- Template de PR do Github.
- Passamos a calcular double, triple, quadra e ace separadamente [#606](https://github.com/3C-gg/reload-backend/issues/606).
- Quantidade de rounds para detectar fim da partida agora é uma config [#605](https://github.com/3C-gg/reload-backend/issues/605).
- Melhoramos os esquemas de FiveM para enviar somente campos que são necessários.
- Movemos a lógica de tratamento da partida baseado na resposta do método `handle_create_fivem_match` para o método `set_player_ready` para não sobrecarregar o méotodo de apoio com funções que não são dele.
- Alteramos o arquivo de template de PR no Github para algo mais simples e prático.
- Removemos o workflow de buildar e fazer o push da imagem Docker para o GCP, visto que não estamos mais usando o GCP.
- Alteramos os nomes dos arquivos de deploy para deixar somente o que executa no EC2.
- Alteramos o conteúdo da mensagem que vai para o sistema do Freshdesk. E adicionamos as informações do usuário denunciado, caso tenha.

### Fixed

- Ajusta propagação de eventos de login e logout de amigos [#665](https://github.com/3C-gg/reload-backend/issues/665).
- Conserta deploy que estava rodando com arquivo de variável de ambiente antiga.
- Adiciona proteção nas configs de log para que o sistema ignore essas configs quando não houver envvars do papertrail setadas.
- Corrige estatísticas agregadas no esquema de perfil [#646](https://github.com/3C-gg/reload-backend/issues/646).
- Corrige teste de detalhe de perfil que falhava de maneira itermitente. Isso acontecia devido a um cast do campo `steamid` para `int`, que para testes, é gerado artificialmente, podendo, as vezes, começar com `0`. Quando a conversão para `int` acontecia, ela removia os `0`s iniciais, deixando o valor diferente do cadastrado na conta do usuário.
- Ajusta ordenação do qs de lista de partidas de um usuário para trazer as mais recentes primeiro.
- Quando a aplicação não consegue criar a partida no FiveM, estávamos apenas cancelando a partida, sem enviar as devidas atualizações de usuário e amigos via websocket para o FE. Corrigimos para chamar sempre a mesma função de cancelamento independente da situação.
- Cancelamento de partida vindo do FiveM não estava funcionando para partidas em status de aquecimento (`matches.models.Match.Status.WARMUP`) [#637](https://github.com/3C-gg/reload-backend/issues/637).
- Lista de chat no admin de partidas estava dando erro. Não estávamos convertendo o steamid retornado pelo FiveM que é em hexadecimal antes de tentar trazer a conta do usuário que enviou a mensagem. Corrigimos para fazer a conversão [#632](https://github.com/3C-gg/reload-backend/issues/632).
- Workflow do Github que checa se CHANGELOG.md foi alterado [#269](https://github.com/3C-gg/reload-backend/issues/269).
- Ajusta redirecionamento da Steam em ambiente local sem porta no domínio: `localhost` quando deveria ser `localhost:8000` [#629](https://github.com/3C-gg/reload-backend/issues/629).
- Corrige tarefa que chama api em ambiente local para setar partida como pronta (mock do FiveM) [#624](https://github.com/3C-gg/reload-backend/issues/624).
- Em alguns casos, precisamos converter o steamid64 para hexadecimal para "conversar" com o servidor de jogo (FiveM). Como geramos usuários e steamids fakes, em alguns casos, estávamos gerando o steamid64 com 0s na frente. O código de conversão ignorava esses 0s a esquerda do número e ao "re-converter" para steamid64, os 0s originais não eram adicionados, fazendo com que, alguns testes falhassem "de vez em quando". Consertamos esse comportamento.
- Paginação da API não estava entregando a quantidade total de páginas corretamente [#618](https://github.com/3C-gg/reload-backend/issues/618).
- Corrige os pontos perdidos para o jogador que perde partida e está no level 0 [#612](https://github.com/3C-gg/reload-backend/issues/612).
- Corrigimos esquema `MatchPlayerProgressSchema` com campos `null` estava fazendo com que FE não renderizasse corretamente [#610](https://github.com/3C-gg/reload-backend/issues/610).
- Detalhe de partida estava permitindo partidas canceladas. Agora estamos retornando 404 para essas partidas e apenas partidas finalizadas ou em andamento podem ser exibidas no FE [#609](https://github.com/3C-gg/reload-backend/issues/609).
- Admin de notificações estava com erro ao carregar usuários online. Antigamente retornávamos um QS e agora estamos retornando uma lista. Contornamos o problema.

## [ 24/7/2023 - 7e7192c]

### Special

- Muitas coisas foram alteradas as pressas pra cumprir com a data de lançamento inicial. Um grande esforço foi aplicado para reduzir ao máximo a latência e o `load` das chamadas e das queries. Conseguimos reduzir de 120+ queries no banco para 10 em algumas chamadas. Também alteramos os Schemas, pois alguns deles estavam enviando informações desnecessárias, causando overload de rede e consultas no banco. Para nos ajudar nessa tarefa, instalamos a bilbioteca Silk para fazer inspeções e `profiling` das chamadas.

Além disso, configuramos o ambiente local para rodar réplicas da aplicação django e celery, tentando simular o Kubernetes no ambiente da nuvem. Para esse fim, adicionamos uma camada de Nginx no nosso desenvolvimento local para que ele controle a qual "pod" envia os pedidos.

Ao testar com o Locust (outra ferramenta bem importante nesse processo), usando cenários de 30 usuários, "nascendo" 2-5 usuários por segundo e com uma carga de ~20 requisições por segundo, víamos algumas requisições ficarem penduradas por mais de 20s. Conseguimos reduzir bem esse número, mas é difícil de testar os "pods" em ambiente local.

### Added

- Métodos de apoio para conversão de steamid64 em hex e vice-versa.
- Botão para assumir identidade de um usuário por um membro do staff no admin [#579](https://github.com/3C-gg/reload-backend/issues/579).
- Modelo `IdentityManager` para salvar um log de todos os staff que assumem usuários.
- Bilbioteca `django-object-actions` para adicionar ações aos objetos no admin.
- Adiciona proteção no conteúdo de `social_user.extra_data` para sempre transformar para dict antes de usar.
- Endpoint para cancelamento de partida a partir do FiveM [#334](https://github.com/3C-gg/reload-backend/issues/334).
- Chamada para criação de partida no FiveM na criação de partida [#243](https://github.com/3C-gg/reload-backend/issues/243).
- Configs (`FIVEM_MATCH_MOCK_DELAY_START` e `FIVEM_MATCH_MOCK_CREATION_SUCCESS`) de testes locais para mock de início de partidas no FiveM.
- Mixin de testes para lobbies.
- Tarefas de `queue` e `matchmaking` que percorrem os lobbies em fila para montar partidas. Essas tarefas entram para substituir a formação de times e oponentes ao iniciar a fila.
- Método para trazer todos os lobbies em fila no modelo `Lobby`.
- Proteções ao modelo `Team` para não trazer valor nulo nas queries. Também adiciona proteção de transação em chaves críticas ao adicionar um lobby.
- Ferramenta de teste de carga `Locust`.

### Changed

- Assumir identidade via admin agora só aparece para usuários não-staff [#596](https://github.com/3C-gg/reload-backend/issues/596).
- O FiveM só aceita o steamid hexadecimal, então passamos a fazer a conversão do steamid64 (que é o nosso padrão) para o hexadecimal ao nos comunicar com os servidores FiveM [#594](https://github.com/3C-gg/reload-backend/issues/594).
- Passamos a manter as versões fixadas no pipenv a fim de evitar que alguma atualização quebre a aplicação.
- Mixin de testes de times, que continha uma lógica muito extensa. A lógica de criação de lobbies desse mixin foi movida para seu próprio mixin de lobbies.
- Troca Backend de emails do Django para `dummy` ao invés de `console`.
- Altera ordem da deleção de pré-partidas, passando a deleção destas para antes da deleção dos times. Isso pode evitar _race conditions_.
- Altera chave de `auto_id` do Redis para o modelo `PreMatch`. O padrão anterior estava conflitando com algumas operações no Redis.
- Altera método `get_all` do modelo `PreMatch` para padronizar com o restante dos models e adotar a alteração do `auto_id`.

### Fixed

- Fila com múltiplos lobbies estava gerando um erro no gerenciamento de time. Foi corrigido substituindo a lógica síncrona de criação de time e partida a partir do start da fila de um lobby por duas tarefas que varrem o Redis em busca de lobbies e times prontos para montar a partida corretamente [#590](https://github.com/3C-gg/reload-backend/issues/590).

### Removed

- Status `READY` do modelo `Match` foi removido pois não precisamos desse estado. Depois de `LOADING` já podemos ir para `RUNNING`.

## [46ada28 - 17/7/2023]

### Added

- Nova tarefa `end_player_restriction` que será chamada quando uma restrição de jogador terminar. Essa tarefa faz chamadas websockets para o FE saber que a restrição do player acabou [#587](https://github.com/3C-gg/reload-backend/issues/587).
- Configuração no settings para definir os multiplicadores de tempo de restrição dos dodges(`PLAYER_DODGES_MULTIPLIER`).
- Configuração no settings para definir a quantidade mínima de dodges que o jogador precisa fazer para sofre a primeira restrição (`PLAYER_DODGES_MIN_TO_RESTRICT`).
- Chamadas websocket `ws_update_user` e `ws_friend_update_or_create` quando a partida é finalizada [#539](https://github.com/3C-gg/reload-backend/issues/539).
- Esquemas `MatchUpdatePlayerStats` e `MatchUpdateSchema` para conter os dados recebidos pelo servidor FiveM.
- Decorator que garante que determinados endpoints do app `Matches` sejam acessados somente por servidores conhecidos.
- Websocket `matches/update` para atualizar partida em andamento para jogadores.
- Endpoint para atualizar partida a partir de um servidor FiveM [#333](https://github.com/3C-gg/reload-backend/issues/333).
- Cancela todas as filas ao ligar manutenção [#565](https://github.com/3C-gg/reload-backend/issues/565).
- Websocket `lobbies/queue_start` para que o client possa interceptar e reiniciar a fila do lobby.
- Método que cancela todas as filas de todos os lobbies.

### Changed

- Altera tarefa `cancel_match_after_countdown` para ficar menos complexa e seguir padrões de formatação.
- Atualiza modelo `Player` para utilizar novas configs de dodges.
- Separa configs relacionadas as dodges de fila no settings.
- Move métodos estáticos do modelo `Player` de modo que fiquem todos juntos e organizados.
- Atualiza arquivos de admin e prepara admin para lançamento [#580](https://github.com/3C-gg/reload-backend/issues/580).
- Altera multiplicadores do tempo de restrição para dodges, deixando eles menos agressivos para os primeiros dodges.
- Altera página de partida em andamento para que somente os jogadores naquela partida possam acessá-la nesse estado.
- Envio de ws `lobbies/update` quando a partida for cancelada para todos os lobbies participantes [#573](https://github.com/3C-gg/reload-backend/issues/573).
- Move métodos estáticos do modelo `Lobby` de modo que fiquem todos juntos e organizados.
- Altera verificação de backend de envio de emails do Django para usar o console caso o valor de `EMAIL_HOST` seja diferente de `localhost`.

### Fixed

- Problema ao ter múltiplos lobbies em fila com dodges. Os times não estavam sendo carregados e deletados corretamente [#585](https://github.com/3C-gg/reload-backend/issues/585).
- Erro que fazia com que jogadores ficassem impossibilitados de iniciar fila, caso viessem de um lobby que foi deletado, ou seja, que o dono fez logout, inativou conta, excluiu conta ou alterou email [#583](https://github.com/3C-gg/reload-backend/issues/583).
- Erro no cálculo de média de HS por round.
- Problema em que fazia com que lobbies não atualizassem o tick no client depois de voltar de uma partida cancelada por outro lobby.
- Propriedade `ready` do modelo `Team` que estava com uma verificação errada.
- Corrige erro que fazia com que durante o matchmaking, se um lobby tivesse chegado ao limite de jogadores para estar pronto, ao entrar em fila com um teceiro lobby, sem estar com o limite de jogadores atingido, ele encaixava o novo lobby no time já existente ao invés de criar o seu próprio, e ainda criava uma partida com times duplicados [#571](https://github.com/3C-gg/reload-backend/issues/571).
- Corrige tradução de mensagem em tarefa do Celery.
- Ao tentar fazer lockin ou ready de um jogador, estávamos checando uma config fixa, o que não permitia que fizéssemos testes 3x2, por exemplo. Corrigimos para que as verificações sejam em cima da quantidade de players na partida, e não em cima da config fixa [#567](https://github.com/3C-gg/reload-backend/issues/567).
- Ao deletar um jogador (model `Player`), estávamos tentando carregar o jogador do Redis. Porém, se por algum motivo o jogador não tivesse sido criado ou já tivesse sido excluído, estávamos encontrando um erro `Player not found`. Removemos a busca pelo jogador no Redis, visto que o método `delete` já recebe o `user_id`, que é necessário para remover a chave do `set` no Redis [#563](https://github.com/3C-gg/reload-backend/issues/563).

### Removed

- Configuração `TEAM_READY_PLAYERS_MAX` que não estava sendo usada corretamente.

## [e6b3241 - 9/7/2023]

### Added

- Tarefa que envia websocket para client a cada "tick" da fila do lobby [#555](https://github.com/3C-gg/reload-backend/issues/555).

### Fixed

- Corrigimos um erro que fazia com que a aplicação não pegasse as traduções atualizadas. O arquivo compilado de traduções atualizado precisa estar na imagem Docker para ser lido pelo Django. Estávamos tentando rodar o comando de compilar as mensagens durante o deploy [#558](https://github.com/3C-gg/reload-backend/issues/558).
- Corrigimos um erro que acontecia quando o usuário troacava de e-mail. Ele não estava saindo dos lobbies e chamando os websockets necessários [#559](https://github.com/3C-gg/reload-backend/issues/559).
- Ao validar conta estávamos enviando uma notificação de novo cadastro para os amigos do usuário. Mas isso só deveria acontecer para novos cadastros, e o método de validar conta também é executado quando o usuário troca de e-mail. Adicionamos uma proteção para que o envio da notificação seja feito corretamente.

## [45128bd - 02/07/2023]

### Added

- Adiciona algumas configurações padrão como migrations [https://github.com/3C-gg/reload-backend/issues/550](#550).
- Campo `date_joined` no esquema `ProfileSchema` [#548](https://github.com/3C-gg/reload-backend/issues/548).
- Adiciona sistema de mapa de partida [#545](https://github.com/3C-gg/reload-backend/issues/545).
- Envio de websocket para atualizar lobby ao convidar ou recusar convite [#540](https://github.com/3C-gg/reload-backend/issues/540).
- Envio de toast e notificação via ws ao iniciar uma manutenção.
- Esquema `HealthCheckSchema` com infos sobre o sistema.
- Proteção nas ações de lobby que não podem ser executadas enquanto estiver em manutenção.
- Serviço de verificação de manutenção no app `appsettings` [#536](https://github.com/3C-gg/reload-backend/issues/536).
- Websocket de manutenção (`maintenance/start` e `maintenance/end`) ao app `core` [#535](https://github.com/3C-gg/reload-backend/issues/535).
- Campo `level` no esquema `MatchPlayerSchema` [#533](https://github.com/3C-gg/reload-backend/issues/533).
- Envios de websockets de criação de partidas depois de todos os jogadores se marcarem como pronto [#531](https://github.com/3C-gg/reload-backend/issues/531).
- Campos `match_id` e `pre_match_id` no esquema `UserSchema` [#528](https://github.com/3C-gg/reload-backend/issues/528).
- Chamadas ws para expirar/excluir convites enviados de acordo com cada situação, quando um jogador troca de lobby [#521](https://github.com/3C-gg/reload-backend/issues/521).
- A aplicação `matches` agora possui seu próprio emissor de websockets.
- Criamos a aplicação `pre_matches` que vai substituir a `matchmaking`.
- Envio de websocket para criar um toast no FE quando um usuário for expulso de um lobby [#505](https://github.com/3C-gg/reload-backend/issues/505).
- Método de websocket em `core` para criar toasts no FE.

### Changed

- Ajusta testes para não criar configuração padrão, e sim modificá-los, visto que já estamos as criando nas migrations.
- Ajusta banco de dados e Redis para testes.
- Remove `flushdb` do script `loaddata` do Pipfile.
- Tarefa `cancel_match_after_countdown` agora imterrompe a execução com um retorno ao invés de levantar um erro quando a `pre_match` não for encontrada [#544](https://github.com/3C-gg/reload-backend/issues/544).
- Refatora função de mover jogadores no controller de lobbies para enviar alguns updates faltantes pro FE via websockets [#541](https://github.com/3C-gg/reload-backend/issues/541).
- Ajusta endpoint de health_check (`/api/`) para retornar o esquema `HealthCheckSchema`, que contém dentre outras infos, a de manutenção [#537](https://github.com/3C-gg/reload-backend/issues/537).
- Remove envio de todos os emails para o mailtrap. Caso a gente precise ver o email no mailtrap, devemos adicionar as variáveis de ambiente necessárias [#515](https://github.com/3C-gg/reload-backend/issues/515).
- Altera o campo `queue` do esquema `LobbySchema` para retornar o valor em `ISO` [#426](https://github.com/3C-gg/reload-frontend/issues/426).
- Renomeia método `player_move` do `controller` na `api` do app `lobbies` para `handle_player_move` para seguir um padrão em que os métodos de apoio dos controladores possuem `handle_` como prefixo.
- `ws_expire_player_invites` do websocket de `lobbies` agora recebe dois parametros opcionais: `sent` e `received` que indicam quais convites devem ser excluídos. Caso nenhum seja informado, todos os convites serão excluídos.
- Método `move` do modelo `Lobby` não exclui mais os convites enviados pelo usuário que se moveu. Essa lógica agora tem que ser realizada por quem está controlando a transferência de lobbies do usuário.
- Melhorias no endpoint de detalhe de perfil.
- Substitui a aplicação `matchmaking` pela `pre_matches`.
- Move a tarefa `clear_dodges` para o app `lobbies`.
- Move mixin de teste `VerifiedAccountsMixin` para app `accounts`.
- Altera comando startapp no Makefile para ficar mais "verbose".

### Fixed

- Corrige erro ao tentar salvar lista de amigos no Redis. Quando não haviam amigos retornados pelo sistema, tentávamos incluir "nada" na lista no Redis, que retornava um erro. Adicionamos uma proteção para só adicionar no Redis, caso a lista contenha algum resultado [#553](https://github.com/3C-gg/reload-backend/issues/553).
- Corrige modelos do `AppSettings` que não estavam salvando corretamente o tipo da config.
- Ajusta websocket de criação de partida não estar sendo enviado aos grupos corretos.
- Ajusta typo no método `get_by_from_user_id` do model `LobbyInvite`.
- Adiciona verificação no método `delete` do model `Player` e no método `mode` do model `Lobby` para que, caso os valores solicitados não existam, o sistema não jogue um erro inesperado.
- Chamada para websocket informando que o amigo se cadastrou estava sendo formatada errada, antes da frase ser traduzida. Mudamos a formatação para ser feita logo após a tradução e passou a funcionar [#516](https://github.com/3C-gg/reload-backend/issues/516).

### Removed

- Códigos legados da aplicação `websocket`.

## [cef26da - 26-06-2023]

### Added

- Ao fazer logout, agora deletamos a lista de amigos do usuário que deslogou [#492](https://github.com/3C-gg/reload-backend/issues/492).
- Método `delete` no modelo `LobbyInvite` para deletar convites. Esse método deve substituir o método `delete_invite` do modelo `Lobby` na tarefa [#502](https://github.com/3C-gg/reload-backend/issues/502).
- Novo websocket para notificar todas as sessões do usuário no FE de que ele fez logout [#461](https://github.com/3C-gg/reload-backend/issues/461).
- Ao iniciar a fila de um lobby, o sistema agora monta ou encontra um time para aquele lobby, em seguida busca por um adversário, e, case encontre um, envia o websocket de partida encontrada [#457](https://github.com/3C-gg/reload-backend/issues/457).
- Método `ws_match_found` ao websocket de matchmaking.

### Changed

- Tarefa `watch_user_status_change` agora passa a usar o controller `logout` para deslogar o usuário.
- Altera endpoint de cancelar para deletar usuário do banco. Cria outro endpoint para inativar [#489](https://github.com/3C-gg/reload-backend/issues/489).
- Mudamos a tarefa `watch_user_status_change` para enviar um websocket de logout caso, por algum motivo, o FE do usuário ainda esteja ativo [#498](https://github.com/3C-gg/reload-backend/issues/498).
- Altera comportamento de websocket `ws_expire_player_invites` para deletar convites depois de enviar a expiração deles para o FE.
- Altera a quantidade de workers e processos que cada container roda. Também setamos o nível de debug do celery para `WARNING`, além de remover a opção `--reload` do `uvicorn` em produção [#495](https://github.com/3C-gg/reload-backend/issues/495).
- Mudamos a lógica de amigos. Agora só vamos a Steam atualizar a lista de amigos quando o FE solicita o endpoint `friends/`. Esse endpoint vai à Steam e salva os amigos no Redis, a partir desse ponto, todas as chamadas para amigos são realizadas diretamente no cache. Quando um usuário se cadastra e verifica sua conta, a gente adiciona ele na lista de amigos de seus amigos no cache [#474](https://github.com/3C-gg/reload-backend/issues/474).
- Campo `lobby_id` no esquema `LobbyPlayerSchema` agora pode ser nulo.
- Lógica de mover player foi refatorada para termos melhor compreensão sobre ela e sobre os eventos disparados via websocket. Com isso, também mitigamos alguns websockets que não estavam sendo enviados ou estavam sendo erroneamente enviados para o FE [#465](https://github.com/3C-gg/reload-backend/issues/465).
- Model `Team` não utiliza mais a `TeamConfig.READY_PLAYERS_MIN`. Ao invés disso, pega esse valor direto de `django.conf.settings.TEAM_READY_PLAYERS_MIN`.

### Fixed

- Corrige erro ao enviar tickets de suporte. Eram 2 problemas: o primeiro era relacionado aos anexos serem enviados para o CDN, fazendo com que o sistema de arquivos não encontrasse os anexos salvos localmente. Para esse problema, removemos o upload para o CDN, uma vez que não teremos uploads de usuários (até segunda ordem). O segundo problema, era que o sistema estava tentando enviar o email com o `from` do usuário, porém, para que possamos enviar emails via AWS, precisamos verificar o `from`, o que foi feito com todos os emails do domínio `reloadclub.gg`. Como os emails dos usuários não estão verificados como `from`, o envio de emails da AWS retornava um erro. Ajustamos para enviar o email de `from` verificado (`equipe@reloadclub.gg`) e adicionamos um header ao envio do email (`reply_to`) para que o analista do Freshdesk possa responder a esse usuário via e-mail [#506](https://github.com/3C-gg/reload-backend/issues/506).
- Ajusta avatar de notificações de sistema que estava sendo enviado errado [#509](https://github.com/3C-gg/reload-backend/issues/509).
- Encontramos e corrigimos alguns erros de nomenclaturas no sistema de CDN. Além disso, mudamos também a forma como detectamos se devemos aplicar as configurações de CDN - antes fazíamos baseado em uma das configs CDN, agora passamos a fazer baseado no ambiente (`ENVIRONMENT`).
- Sistema não estava enviando notificações via websockets criadas a partir do admin.
- Adicionamos o envio de websocket para corrigir e expirar convites de jogadores de um lobby que iniciam fila [#500](https://github.com/3C-gg/reload-backend/issues/500).
- Corrigimos um problema que fazia com que os jogadores de um lobby não fossem atualizados via ws ao iniciar ou cancelar a fila [#490](https://github.com/3C-gg/reload-backend/issues/490).
- Corrigimos um bug que fazia com que o usuário e seus amigos não fossem notificados via WS quando entravam ou saíam da fila [#482](https://github.com/3C-gg/reload-backend/issues/482) [#483](https://github.com/3C-gg/reload-backend/issues/483).
- Resolvemos um erro que fazia com que um erro fosse retornado ao iniciar fila com mais de um jogador por lobby [#478](https://github.com/3C-gg/reload-backend/issues/478).
- Corrigimos um erro que fazia com que, ao encontrar uma partida, não estava sendo disparado update para os lobbies [#480](https://github.com/3C-gg/reload-backend/issues/480).
- Resolvemos um erro que fazia com que, ao cancelar fila de um lobby, o sistema não estava removendo esse lobby de um time caso estivesse em um [#476](https://github.com/3C-gg/reload-backend/issues/476).
- Resolvemos erros de envio de websocket faltando em alguns casos do processo de matchmaking [#471](https://github.com/3C-gg/reload-backend/issues/471).
- Corrigimos um erro que fazia com que a notificação que informa aos amigos de um jogador que ele acabou de se cadastrar não estava sendo disparada corretamente [#468](https://github.com/3C-gg/reload-backend/issues/468).
- Sessão de usuário não estava persistindo depois de uma chamada bem sucedida para `/auth` [#467](https://github.com/3C-gg/reload-backend/issues/467).
- Controle de sessões não estava bom, causando verificações duplicadas e até mesmo código que nunca era acessado devido a más verificações. Passamos a adicionar uma sessão sempre que o usuário acessa a rota `/auth` e é verificado. O Websocket agora só altera a sessão no `disconnect`, e não adiciona mais sessões, apenas remove [#462](https://github.com/3C-gg/reload-backend/issues/462).
- Documentação de websockets não abria corretamente contendo âncora na URl [#459](https://github.com/3C-gg/reload-backend/issues/459).

### Removed

- Campos não utilizados no esquema `AccountSchema`: `lobby`, `match`, `pre_match` e `friends`. Esses campos estavam causando uma demora muito grande em carregar o esquema no client, e como não utilizamos mais eles, foram removidos para ajudar no load up.

## [46559aa - 19-06-2023]

### Added

- Retorno ao aceitar ou recusar convites [#454](https://github.com/3C-gg/reload-backend/issues/454).
- Campo `lobby_id` no esquema `LobbyPlayerSchema` [#452](https://github.com/3C-gg/reload-backend/issues/452).
- Actions das chamadas websocket nos docs [#447](https://github.com/3C-gg/reload-backend/issues/447).
- Envio de WS de expiração de convites quando usuário fizer logout `invites/expire`.
- Envio de WS quando usuário se cadastrar `friends/create` [#444](https://github.com/3C-gg/reload-backend/issues/444).
- Campo `profileurl` nos dados de inicialização pra testes locais (`seed.json`).
- Views de documentação de websockets em `/ws/docs` [#436](https://github.com/3C-gg/reload-backend/issues/436).
- O package `websocket` agora é um app do Django.
- Dois esquemas exclusivos para websockets: `LobbyInviteWebsocketSchema` e `LobbyPlayerWebsocketUpdate`. Esses dois esquemas facilitam o envio de dados para o client via ws e também servem para padronizar a documentação dos websockets.
- Chamadas websocket sempre que houver alterações no lobby (queue, etc) [#439](https://github.com/3C-gg/reload-backend/issues/439).
- Chamadas websocket sempre que houver alterações na lista de jogadores de um lobby [#434](https://github.com/3C-gg/reload-backend/issues/434).

### Changed

- Campo `id` passa a ser `user_id` no esquema `FriendSchema` [#450](https://github.com/3C-gg/reload-backend/issues/450).
- Campo `lobby` passa a ser `lobby_id` no esquema `FriendSchema` [#437](https://github.com/3C-gg/reload-backend/issues/437).
- Websockets de `notifications` agora recebem objetos ao invés de valores primitivos.
- Websockets de `lobbies` agora recebem objetos ao invés de valores primitivos.
- Websocket `ws_friend_update` agora recebe objeto `User` ao invés de `user_id: int`.

### Fixed

- Os convites enviados para um usuário que fez logout estavam permanecendo no Redis. Removemos eles no logout do usuário, onde removemos também o seu lobby.

### Removed

- Comentário de testes de tarefas em `accounts`.
- Campos calculados do `FriendSchema` uma vez que eles estão disponíveis como campos de db.
- Não obrigatoriedade de campos que são obrigatórios no esquema `FriendSchema`.
- Campo `match` do esquema `FriendSchema` por não ser utilizado.

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
