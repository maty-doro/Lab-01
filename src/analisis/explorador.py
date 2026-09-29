"""Data Understanding sobre el corpus estructurado."""

from __future__ import annotations

import json
from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd

from src.config import DIR_JSON


class ExploradorDatos:

    def __init__(self, dir_json: Path = DIR_JSON, dir_salida: Path = Path("docs/graficos")) -> None:
        self.dir_json = Path(dir_json)
        self.dir_salida = Path(dir_salida)
        self.dir_salida.mkdir(parents=True, exist_ok=True)
        self.noticias: list[dict] = self._cargar_noticias()

    def _cargar_noticias(self) -> list[dict]:
        archivos = sorted(self.dir_json.glob("*.json"))
        corpus = []
        for arch in archivos:
            try:
                data = json.loads(arch.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    corpus.append(data)
            except Exception:
                continue
        return corpus

    def noticias_por_fuente(self) -> None:
        if not self.noticias:
            return

        fuentes = [n.get("fuente") or "Desconocida" for n in self.noticias]
        serie = pd.Series(fuentes).value_counts()

        plt.figure(figsize=(8, 4.5))
        serie.plot(kind="bar", color="steelblue", edgecolor="black")
        plt.title("Distribución de Noticias por Fuente")
        plt.xlabel("Fuente de Prensa")
        plt.ylabel("Cantidad de Noticias")
        plt.xticks(rotation=30, ha="right")
        plt.tight_layout()
        plt.savefig(self.dir_salida / "noticias_por_fuente.png", dpi=300)
        plt.close()

    def delitos_frecuentes(self, top_n: int = 10) -> None:
        if not self.noticias:
            return

        todos_delitos = []
        for n in self.noticias:
            delitos = n.get("delitos") or []
            todos_delitos.extend([d.strip().capitalize() for d in delitos if d and d.strip()])

        if not todos_delitos:
            return

        serie = pd.Series(todos_delitos).value_counts().head(top_n)

        plt.figure(figsize=(9, 5))
        serie.sort_values().plot(kind="barh", color="coral", edgecolor="black")
        plt.title(f"Top {top_n} Delitos Más Frecuentes")
        plt.xlabel("Menciones")
        plt.ylabel("Tipo de Delito")
        plt.tight_layout()
        plt.savefig(self.dir_salida / "delitos_frecuentes.png", dpi=300)
        plt.close()

    def lugares_frecuentes(self, top_n: int = 10) -> None:
        if not self.noticias:
            return

        todos_lugares = []
        for n in self.noticias:
            lugares = n.get("lugares") or []
            todos_lugares.extend([l.strip().title() for l in lugares if l and l.strip()])

        if not todos_lugares:
            return

        serie = pd.Series(todos_lugares).value_counts().head(top_n)

        plt.figure(figsize=(9, 5))
        serie.sort_values().plot(kind="barh", color="mediumseagreen", edgecolor="black")
        plt.title(f"Top {top_n} Lugares con Mayor Cobertura")
        plt.xlabel("Menciones")
        plt.ylabel("Comuna / Región")
        plt.tight_layout()
        plt.savefig(self.dir_salida / "lugares_frecuentes.png", dpi=300)
        plt.close()

    def campos_faltantes(self) -> None:
        if not self.noticias:
            return

        campos = [
            "id_noticia", "titulo", "fecha_publicacion", "fuente", "url",
            "resumen", "delitos", "personas", "organizaciones", "lugares",
            "objetos", "relaciones"
        ]

        total = len(self.noticias)
        faltantes = {c: 0 for c in campos}

        for n in self.noticias:
            for c in campos:
                val = n.get(c)
                if val is None or val == "" or val == []:
                    faltantes[c] += 1

        porcentajes = {k: (v / total) * 100 for k, v in faltantes.items()}
        serie = pd.Series(porcentajes).sort_values(ascending=False)

        plt.figure(figsize=(10, 5))
        serie.plot(kind="bar", color="indianred", edgecolor="black")
        plt.title("Porcentaje de Campos Faltantes o Vacíos en JSON")
        plt.ylabel("% de Noticias")
        plt.xlabel("Campo")
        plt.ylim(0, 100)
        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()
        plt.savefig(self.dir_salida / "campos_faltantes.png", dpi=300)
        plt.close()

    def evolucion_temporal(self) -> None:
        if not self.noticias:
            return

        fechas = []
        for n in self.noticias:
            f = n.get("fecha_publicacion")
            if f:
                fechas.append(str(f)[:10])

        if not fechas:
            return

        serie_fechas = pd.Series(pd.to_datetime(fechas, errors="coerce")).dropna()
        if serie_fechas.empty:
            return

        agrupado = serie_fechas.dt.to_period("M").value_counts().sort_index()

        plt.figure(figsize=(9, 4.5))
        agrupado.plot(kind="line", marker="o", color="darkslateblue", linewidth=2)
        plt.title("Evolución Temporal de Publicaciones por Mes")
        plt.xlabel("Mes")
        plt.ylabel("Cantidad de Noticias")
        plt.grid(True, linestyle="--", alpha=0.6)
        plt.tight_layout()
        plt.savefig(self.dir_salida / "evolucion_temporal.png", dpi=300)
        plt.close()
        
    def ejecutar(self) -> None:
        if not self.noticias:
            print(f"No se encontraron JSONs en {self.dir_json}.")
            return

        self.noticias_por_fuente()
        self.delitos_frecuentes()
        self.lugares_frecuentes()
        self.campos_faltantes()
        self.evolucion_temporal()