# Websocket workflow

Mapeamento de disparo dos eventos websocket disparados baseados em triggers

## Usuário inativa sua conta

[Add WS ao inativar conta](https://github.com/3C-gg/reload-backend/issues/62)

| Pra quem?                   | Payload             | Action              |
| --------------------------- | ------------------- | ------------------- |
| Usuários que estão no lobby | LobbySchema         | ws_lobbyUpdate      |
| Amigos online               | FriendAccountSchema | ws_userStatusChange |

## Usuário troca de e-mail

[Add WS ao trocar email](https://github.com/3C-gg/reload-backend/issues/70)

| Pra quem?                   | Payload             | Action              |
| --------------------------- | ------------------- | ------------------- |
| Usuários que estão no lobby | LobbySchema         | ws_lobbyUpdate      |
| Amigos online               | FriendAccountSchema | ws_userStatusChange |

## Usuário entra em um lobby

[Add WS ao entrar em um lobby](https://github.com/3C-gg/reload-backend/issues/71)

| Pra quem?                   | Payload             | Action              |
| --------------------------- | ------------------- | ------------------- |
| Usuários que estão no lobby | LobbySchema         | ws_lobbyUpdate      |
| Amigos online               | FriendAccountSchema | ws_userStatusChange |

## Usuário sai de um lobby

[Add WS ao sair de um lobby](https://github.com/3C-gg/reload-backend/issues/72)

| Pra quem?                   | Payload             | Action              |
| --------------------------- | ------------------- | ------------------- |
| Usuários que estão no lobby | LobbySchema         | ws_lobbyUpdate      |
| Amigos online               | FriendAccountSchema | ws_userStatusChange |

## Usuário convida outro usuário pro lobby

[Add WS ao criar convite](https://github.com/3C-gg/reload-backend/issues/73)

| Pra quem?         | Payload           | Action                 |
| ----------------- | ----------------- | ---------------------- |
| Usuário convidado | LobbyInviteSchema | ws_lobbyInviteReceived |

## Usuário rejeita convite para entrar em lobby

| Pra quem?            | Payload           | Action                |
| -------------------- | ----------------- | --------------------- |
| Usuário que convidou | LobbyInviteSchema | ws_lobbyInviteRefused |

## Usuário aceita convite para entrar em lobby

| Pra quem?            | Payload           | Action                 |
| -------------------- | ----------------- | ---------------------- |
| Usuário que convidou | LobbyInviteSchema | ws_lobbyInviteAccepted |

## Usuário troca o tipo ou modo do lobby

[Add WS ao alterar tipo/modo de lobby](https://github.com/3C-gg/reload-backend/issues/74)

| Pra quem?                   | Payload     | Action         |
| --------------------------- | ----------- | -------------- |
| Usuários que estão no lobby | LobbySchema | ws_lobbyUpdate |

## Usuário troca a visibilidade do lobby (public/private)

[Add WS ao alterar visibilidade do lobby](https://github.com/3C-gg/reload-backend/issues/75)

| Pra quem?                   | Payload     | Action         |
| --------------------------- | ----------- | -------------- |
| Usuários que estão no lobby | LobbySchema | ws_lobbyUpdate |
| Amigos online               | LobbySchema | ws_lobbyUpdate |
