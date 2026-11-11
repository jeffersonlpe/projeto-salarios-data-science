from __future__ import annotations

from pipeline.graficos import gerar_graficos
from pipeline.ingestao import ingerir
from pipeline.marts import (
    criar_salario_por_cargo,
    criar_salario_por_experiencia,
    criar_salario_por_pais,
    criar_salarios_por_perfil,
)
from pipeline.refinamento import refinar_salarios


def main() -> None:
    print("Iniciando ingestão...")
    ingerir()
    print("Concluído ingestão.")

    print("Iniciando refinamento...")
    refinar_salarios()
    print("Concluído refinamento.")

    print("Iniciando marts...")
    criar_salario_por_cargo()
    criar_salario_por_experiencia()
    criar_salario_por_pais()
    criar_salarios_por_perfil()
    print("Concluído marts.")

    print("Iniciando gráficos...")
    gerar_graficos()
    print("Concluído gráficos.")


if __name__ == "__main__":
    main()
