"""
Testes para o Projeto FlyFood.

Cobre os seguintes cenários:
- Leitura de matriz a partir de arquivo
- Cálculo de distância Manhattan
- Cálculo de custo de rota
- Encontrar menor rota (força bruta)
- Casos com 1, 2, 3, 4 e 5 pontos de entrega
- Pontos na mesma linha/coluna
- Pontos nos cantos da matriz
- Matriz grande
- Validação do exemplo do enunciado
"""

import os
import tempfile
import pytest

from flyfood import (
    ler_matriz,
    distancia_manhattan,
    calcular_custo_rota,
    encontrar_menor_rota,
    formatar_resultado,
)


# ---------- Helpers ----------

def criar_arquivo_temp(conteudo):
    """Cria um arquivo temporário com o conteúdo fornecido e retorna o caminho."""
    fd, caminho = tempfile.mkstemp(suffix=".txt")
    with os.fdopen(fd, "w") as f:
        f.write(conteudo)
    return caminho


# ---------- Testes de distância Manhattan ----------

class TestDistanciaManhattan:
    def test_mesma_posicao(self):
        assert distancia_manhattan((0, 0), (0, 0)) == 0

    def test_horizontal(self):
        assert distancia_manhattan((0, 0), (0, 5)) == 5

    def test_vertical(self):
        assert distancia_manhattan((0, 0), (3, 0)) == 3

    def test_diagonal(self):
        assert distancia_manhattan((1, 1), (3, 4)) == 5

    def test_simetria(self):
        a, b = (2, 3), (5, 1)
        assert distancia_manhattan(a, b) == distancia_manhattan(b, a)

    def test_valores_grandes(self):
        assert distancia_manhattan((0, 0), (100, 200)) == 300


# ---------- Testes de leitura de matriz ----------

class TestLerMatriz:
    def test_exemplo_enunciado(self):
        conteudo = "4 5\n0 0 0 0 D\n0 A 0 0 0\n0 0 0 0 C\nR 0 B 0 0\n"
        caminho = criar_arquivo_temp(conteudo)
        try:
            pontos = ler_matriz(caminho)
            assert pontos["R"] == (3, 0)
            assert pontos["A"] == (1, 1)
            assert pontos["B"] == (3, 2)
            assert pontos["C"] == (2, 4)
            assert pontos["D"] == (0, 4)
            assert len(pontos) == 5  # R + 4 entregas
        finally:
            os.unlink(caminho)

    def test_matriz_minima(self):
        conteudo = "2 2\nR A\n0 0\n"
        caminho = criar_arquivo_temp(conteudo)
        try:
            pontos = ler_matriz(caminho)
            assert pontos["R"] == (0, 0)
            assert pontos["A"] == (0, 1)
        finally:
            os.unlink(caminho)

    def test_matriz_uma_linha(self):
        conteudo = "1 5\nR A B C D\n"
        caminho = criar_arquivo_temp(conteudo)
        try:
            pontos = ler_matriz(caminho)
            assert pontos["R"] == (0, 0)
            assert pontos["D"] == (0, 4)
        finally:
            os.unlink(caminho)

    def test_matriz_uma_coluna(self):
        conteudo = "4 1\nR\nA\nB\n0\n"
        caminho = criar_arquivo_temp(conteudo)
        try:
            pontos = ler_matriz(caminho)
            assert pontos["R"] == (0, 0)
            assert pontos["A"] == (1, 0)
            assert pontos["B"] == (2, 0)
        finally:
            os.unlink(caminho)


# ---------- Testes de custo de rota ----------

class TestCalcularCustoRota:
    def test_rota_simples(self):
        pontos = {"R": (0, 0), "A": (0, 2)}
        custo = calcular_custo_rota(("A",), pontos)
        # R(0,0)->A(0,2) = 2, A(0,2)->R(0,0) = 2  => total = 4
        assert custo == 4

    def test_rota_dois_pontos(self):
        pontos = {"R": (0, 0), "A": (1, 0), "B": (2, 0)}
        custo = calcular_custo_rota(("A", "B"), pontos)
        # R->A = 1, A->B = 1, B->R = 2 => total = 4
        assert custo == 4

    def test_rota_inversa_pode_diferir(self):
        pontos = {"R": (0, 0), "A": (1, 0), "B": (0, 3)}
        custo_ab = calcular_custo_rota(("A", "B"), pontos)
        custo_ba = calcular_custo_rota(("B", "A"), pontos)
        # R->A=1, A->B=4, B->R=3 => 8
        # R->B=3, B->A=4, A->R=1 => 8
        # Neste caso são iguais (ida e volta simétricos)
        assert custo_ab == custo_ba == 8


# ---------- Testes do algoritmo principal ----------

class TestEncontrarMenorRota:
    def test_exemplo_enunciado(self):
        """Valida o exemplo do PDF do projeto."""
        pontos = {
            "R": (3, 0),
            "A": (1, 1),
            "B": (3, 2),
            "C": (2, 4),
            "D": (0, 4),
        }
        rota, custo = encontrar_menor_rota(pontos)

        # Verifica que todos os pontos de entrega estão na rota
        assert set(rota) == {"A", "B", "C", "D"}

        # Verifica que o custo é ótimo.
        # Rota ótima: R->B->A->D->C->R = 2 + 3 + 5 + 2 + 6 = 18
        # Ou equivalentes com mesmo custo
        # Vamos calcular manualmente o custo para confirmar
        assert custo == calcular_custo_rota(rota, pontos)

        # Verifica que nenhuma outra permutação tem custo menor
        from itertools import permutations
        entregas = ["A", "B", "C", "D"]
        custo_minimo = min(
            calcular_custo_rota(p, pontos) for p in permutations(entregas)
        )
        assert custo == custo_minimo

    def test_um_ponto(self):
        """Apenas um ponto de entrega - rota trivial."""
        pontos = {"R": (0, 0), "A": (2, 3)}
        rota, custo = encontrar_menor_rota(pontos)
        assert rota == ("A",)
        assert custo == 10  # ida 5 + volta 5

    def test_dois_pontos(self):
        """Dois pontos de entrega."""
        pontos = {"R": (0, 0), "A": (1, 0), "B": (0, 1)}
        rota, custo = encontrar_menor_rota(pontos)
        assert set(rota) == {"A", "B"}
        # R->A->B->R = 1+2+1 = 4  ou R->B->A->R = 1+2+1 = 4
        assert custo == 4

    def test_tres_pontos_em_linha(self):
        """Três pontos em linha reta."""
        pontos = {"R": (0, 0), "A": (0, 1), "B": (0, 2), "C": (0, 3)}
        rota, custo = encontrar_menor_rota(pontos)
        assert set(rota) == {"A", "B", "C"}
        # Melhor rota: R->A->B->C->R = 1+1+1+3 = 6
        assert custo == 6

    def test_pontos_nos_cantos(self):
        """Pontos nos quatro cantos de uma matriz 4x4."""
        pontos = {
            "R": (0, 0),
            "A": (0, 3),
            "B": (3, 3),
            "C": (3, 0),
        }
        rota, custo = encontrar_menor_rota(pontos)
        assert set(rota) == {"A", "B", "C"}
        # Perímetro: R->A->B->C->R = 3+3+3+3 = 12
        # ou R->C->B->A->R = 3+3+3+3 = 12
        assert custo == 12

    def test_cinco_pontos(self):
        """Cinco pontos de entrega."""
        pontos = {
            "R": (0, 0),
            "A": (1, 0),
            "B": (2, 0),
            "C": (0, 1),
            "D": (0, 2),
            "E": (1, 1),
        }
        rota, custo = encontrar_menor_rota(pontos)
        assert set(rota) == {"A", "B", "C", "D", "E"}

        # Verifica otimalidade por força bruta
        from itertools import permutations
        entregas = ["A", "B", "C", "D", "E"]
        custo_minimo = min(
            calcular_custo_rota(p, pontos) for p in permutations(entregas)
        )
        assert custo == custo_minimo

    def test_r_no_centro(self):
        """R no centro da matriz."""
        pontos = {
            "R": (2, 2),
            "A": (0, 0),
            "B": (0, 4),
            "C": (4, 4),
            "D": (4, 0),
        }
        rota, custo = encontrar_menor_rota(pontos)
        assert set(rota) == {"A", "B", "C", "D"}

        from itertools import permutations
        entregas = ["A", "B", "C", "D"]
        custo_minimo = min(
            calcular_custo_rota(p, pontos) for p in permutations(entregas)
        )
        assert custo == custo_minimo

    def test_pontos_adjacentes(self):
        """Todos os pontos adjacentes ao R."""
        pontos = {
            "R": (1, 1),
            "A": (0, 1),
            "B": (1, 0),
            "C": (2, 1),
            "D": (1, 2),
        }
        rota, custo = encontrar_menor_rota(pontos)
        assert set(rota) == {"A", "B", "C", "D"}
        # Cada ponto está a distância 1 de R.
        # Melhor rota circular: custo mínimo = 8 (circuito ótimo)
        assert custo == 8


# ---------- Testes de formatação ----------

class TestFormatarResultado:
    def test_formato_basico(self):
        assert formatar_resultado(("A", "B", "C")) == "A B C"

    def test_ponto_unico(self):
        assert formatar_resultado(("A",)) == "A"

    def test_cinco_pontos(self):
        assert formatar_resultado(("A", "D", "C", "B", "E")) == "A D C B E"


# ---------- Teste de integração (leitura de arquivo + resolução) ----------

class TestIntegracao:
    def test_arquivo_exemplo_completo(self):
        """Teste de integração completo com o exemplo do enunciado."""
        conteudo = "4 5\n0 0 0 0 D\n0 A 0 0 0\n0 0 0 0 C\nR 0 B 0 0\n"
        caminho = criar_arquivo_temp(conteudo)
        try:
            pontos = ler_matriz(caminho)
            rota, custo = encontrar_menor_rota(pontos)
            resultado = formatar_resultado(rota)

            # Todos os pontos devem estar na resposta
            for ponto in ["A", "B", "C", "D"]:
                assert ponto in resultado

            # R não deve estar na resposta
            assert "R" not in resultado
        finally:
            os.unlink(caminho)

    def test_arquivo_dois_pontos(self):
        conteudo = "3 3\n0 0 A\nR 0 0\n0 B 0\n"
        caminho = criar_arquivo_temp(conteudo)
        try:
            pontos = ler_matriz(caminho)
            rota, custo = encontrar_menor_rota(pontos)
            assert set(rota) == {"A", "B"}
        finally:
            os.unlink(caminho)

    def test_arquivo_matriz_grande(self):
        """Matriz 6x6 com 4 pontos."""
        linhas = ["6 6"]
        matriz = [["0"] * 6 for _ in range(6)]
        matriz[0][0] = "R"
        matriz[0][5] = "A"
        matriz[5][0] = "B"
        matriz[5][5] = "C"
        matriz[2][3] = "D"
        for row in matriz:
            linhas.append(" ".join(row))
        conteudo = "\n".join(linhas) + "\n"

        caminho = criar_arquivo_temp(conteudo)
        try:
            pontos = ler_matriz(caminho)
            assert pontos["R"] == (0, 0)
            assert pontos["A"] == (0, 5)
            assert pontos["B"] == (5, 0)
            assert pontos["C"] == (5, 5)
            assert pontos["D"] == (2, 3)

            rota, custo = encontrar_menor_rota(pontos)
            assert set(rota) == {"A", "B", "C", "D"}

            # Verifica otimalidade
            from itertools import permutations
            entregas = ["A", "B", "C", "D"]
            custo_minimo = min(
                calcular_custo_rota(p, pontos) for p in permutations(entregas)
            )
            assert custo == custo_minimo
        finally:
            os.unlink(caminho)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--durations=3"])
