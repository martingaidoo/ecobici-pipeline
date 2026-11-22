"""Corre el pipeline completo: bronze -> silver -> gold -> reportes."""
import time

from src import bronze, gold, reportes, silver


def main():
    inicio = time.time()
    for nombre, capa in [("bronze", bronze), ("silver", silver), ("gold", gold), ("reportes", reportes)]:
        print(f"== {nombre}")
        t = time.time()
        capa.ejecutar()
        print(f"   listo en {time.time() - t:.0f} s\n")
    print(f"Pipeline terminado en {time.time() - inicio:.0f} s")


if __name__ == "__main__":
    main()
