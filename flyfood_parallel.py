"""
Projeto FlyFood - Versão paralela/otimizada do roteamento de drones.

Mesma lógica algorítmica do flyfood.py (força bruta sobre todas as permutações
dos pontos de entrega), com três otimizações que NÃO alteram o algoritmo:

1. Matriz de distâncias pré-computada (acesso O(1) por índice inteiro, sem
   lookups em dicionário nem chamadas a abs() por iteração).
2. Inner loop opcionalmente acelerado com Numba @njit (quando instalado).
3. Distribuição das permutações entre processos via multiprocessing.Pool,
   fixando o primeiro ponto de entrega e dividindo as (n-1)! permutações
   restantes entre os cores disponíveis.

A API pública é idêntica a flyfood.py para que os testes existentes possam ser
executados sem alteração funcional.
"""

import math
import os
import time
from itertools import permutations
from multiprocessing import Pool, cpu_count

try:
    import numpy as np
    _NUMPY_OK = True
except ImportError:
    _NUMPY_OK = False

try:
    from numba import njit
    _NUMBA_OK = _NUMPY_OK  # numba requires numpy
except ImportError:
    _NUMBA_OK = False

# Limite a partir do qual vale a pena pagar o overhead de spawn de processos.
# Abaixo disso, força bruta serial em Python puro com matriz de distâncias já
# é praticamente instantâneo.
_PARALLEL_THRESHOLD = 9


# ---------- API pública (compatível com flyfood.py) ----------

def ler_matriz(caminho_arquivo):
    """
    Lê o arquivo de entrada e retorna um dicionário com os pontos e suas
    coordenadas (linha, coluna).
    """
    with open(caminho_arquivo, "r") as f:
        linhas = f.read().strip().split("\n")

    num_linhas, _ = map(int, linhas[0].split())
    pontos = {}

    for i in range(1, num_linhas + 1):
        elementos = linhas[i].split()
        for j, elem in enumerate(elementos):
            if elem != "0":
                pontos[elem] = (i - 1, j)

    return pontos


def distancia_manhattan(ponto_a, ponto_b):
    """Distância Manhattan entre dois pontos."""
    return abs(ponto_a[0] - ponto_b[0]) + abs(ponto_a[1] - ponto_b[1])


def calcular_custo_rota(rota, pontos):
    """Custo total de uma rota completa (R -> entregas -> R)."""
    custo = distancia_manhattan(pontos["R"], pontos[rota[0]])
    for i in range(len(rota) - 1):
        custo += distancia_manhattan(pontos[rota[i]], pontos[rota[i + 1]])
    custo += distancia_manhattan(pontos[rota[-1]], pontos["R"])
    return custo


def encontrar_menor_rota(pontos):
    """
    Encontra a rota ótima por força bruta paralela/otimizada.

    Retorna (melhor_rota, menor_custo) com o mesmo formato de flyfood.py:
        melhor_rota: tuple[str, ...] - nomes dos pontos na ordem ótima
        menor_custo: int - custo total em dronômetros
    """
    nomes_entrega = [p for p in pontos if p != "R"]
    n = len(nomes_entrega)

    if n == 0:
        return (), 0
    if n == 1:
        rota = (nomes_entrega[0],)
        return rota, calcular_custo_rota(rota, pontos)

    total = math.factorial(n)
    backend = _escolher_backend(n)
    print(f"[LOG] Força bruta paralela ({backend}): {n}! = {total} rotas a testar")

    # Index 0 = R, índices 1..n = pontos de entrega.
    nomes_indexados = ["R"] + nomes_entrega
    coords = [pontos[name] for name in nomes_indexados]
    dist = _construir_matriz_distancias(coords)

    inicio = time.perf_counter()

    if n >= _PARALLEL_THRESHOLD:
        melhor_custo, melhor_perm = _resolver_paralelo(dist, n)
    else:
        melhor_custo, melhor_perm = _resolver_serial(dist, n)

    duracao = time.perf_counter() - inicio
    print(f"[LOG] Busca concluída em {duracao * 1000:.2f} ms")

    melhor_rota = tuple(nomes_entrega[i - 1] for i in melhor_perm)
    return melhor_rota, int(melhor_custo)


def formatar_resultado(rota):
    """Formata a rota como string separada por espaços."""
    return " ".join(rota)


# ---------- Internals: matriz de distâncias ----------

def _construir_matriz_distancias(coords):
    """
    Constrói a matriz Manhattan (n+1) x (n+1) onde o índice 0 é R.

    Retorna numpy.ndarray int64 se numpy estiver disponível,
    caso contrário list[list[int]] (ambas funcionam por indexação dist[i][j]).
    """
    n = len(coords)
    if _NUMPY_OK:
        dist = np.zeros((n, n), dtype=np.int64)
        for i in range(n):
            for j in range(n):
                dist[i, j] = abs(coords[i][0] - coords[j][0]) + abs(
                    coords[i][1] - coords[j][1]
                )
        return dist

    dist = [[0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            dist[i][j] = abs(coords[i][0] - coords[j][0]) + abs(
                coords[i][1] - coords[j][1]
            )
    return dist


def _escolher_backend(n):
    """Descreve qual caminho será usado (apenas para o log)."""
    if n >= _PARALLEL_THRESHOLD:
        modo = f"multiprocessing x{min(cpu_count(), n)}"
    else:
        modo = "serial"
    if _NUMBA_OK:
        return f"{modo} + numba"
    if _NUMPY_OK:
        return f"{modo} + numpy"
    return f"{modo} + python puro"


# ---------- Internals: caminho serial ----------

def _resolver_serial(dist, n):
    """Força bruta serial usando a matriz pré-computada."""
    if _NUMBA_OK:
        arr = np.arange(1, n + 1, dtype=np.int64)
        custo, perm = _heaps_njit(arr, 0, dist)
        return int(custo), [int(x) for x in perm]
    return _busca_chunk_python(dist, fixados=())


# ---------- Internals: caminho paralelo ----------

def _resolver_paralelo(dist, n):
    """
    Distribui as permutações entre processos fixando o primeiro ponto de entrega.

    Cria n tarefas, cada uma com (n-1)! permutações. O Pool faz balanceamento
    dinâmico, então não importa que n possa ser maior que o número de cores.
    """
    n_workers = min(cpu_count(), n)
    tarefas = [(dist, primeiro, n) for primeiro in range(1, n + 1)]

    with Pool(processes=n_workers) as pool:
        resultados = pool.map(_worker_chunk, tarefas)

    melhor_custo = None
    melhor_perm = None
    for custo, perm in resultados:
        if melhor_custo is None or custo < melhor_custo:
            melhor_custo = custo
            melhor_perm = perm
    return melhor_custo, melhor_perm


def _worker_chunk(args):
    """
    Worker do Pool: itera todas as permutações dos pontos restantes com o
    primeiro ponto fixado, retorna (melhor_custo, melhor_permutacao_completa).
    """
    dist, primeiro, n = args

    if _NUMBA_OK:
        arr = np.empty(n, dtype=np.int64)
        arr[0] = primeiro
        idx = 1
        for k in range(1, n + 1):
            if k != primeiro:
                arr[idx] = k
                idx += 1
        custo, perm = _heaps_njit(arr, 1, dist)
        return int(custo), [int(x) for x in perm]

    return _busca_chunk_python(dist, fixados=(primeiro,), n=n)


def _busca_chunk_python(dist, fixados, n=None):
    """
    Força bruta em Python puro usando itertools.permutations sobre índices
    inteiros. Se `fixados` for não-vazio, esses índices ficam no início da rota
    e apenas o restante é permutado (usado no caminho paralelo).
    """
    if n is None:
        # Inferir n: dist é (n+1) x (n+1) onde o índice 0 é R.
        n = (len(dist) - 1) if isinstance(dist, list) else (dist.shape[0] - 1)

    todos = set(range(1, n + 1))
    restantes = [i for i in todos if i not in fixados]

    melhor_custo = math.inf
    melhor_perm = None

    if fixados:
        # Pré-computa o custo do prefixo fixo (R -> fixados[0] -> ... -> fixados[-1])
        prefix_cost = dist[0][fixados[0]]
        for i in range(len(fixados) - 1):
            prefix_cost += dist[fixados[i]][fixados[i + 1]]
        ultimo_fixado = fixados[-1]

        for perm in permutations(restantes):
            custo = prefix_cost + dist[ultimo_fixado][perm[0]]
            for i in range(len(perm) - 1):
                custo += dist[perm[i]][perm[i + 1]]
            custo += dist[perm[-1]][0]
            if custo < melhor_custo:
                melhor_custo = custo
                melhor_perm = fixados + perm
    else:
        for perm in permutations(restantes):
            custo = dist[0][perm[0]]
            for i in range(len(perm) - 1):
                custo += dist[perm[i]][perm[i + 1]]
            custo += dist[perm[-1]][0]
            if custo < melhor_custo:
                melhor_custo = custo
                melhor_perm = perm

    return int(melhor_custo), list(melhor_perm)


# ---------- Internals: caminho Numba (se instalado) ----------

if _NUMBA_OK:

    @njit(cache=True)
    def _heaps_njit(arr_init, start, dist):
        """
        Algoritmo de Heap iterativo sobre arr_init[start:], com arr_init[:start]
        fixo. Para cada permutação calcula o custo da rota
            R -> arr[0] -> arr[1] -> ... -> arr[n-1] -> R
        e mantém a melhor.

        Retorna (melhor_custo, melhor_arr).
        """
        n = arr_init.shape[0]
        arr = arr_init.copy()
        k = n - start  # tamanho da fatia a permutar

        c = np.zeros(k, dtype=np.int64)

        # Custo da configuração inicial
        cur = dist[0, arr[0]]
        for idx in range(n - 1):
            cur += dist[arr[idx], arr[idx + 1]]
        cur += dist[arr[n - 1], 0]

        best_cost = cur
        best_arr = arr.copy()

        i = 1
        while i < k:
            if c[i] < i:
                if i % 2 == 0:
                    tmp = arr[start]
                    arr[start] = arr[start + i]
                    arr[start + i] = tmp
                else:
                    tmp = arr[start + c[i]]
                    arr[start + c[i]] = arr[start + i]
                    arr[start + i] = tmp

                cost = dist[0, arr[0]]
                for idx in range(n - 1):
                    cost += dist[arr[idx], arr[idx + 1]]
                cost += dist[arr[n - 1], 0]

                if cost < best_cost:
                    best_cost = cost
                    best_arr = arr.copy()

                c[i] += 1
                i = 1
            else:
                c[i] = 0
                i += 1

        return best_cost, best_arr


# ---------- Entry point ----------

def main(caminho_arquivo="entrada.txt"):
    """Função principal: lê a matriz, resolve, imprime e devolve o resultado."""
    inicio_total = time.perf_counter()

    print(f"[LOG] Lendo matriz de '{caminho_arquivo}'...")
    t0 = time.perf_counter()
    pontos = ler_matriz(caminho_arquivo)
    print(f"[LOG] Leitura em {(time.perf_counter() - t0) * 1000:.2f} ms "
          f"({len(pontos)} pontos identificados)")

    entregas = [p for p in pontos if p != "R"]
    print(f"Ponto de origem (R): {pontos['R']}")
    print(f"Pontos de entrega: {', '.join(f'{p} {pontos[p]}' for p in entregas)}")
    print()

    melhor_rota, menor_custo = encontrar_menor_rota(pontos)

    resultado = formatar_resultado(melhor_rota)
    print()
    print(f"Melhor rota: {resultado}")
    print(f"Custo total: {menor_custo} dronômetros")
    print(f"[LOG] Tempo total: {(time.perf_counter() - inicio_total) * 1000:.2f} ms")

    return resultado


if __name__ == "__main__":
    import sys

    arquivo = sys.argv[1] if len(sys.argv) > 1 else "entrada.txt"
    main(arquivo)
