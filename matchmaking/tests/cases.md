# CASOS

## 1 - Troca simples #1
> user_1 abandona seu lobby sem ninguém e entra no lobby do user_2
```
// estado inicial
lobby user_1
    user_1

lobby user_2
    user_2

// ação
user_1 -> lobby user_2

// estado final
lobby user_1

lobby user_2
    user_2
    user_1
```

## 2 - Troca simples #2
> user_3 abandona o lobby em que está, não é dono e entra no lobby do user_2
```
// estado inicial
lobby user_1
    user_1
    user_3

lobby user_2
    user_2

lobby user_3

// ação
user_3 -> lobby user_2

// estado final
lobby user_1
    user_1

lobby user_2
    user_2
    user_3

lobby user_3
```

## 3 - Convidado sai
> user_3 abandona o lobby em que está e não é dono
```
// estado inicial
lobby user_1
    user_1
    user_3

lobby user_2
    user_2

lobby user_3

// ação
user_3 -> lobby user_2

// estado final
lobby user_1
    user_1

lobby user_2
    user_2

lobby user_3
    user_3
```

## 4 - Troca de dono
> user_1 abandona o seu próprio lobby que tem um outro companheiro e entra no lobby do user_2
```
// estado inicial
lobby user_1
    user_1
    user_3

lobby user_2
    user_2

lobby user_3

// ação
user_1 -> lobby user_2

// estado final
lobby user_1    

lobby user_2
    user_2
    user_1

lobby user_3
    user_3
```

## 5 - Troca de dono #2
> user_1 abandona o seu próprio lobby que tem outros companheiros e entra no lobby do user_2
```
// estado inicial
lobby user_1
    user_1
    user_3
    user_4

lobby user_2
    user_2

lobby user_3

lobby user_4

// ação
user_1 -> lobby user_2

// estado final
lobby user_1    

lobby user_2
    user_2
    user_1

lobby user_3
    user_3
    user_4

lobby user_4
```

## 6 - Dono cancela (sair do próprio lobby)
> user_1 abandona/cancela o seu próprio lobby que tem outros companheiros
```
// estado inicial
lobby user_1
    user_1
    user_3
    user_4

lobby user_2
    user_2

lobby user_3

lobby user_4

// ação
user_1 -> cancela

// estado final
lobby user_1    
    user_1

lobby user_2
    user_2

lobby user_3
    user_3
    user_4

lobby user_4
```

## 7 - Player convidado desloga
> user_3 desloga
```
// estado inicial
lobby user_1
    user_1
    user_3
    user_4

lobby user_2
    user_2

lobby user_3

lobby user_4

// ação
user_3 -> desloga

// estado final
lobby user_1    
    user_1
    user_4

lobby user_2
    user_2 

lobby user_4
```

## 8 - Dono desloga
> user_1 desloga
```
// estado inicial
lobby user_1
    user_1
    user_3
    user_4

lobby user_2
    user_2

lobby user_3

lobby user_4

// ação
user_1 -> desloga

// estado final
lobby user_2
    user_2

lobby user_3
    user_3 
    user_4   

lobby user_4
```
