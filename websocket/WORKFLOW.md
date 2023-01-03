# Websocket workflow

Mapeamento de disparo dos eventos websocket disparados baseados em triggers

## [Add WS ao inativar conta](https://github.com/3C-gg/reload-backend/issues/62)

| Pra quem?                   | Payload?                             |
| --------------------------- | ------------------------------------ |
| Usuários que estão no lobby | Usuário saiu do lobby                |
| Amigos online               | Usuário mudou status (ficou offline) |

## [Add WS ao trocar email](https://github.com/3C-gg/reload-backend/issues/70)

| Pra quem?                   | Payload?                             |
| --------------------------- | ------------------------------------ |
| Usuários que estão no lobby | Usuário saiu do lobby                |
| Amigos online               | Usuário mudou status (ficou offline) |

## [Add WS ao entrar em um lobby](https://github.com/3C-gg/reload-backend/issues/71)

| Pra quem?                        | Payload?                        |
| -------------------------------- | ------------------------------- |
| Usuários que estão no lobby      | Usuário entrou no lobby         |
| Amigos online                    | Usuário mudou status (em grupo) |
| Usuário que convidou (caso haja) | Aceitou o convite               |

## [Add WS ao sair de um lobby](https://github.com/3C-gg/reload-backend/issues/72)

| Pra quem?                   | Payload?                          |
| --------------------------- | --------------------------------- |
| Usuários que estão no lobby | Usuário saiu do lobby             |
| Amigos online               | Usuário mudou status (disponível) |

## [Add WS ao criar convite](https://github.com/3C-gg/reload-backend/issues/73)

| Pra quem?         | Payload?         |
| ----------------- | ---------------- |
| Usuário convidado | Convite recebido |

## [Add WS ao alterar tipo/modo de lobby](https://github.com/3C-gg/reload-backend/issues/74)

| Pra quem?                   | Payload?           |
| --------------------------- | ------------------ |
| Usuários que estão no lobby | Lobby mudou o tipo |
| Amigos online               | Lobby mudou o tipo |
