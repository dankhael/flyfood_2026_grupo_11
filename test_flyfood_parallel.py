"""
Testes para o Projeto FlyFood (versão paralela).

Mesma bateria de testes de test_flyfood.py, apontando para flyfood_parallel.
A API pública é idêntica, então os testes não precisam mudar - apenas o import.
"""

import os
import tempfile
import pytest

from flyfood_parallel import (
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

    def test_escalabilidade_ate_15_entregas(self):
        """
        Teste de escalabilidade com até 15 entregas.

        Para cada número de entregas (1-15):
        - Cria uma grade com R no centro e pontos distribuídos
        - Exibe a grade visualmente
        - Resolve o TSP com força bruta paralela/otimizada
        - Registra tempo, melhor rota e custo

        ATENÇÃO: n=14 e n=15 levam tempo considerável mesmo na versão paralela.
        Com numpy+numba instalados (`pip install numpy numba`) cada nível é
        executado em minutos. Sem eles, n=15 pode levar horas.
        """
        import time

        print("\n" + "=" * 80)
        print("TESTE DE ESCALABILIDADE (PARALELO) - TSP COM ATÉ 15 ENTREGAS")
        print("=" * 80)

        # Distribuição de pontos em espiral para melhor cobertura da grade 6x6.
        # R fica em (2, 2); as 15 entregas preenchem o anel externo e o centro.
        pontos_espiral = [
            (1, 1), (1, 2), (1, 3), (1, 4),  # linha 1
            (2, 4), (3, 4), (4, 4),          # coluna 4
            (4, 3), (4, 2), (4, 1),          # linha 4
            (3, 1), (2, 1),                  # coluna 1
            (3, 2),                          # centro extra
            (2, 3),                          # centro extra (lado direito de R)
            (1, 5),                          # canto superior direito estendido
        ]

        tamanho_grade = 6  # Grade 6x6 para acomodar até 15 entregas
        centro = (2, 2)    # Posição de R

        resultados = []

        for num_entregas in range(1, 16):
            print(f"\n{'-' * 80}")
            print(f"TESTE {num_entregas}: {num_entregas} ENTREGA(S)")
            print(f"{'-' * 80}")

            # Criar pontos de entrega (letras de A a O para até 15)
            letras_entrega = [chr(ord('A') + i) for i in range(num_entregas)]

            # Construir matriz com pontos em posições específicas
            matriz = [["0"] * tamanho_grade for _ in range(tamanho_grade)]
            matriz[centro[0]][centro[1]] = "R"

            pontos_dict = {"R": centro}
            for i, letra in enumerate(letras_entrega):
                pos = pontos_espiral[i]
                matriz[pos[0]][pos[1]] = letra
                pontos_dict[letra] = pos

            # Exibir grade
            print("\nGRADE:")
            for i, linha in enumerate(matriz):
                print(f"  {i} | " + " | ".join(f"{elem:^3}" for elem in linha))
            print("    +" + "-+-" * tamanho_grade)
            print("      " + "   ".join(str(i) for i in range(tamanho_grade)))

            print(f"\nPontos:")
            print(f"  Origem (R): {pontos_dict['R']}")
            for letra in letras_entrega:
                print(f"  {letra}: {pontos_dict[letra]}")

            # Resolver TSP
            print(f"\nResolvendo ({num_entregas}! = {__import__('math').factorial(num_entregas)} permutações)...")
            inicio = time.perf_counter()
            melhor_rota, menor_custo = encontrar_menor_rota(pontos_dict)
            tempo_decorrido = (time.perf_counter() - inicio) * 1000  # em ms

            resultado_formatado = formatar_resultado(melhor_rota)

            # Exibir resultados
            print(f"\n✓ RESULTADO:")
            print(f"  Melhor rota: {resultado_formatado}")
            print(f"  Custo total: {menor_custo} dronômetros")
            print(f"  Tempo: {tempo_decorrido:.3f} ms")

            # Validação
            assert set(melhor_rota) == set(letras_entrega), \
                f"Rota não contém todos os pontos de entrega"
            assert menor_custo == calcular_custo_rota(melhor_rota, pontos_dict), \
                f"Custo calculado incorretamente"

            # Guardar resultado
            resultados.append({
                "entregas": num_entregas,
                "rota": resultado_formatado,
                "custo": menor_custo,
                "tempo_ms": tempo_decorrido,
            })

        # Exibir resumo geral
        print(f"\n{'=' * 80}")
        print("RESUMO GERAL")
        print(f"{'=' * 80}")
        print(f"{'Entregas':<12} {'Custo':<10} {'Tempo (ms)':<15} {'Rota':<40}")
        print("-" * 80)
        for res in resultados:
            print(f"{res['entregas']:<12} {res['custo']:<10} {res['tempo_ms']:<15.3f} {res['rota']:<40}")

        # Validar crescimento de tempo
        print(f"\n{'=' * 80}")
        print("ANÁLISE DE COMPLEXIDADE")
        print(f"{'=' * 80}")
        for i, res in enumerate(resultados):
            if i > 0 and resultados[i - 1]['tempo_ms'] > 0:
                razao = res['tempo_ms'] / resultados[i - 1]['tempo_ms']
                entregas_razao = res['entregas'] / resultados[i - 1]['entregas']
                print(f"De {resultados[i - 1]['entregas']} → {res['entregas']} entregas: "
                      f"tempo aumentou {razao:.1f}x (esperado ~{entregas_razao:.1f}x para n!)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--durations=3"])
