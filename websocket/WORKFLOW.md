# Websocket workflow

Mapeamento de disparo dos eventos websocket disparados baseados em triggers

## [Add WS ao inativar conta](https://github.com/3C-gg/reload-backend/issues/62)

| Pra quem?                   | Payload             | Action                |
| --------------------------- | ------------------- | --------------------- |
| Usuários que estão no lobby | LobbySchema         | ws_lobbyPlayersUpdate |
| Amigos online               | FriendAccountSchema | ws_userStatusChange   |

## [Add WS ao trocar email](https://github.com/3C-gg/reload-backend/issues/70)

| Pra quem?                   | Payload             | Action                |
| --------------------------- | ------------------- | --------------------- |
| Usuários que estão no lobby | LobbySchema         | ws_lobbyPlayersUpdate |
| Amigos online               | FriendAccountSchema | ws_userStatusChange   |

## [Add WS ao entrar em um lobby](https://github.com/3C-gg/reload-backend/issues/71)

| Pra quem?                        | Payload             | Action                 |
| -------------------------------- | ------------------- | ---------------------- |
| Usuários que estão no lobby      | LobbySchema         | ws_lobbyPlayersUpdate  |
| Amigos online                    | FriendAccountSchema | ws_userStatusChange    |
| Usuário que convidou (caso haja) | ?                   | ws_lobbyInviteAccepted |

## [Add WS ao sair de um lobby](https://github.com/3C-gg/reload-backend/issues/72)

| Pra quem?                   | Payload             | Action                |
| --------------------------- | ------------------- | --------------------- |
| Usuários que estão no lobby | LobbySchema         | ws_lobbyPlayersUpdate |
| Amigos online               | FriendAccountSchema | ws_userStatusChange   |

## [Add WS ao criar convite](https://github.com/3C-gg/reload-backend/issues/73)

| Pra quem?         | Payload | Action                 |
| ----------------- | ------- | ---------------------- |
| Usuário convidado | ?       | ws_lobbyInviteReceived |

## [Add WS ao alterar tipo/modo de lobby](https://github.com/3C-gg/reload-backend/issues/74)

| Pra quem?                   | Payload     | Action         |
| --------------------------- | ----------- | -------------- |
| Usuários que estão no lobby | LobbySchema | ws_lobbyUpdate |
| Amigos online               | LobbySchema | ws_lobbyUpdate |
