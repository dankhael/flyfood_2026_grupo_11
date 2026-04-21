"""
Projeto FlyFood - Algoritmo de roteamento para drones de entrega.

Resolve o Problema do Caixeiro Viajante (TSP) utilizando força bruta
para encontrar a rota de menor custo (distância Manhattan) entre os
pontos de entrega, partindo e retornando ao ponto R.
"""

import math
import time
from itertools import permutations


def ler_matriz(caminho_arquivo):
    """
    Lê o arquivo de entrada e retorna a dimensão da matriz
    e um dicionário com os pontos e suas coordenadas (linha, coluna).

    Formato do arquivo:
        Linha 1: número de linhas e colunas
        Demais linhas: a matriz com '0' para vazio e letras para pontos

    Retorna:
        pontos (dict): mapeamento nome_do_ponto -> (linha, coluna)
                        Inclui 'R' (origem) e todos os pontos de entrega.
    """
    with open(caminho_arquivo, "r") as f:
        linhas = f.read().strip().split("\n")

    num_linhas, num_colunas = map(int, linhas[0].split())
    pontos = {}

    for i in range(1, num_linhas + 1):
        elementos = linhas[i].split()
        for j, elem in enumerate(elementos):
            if elem != "0":
                pontos[elem] = (i - 1, j)  # i-1 porque a primeira linha é a dimensão

    return pontos


def distancia_manhattan(ponto_a, ponto_b):
    """
    Calcula a distância Manhattan entre dois pontos.

    A distância Manhattan é a soma das diferenças absolutas das
    coordenadas, pois o drone só se move na horizontal e vertical.

    Parâmetros:
        ponto_a (tuple): coordenadas (linha, coluna) do primeiro ponto
        ponto_b (tuple): coordenadas (linha, coluna) do segundo ponto

    Retorna:
        int: distância em dronômetros
    """
    return abs(ponto_a[0] - ponto_b[0]) + abs(ponto_a[1] - ponto_b[1])


def calcular_custo_rota(rota, pontos):
    """
    Calcula o custo total de uma rota completa (R -> entregas -> R).

    Parâmetros:
        rota (tuple/list): sequência de nomes dos pontos de entrega
        pontos (dict): mapeamento nome_do_ponto -> (linha, coluna)

    Retorna:
        int: custo total em dronômetros
    """
    custo = distancia_manhattan(pontos["R"], pontos[rota[0]])

    for i in range(len(rota) - 1):
        custo += distancia_manhattan(pontos[rota[i]], pontos[rota[i + 1]])

    custo += distancia_manhattan(pontos[rota[-1]], pontos["R"])
    return custo


def encontrar_menor_rota(pontos):
    """
    Encontra a rota de menor custo usando força bruta (todas as permutações).

    Testa todas as permutações possíveis dos pontos de entrega e retorna
    a que possui o menor custo total (partindo e retornando a R).

    Parâmetros:
        pontos (dict): mapeamento nome_do_ponto -> (linha, coluna)

    Retorna:
        melhor_rota (tuple): sequência dos pontos de entrega na ordem ótima
        menor_custo (int): custo total da melhor rota em dronômetros
    """
    entregas = [p for p in pontos if p != "R"]
    total_permutacoes = math.factorial(len(entregas))
    print(f"[LOG] Força bruta: {len(entregas)}! = {total_permutacoes} rotas a testar")

    melhor_rota = None
    menor_custo = float("inf")
    rotas_testadas = 0
    atualizacoes = 0

    inicio = time.perf_counter()
    for perm in permutations(entregas):
        custo = calcular_custo_rota(perm, pontos)
        rotas_testadas += 1
        if custo < menor_custo:
            menor_custo = custo
            melhor_rota = perm
            atualizacoes += 1

    duracao = time.perf_counter() - inicio
    print(f"[LOG] Busca concluída em {duracao*1000:.2f} ms "
          f"({rotas_testadas} rotas, {atualizacoes} melhorias do ótimo)")

    return melhor_rota, menor_custo


def formatar_resultado(rota):
    """
    Formata a rota como string separada por espaços.

    Parâmetros:
        rota (tuple): sequência dos pontos de entrega

    Retorna:
        str: pontos separados por espaço (ex: "A D C B")
    """
    return " ".join(rota)


def main(caminho_arquivo="entrada.txt"):
    """
    Função principal que executa o algoritmo FlyFood.

    Lê a matriz do arquivo, encontra a menor rota e exibe o resultado.
    """
    inicio_total = time.perf_counter()

    print(f"[LOG] Lendo matriz de '{caminho_arquivo}'...")
    t0 = time.perf_counter()
    pontos = ler_matriz(caminho_arquivo)
    print(f"[LOG] Leitura em {(time.perf_counter()-t0)*1000:.2f} ms "
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
    print(f"[LOG] Tempo total: {(time.perf_counter()-inicio_total)*1000:.2f} ms")

    return resultado


if __name__ == "__main__":
    import sys

    arquivo = sys.argv[1] if len(sys.argv) > 1 else "entrada.txt"
    main(arquivo)
