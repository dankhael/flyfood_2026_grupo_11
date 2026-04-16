# Documentação do Projeto FlyFood

## 1. Visão Geral

O **FlyFood** é um algoritmo de roteamento para drones de entrega. Dado um mapa (matriz) com pontos de entrega e um ponto de origem **R**, o programa encontra a **rota de menor custo** para que o drone visite todos os pontos de entrega e retorne à origem.

O custo é medido em **dronômetros** (distância Manhattan), pois o drone só se move na horizontal e na vertical — sem diagonais.

Este é essencialmente o **Problema do Caixeiro Viajante (TSP)**, resolvido por **força bruta** (testando todas as permutações possíveis).

---

## 2. Como Executar

### Pré-requisitos
- Python 3.6 ou superior

### Executando o programa
```bash
python flyfood.py entrada.txt
```

### Executando os testes
```bash
python -m pytest test_flyfood.py -v
```

---

## 3. Formato do Arquivo de Entrada

```
<linhas> <colunas>
<matriz com '0' para vazio e letras para pontos>
```

**Exemplo** (`entrada.txt`):
```
4 5
0 0 0 0 D
0 A 0 0 0
0 0 0 0 C
R 0 B 0 0
```

- **R** = origem e retorno do drone (obrigatório)
- **A, B, C, D...** = pontos de entrega
- **0** = posição vazia

---

## 4. Explicação do Código Passo a Passo

O código está organizado em 5 funções, cada uma com uma responsabilidade clara:

### 4.1. `ler_matriz(caminho_arquivo)`

**O que faz:** Lê o arquivo de entrada e extrai as coordenadas de cada ponto.

**Como funciona:**
1. Abre o arquivo e lê todas as linhas.
2. A primeira linha contém as dimensões da matriz (ex: `4 5` = 4 linhas, 5 colunas).
3. Percorre cada célula da matriz. Se o valor não for `"0"`, salva o nome do ponto e sua posição `(linha, coluna)` em um dicionário.

**Exemplo de retorno:**
```python
{
    "R": (3, 0),
    "A": (1, 1),
    "B": (3, 2),
    "C": (2, 4),
    "D": (0, 4)
}
```

### 4.2. `distancia_manhattan(ponto_a, ponto_b)`

**O que faz:** Calcula a distância entre dois pontos usando a **distância Manhattan**.

**Fórmula:**
```
distância = |linha_a - linha_b| + |coluna_a - coluna_b|
```

**Por que Manhattan?** O drone só se move na horizontal e vertical (sem diagonais), então a distância real é a soma das diferenças absolutas das coordenadas.

**Exemplo:**
- De A(1,1) para B(3,2): |1-3| + |1-2| = 2 + 1 = **3 dronômetros**

### 4.3. `calcular_custo_rota(rota, pontos)`

**O que faz:** Calcula o custo total de uma rota completa, incluindo saída de R e retorno a R.

**Como funciona:**
1. Soma a distância de **R** até o **primeiro ponto** da rota.
2. Soma as distâncias entre cada par de pontos consecutivos na rota.
3. Soma a distância do **último ponto** de volta até **R**.

**Exemplo** para a rota `(A, D, C, B)`:
```
R(3,0) → A(1,1) = 3
A(1,1) → D(0,4) = 4
D(0,4) → C(2,4) = 2
C(2,4) → B(3,2) = 3
B(3,2) → R(3,0) = 2
Total = 14 dronômetros
```

### 4.4. `encontrar_menor_rota(pontos)`

**O que faz:** Testa **todas as permutações** possíveis dos pontos de entrega e retorna a de menor custo.

**Como funciona:**
1. Separa os pontos de entrega (tudo que não é R).
2. Gera todas as permutações possíveis (usando `itertools.permutations`).
3. Para cada permutação, calcula o custo total.
4. Guarda a permutação de menor custo.

**Complexidade:** O(n! × n), onde n é o número de pontos de entrega. Para poucos pontos (até ~10), é perfeitamente viável. Para muitos pontos, seria necessário usar heurísticas (como algoritmos genéticos ou nearest neighbor).

| Pontos | Permutações |
|--------|-------------|
| 4      | 24          |
| 5      | 120         |
| 6      | 720         |
| 8      | 40.320      |
| 10     | 3.628.800   |

### 4.5. `formatar_resultado(rota)`

**O que faz:** Converte a tupla da rota em uma string separada por espaços.

**Exemplo:** `("A", "D", "C", "B")` → `"A D C B"`

### 4.6. `main(caminho_arquivo)`

**O que faz:** Orquestra todo o fluxo:
1. Lê a matriz do arquivo
2. Encontra a menor rota
3. Exibe o resultado no terminal

---

## 5. Exemplo Completo de Execução

**Entrada** (`entrada.txt`):
```
4 5
0 0 0 0 D
0 A 0 0 0
0 0 0 0 C
R 0 B 0 0
```

**Saída:**
```
Ponto de origem (R): (3, 0)
Pontos de entrega: D (0, 4), A (1, 1), C (2, 4), B (3, 2)

Melhor rota: A D C B
Custo total: 14 dronômetros
```

**Visualização do trajeto:**
```
         [D]←——←
    [A]→——→——→↗  |
     ↑           ↓
     |          [C]
     |           |
    [R]    [B]←——↙
       ↘→→↗
```

---

## 6. Descrição dos Testes

Os testes estão em `test_flyfood.py` e cobrem **27 casos de teste** organizados em 6 categorias:

### TestDistanciaManhattan (6 testes)
| Teste | O que valida |
|-------|-------------|
| `test_mesma_posicao` | Distância 0 quando os pontos são iguais |
| `test_horizontal` | Movimento puramente horizontal |
| `test_vertical` | Movimento puramente vertical |
| `test_diagonal` | Movimento combinado (horizontal + vertical) |
| `test_simetria` | dist(A,B) == dist(B,A) |
| `test_valores_grandes` | Coordenadas grandes (100, 200) |

### TestLerMatriz (4 testes)
| Teste | O que valida |
|-------|-------------|
| `test_exemplo_enunciado` | Leitura correta do exemplo do PDF |
| `test_matriz_minima` | Matriz 2x2 |
| `test_matriz_uma_linha` | Matriz com apenas 1 linha |
| `test_matriz_uma_coluna` | Matriz com apenas 1 coluna |

### TestCalcularCustoRota (3 testes)
| Teste | O que valida |
|-------|-------------|
| `test_rota_simples` | Rota com 1 ponto (ida e volta) |
| `test_rota_dois_pontos` | Rota com 2 pontos sequenciais |
| `test_rota_inversa_pode_diferir` | Verifica custo em ambas as direções |

### TestEncontrarMenorRota (8 testes)
| Teste | O que valida |
|-------|-------------|
| `test_exemplo_enunciado` | Resultado correto para o exemplo do PDF |
| `test_um_ponto` | Caso trivial com 1 entrega |
| `test_dois_pontos` | 2 pontos de entrega |
| `test_tres_pontos_em_linha` | Pontos alinhados |
| `test_pontos_nos_cantos` | Pontos nos 4 cantos da matriz |
| `test_cinco_pontos` | 5 pontos de entrega |
| `test_r_no_centro` | R no centro (não no canto) |
| `test_pontos_adjacentes` | Todos os pontos vizinhos ao R |

### TestFormatarResultado (3 testes)
Valida a formatação da saída em string.

### TestIntegracao (3 testes)
| Teste | O que valida |
|-------|-------------|
| `test_arquivo_exemplo_completo` | Fluxo completo com o exemplo do PDF |
| `test_arquivo_dois_pontos` | Fluxo completo com 2 pontos |
| `test_arquivo_matriz_grande` | Fluxo completo com matriz 6x6 |

---

## 7. Conceitos Importantes

### Distância Manhattan
Também chamada de "distância de quarteirão" ou "distância L1". É a distância que se percorre andando apenas em linhas retas horizontais e verticais — exatamente como o drone do FlyFood se move.

### Problema do Caixeiro Viajante (TSP)
É um problema clássico de otimização combinatória: dado um conjunto de cidades, qual a rota mais curta que visita todas exatamente uma vez e retorna à origem? A solução por força bruta tem complexidade fatorial, mas funciona bem para poucos pontos.

### Permutações
Uma permutação é um arranjo ordenado de todos os elementos de um conjunto. Para 4 pontos {A, B, C, D}, existem 4! = 24 permutações possíveis. O algoritmo testa cada uma delas para encontrar a de menor custo.
