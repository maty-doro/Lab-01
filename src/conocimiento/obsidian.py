from __future__ import annotations

from abc import ABC, abstractmethod
from collections import defaultdict
from pathlib import Path

from src.config import DIR_VAULT
from src.conocimiento.utilidades import enlace_obsidian, slugify


class EscritorObsidian(ABC):

    @abstractmethod
    def escribir_noticia(self, data: dict) -> Path:
        pass

    @abstractmethod
    def escribir_entidades(self, noticias: list[dict]) -> None:
        pass

    @abstractmethod
    def escribir_indice(self, noticias: list[dict]) -> Path:
        pass

    @abstractmethod
    def escribir_vault(self, noticias: list[dict]) -> None:
        pass


class EscritorVaultObsidian(EscritorObsidian):

    CARPETAS = [
        "Noticias",
        "Delitos",
        "Personas",
        "Organizaciones",
        "Lugares",
        "Objetos",
        "Relaciones",
    ]

    def __init__(self, vault: Path = DIR_VAULT) -> None:
        self.vault = vault

    def _asegurar_carpetas(self) -> None:
        self.vault.mkdir(parents=True, exist_ok=True)
        for carpeta in self.CARPETAS:
            (self.vault / carpeta).mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _extraer_texto(item: any) -> str:
        if isinstance(item, dict):
            return str(item.get("nombre") or item.get("tipo") or "").strip()
        if item is not None:
            return str(item).strip()
        return ""

    def _wiki_link(self, texto: str) -> str:
        nombre_limpio = (texto or "").strip()
        if not nombre_limpio:
            return ""
        slug = slugify(nombre_limpio)
        if slug == nombre_limpio:
            return enlace_obsidian(slug)
        return f"[[{slug}|{nombre_limpio}]]"

    def escribir_noticia(self, data: dict) -> Path:
        id_noticia = data.get("id_noticia", "N000")
        titulo = data.get("titulo", "Sin titulo")
        fecha = data.get("fecha_publicacion") or ""
        fuente = data.get("fuente", "")
        url = data.get("url", "")
        resumen = data.get("resumen", "")

        ruta = self.vault / "Noticias" / f"{id_noticia}.md"

        lineas: list[str] = [
            "---",
            f"id: {id_noticia}",
            f'titulo: "{titulo}"',
            f"fecha_publicacion: {fecha}",
            f"fuente: {fuente}",
            f"url: {url}",
            "tipo: Noticia",
            "---",
            "",
            f"# {titulo}",
            "",
            "## Resumen",
            resumen or "Sin resumen disponible.",
            "",
        ]

        delitos = [self._extraer_texto(d) for d in (data.get("delitos") or []) if self._extraer_texto(d)]
        lineas.append("## Delitos")
        if delitos:
            for d in delitos:
                lineas.append(f"- {self._wiki_link(d)}")
        else:
            lineas.append("_No se mencionan delitos explícitos._")
        lineas.append("")

        personas = data.get("personas") or []
        lineas.append("## Personas")
        if personas:
            for p in personas:
                if isinstance(p, dict):
                    nombre = self._extraer_texto(p.get("nombre"))
                    rol = self._extraer_texto(p.get("rol"))
                    rol_str = f" ({rol})" if rol else ""
                    if nombre:
                        lineas.append(f"- {self._wiki_link(nombre)}{rol_str}")
                else:
                    nom = self._extraer_texto(p)
                    if nom:
                        lineas.append(f"- {self._wiki_link(nom)}")
        else:
            lineas.append("_No se mencionan personas._")
        lineas.append("")

        organizaciones = [self._extraer_texto(o) for o in (data.get("organizaciones") or []) if self._extraer_texto(o)]
        lineas.append("## Organizaciones")
        if organizaciones:
            for org in organizaciones:
                lineas.append(f"- {self._wiki_link(org)}")
        else:
            lineas.append("_No se mencionan organizaciones._")
        lineas.append("")

        lugares = [self._extraer_texto(l) for l in (data.get("lugares") or []) if self._extraer_texto(l)]
        lineas.append("## Lugares")
        if lugares:
            for lug in lugares:
                lineas.append(f"- {self._wiki_link(lug)}")
        else:
            lineas.append("_No se mencionan lugares._")
        lineas.append("")

        objetos = data.get("objetos") or []
        lineas.append("## Objetos")
        if objetos:
            for obj in objetos:
                if isinstance(obj, dict):
                    nombre_obj = self._extraer_texto(obj.get("nombre") or "objeto")
                    tipo_obj = self._extraer_texto(obj.get("tipo"))
                    cant = obj.get("cantidad")
                    unidad = obj.get("unidad")
                    detalle = f" - Tipo: {tipo_obj}" if tipo_obj else ""
                    if cant is not None:
                        detalle += f", Cantidad: {cant} {unidad or ''}".strip()
                    if nombre_obj:
                        lineas.append(f"- {self._wiki_link(nombre_obj)}{detalle}")
                else:
                    nom = self._extraer_texto(obj)
                    if nom:
                        lineas.append(f"- {self._wiki_link(nom)}")
        else:
            lineas.append("_No se mencionan objetos._")
        lineas.append("")

        relaciones = data.get("relaciones") or []
        lineas.append("## Relaciones")
        if relaciones:
            for rel in relaciones:
                if isinstance(rel, dict):
                    orig = self._extraer_texto(rel.get("origen"))
                    t_rel = self._extraer_texto(rel.get("tipo") or "RELACIONADO_CON")
                    dest = self._extraer_texto(rel.get("destino"))
                    if orig and dest:
                        lineas.append(f"- {self._wiki_link(orig)} --[{t_rel}]--> {self._wiki_link(dest)}")
        else:
            lineas.append("_No se identificaron relaciones explícitas._")
        lineas.append("")

        ruta.write_text("\n".join(lineas), encoding="utf-8")
        return ruta

    def escribir_entidades(self, noticias: list[dict]) -> None:
        idx_delitos: dict[str, dict[str, set[str]]] = defaultdict(lambda: {
            "noticias": set(), "personas": set(), "organizaciones": set(), "lugares": set()
        })
        idx_personas: dict[str, dict[str, any]] = defaultdict(lambda: {
            "noticias": set(), "roles": set(), "delitos": set(), "organizaciones": set()
        })
        idx_organizaciones: dict[str, dict[str, set[str]]] = defaultdict(lambda: {
            "noticias": set(), "delitos": set(), "lugares": set()
        })
        idx_lugares: dict[str, dict[str, set[str]]] = defaultdict(lambda: {
            "noticias": set(), "delitos": set(), "organizaciones": set()
        })
        idx_objetos: dict[str, set[str]] = defaultdict(set)

        for noticia in noticias:
            nid = noticia.get("id_noticia", "")
            if not nid:
                continue

            delitos = [self._extraer_texto(d) for d in (noticia.get("delitos") or []) if self._extraer_texto(d)]
            lugares = [self._extraer_texto(l) for l in (noticia.get("lugares") or []) if self._extraer_texto(l)]
            organizaciones = [self._extraer_texto(o) for o in (noticia.get("organizaciones") or []) if self._extraer_texto(o)]

            personas_data = []
            for p in noticia.get("personas") or []:
                if isinstance(p, dict):
                    nom = self._extraer_texto(p.get("nombre"))
                    rol = self._extraer_texto(p.get("rol"))
                    if nom:
                        personas_data.append((nom, rol))
                else:
                    nom = self._extraer_texto(p)
                    if nom:
                        personas_data.append((nom, ""))

            for d in delitos:
                idx_delitos[d]["noticias"].add(nid)
                idx_delitos[d]["lugares"].update(lugares)
                idx_delitos[d]["organizaciones"].update(organizaciones)
                for nom, _ in personas_data:
                    idx_delitos[d]["personas"].add(nom)

            for nom, rol in personas_data:
                idx_personas[nom]["noticias"].add(nid)
                if rol:
                    idx_personas[nom]["roles"].add(rol)
                idx_personas[nom]["delitos"].update(delitos)
                idx_personas[nom]["organizaciones"].update(organizaciones)

            for org in organizaciones:
                idx_organizaciones[org]["noticias"].add(nid)
                idx_organizaciones[org]["delitos"].update(delitos)
                idx_organizaciones[org]["lugares"].update(lugares)

            for lug in lugares:
                idx_lugares[lug]["noticias"].add(nid)
                idx_lugares[lug]["delitos"].update(delitos)
                idx_lugares[lug]["organizaciones"].update(organizaciones)

            for obj in noticia.get("objetos") or []:
                if isinstance(obj, dict):
                    nombre_obj = self._extraer_texto(obj.get("nombre"))
                else:
                    nombre_obj = self._extraer_texto(obj)
                if nombre_obj:
                    idx_objetos[nombre_obj].add(nid)

        for delito, info in idx_delitos.items():
            ruta = self.vault / "Delitos" / f"{slugify(delito)}.md"
            c = [
                "---",
                "tipo: Delito",
                f'nombre: "{delito}"',
                "---",
                "",
                f"# {delito}",
                "",
                "## Noticias relacionadas",
            ]
            c.extend(f"- {enlace_obsidian(n)}" for n in sorted(info["noticias"]))
            if info["personas"]:
                c.extend(["", "## Personas asociadas"] + [f"- {self._wiki_link(p)}" for p in sorted(info["personas"])])
            if info["organizaciones"]:
                c.extend(["", "## Organizaciones mencionadas"] + [f"- {self._wiki_link(o)}" for o in sorted(info["organizaciones"])])
            if info["lugares"]:
                c.extend(["", "## Lugares donde aparece"] + [f"- {self._wiki_link(l)}" for l in sorted(info["lugares"])])
            c.append("")
            ruta.write_text("\n".join(c), encoding="utf-8")

        for persona, info in idx_personas.items():
            ruta = self.vault / "Personas" / f"{slugify(persona)}.md"
            roles_str = ", ".join(sorted(info["roles"])) if info["roles"] else "No especificado"
            c = [
                "---",
                "tipo: Persona",
                f'nombre: "{persona}"',
                f'roles: "{roles_str}"',
                "---",
                "",
                f"# {persona}",
                "",
                f"**Roles observados:** {roles_str}",
                "",
                "## Noticias donde aparece",
            ]
            c.extend(f"- {enlace_obsidian(n)}" for n in sorted(info["noticias"]))
            if info["delitos"]:
                c.extend(["", "## Delitos asociados"] + [f"- {self._wiki_link(d)}" for d in sorted(info["delitos"])])
            if info["organizaciones"]:
                c.extend(["", "## Organizaciones relacionadas"] + [f"- {self._wiki_link(o)}" for o in sorted(info["organizaciones"])])
            c.append("")
            ruta.write_text("\n".join(c), encoding="utf-8")

        for org, info in idx_organizaciones.items():
            ruta = self.vault / "Organizaciones" / f"{slugify(org)}.md"
            c = [
                "---",
                "tipo: Organizacion",
                f'nombre: "{org}"',
                "---",
                "",
                f"# {org}",
                "",
                "## Noticias relacionadas",
            ]
            c.extend(f"- {enlace_obsidian(n)}" for n in sorted(info["noticias"]))
            if info["delitos"]:
                c.extend(["", "## Delitos vinculados"] + [f"- {self._wiki_link(d)}" for d in sorted(info["delitos"])])
            if info["lugares"]:
                c.extend(["", "## Lugares de operación/mención"] + [f"- {self._wiki_link(l)}" for l in sorted(info["lugares"])])
            c.append("")
            ruta.write_text("\n".join(c), encoding="utf-8")

        for lug, info in idx_lugares.items():
            ruta = self.vault / "Lugares" / f"{slugify(lug)}.md"
            c = [
                "---",
                "tipo: Lugar",
                f'nombre: "{lug}"',
                "---",
                "",
                f"# {lug}",
                "",
                "## Noticias relacionadas",
            ]
            c.extend(f"- {enlace_obsidian(n)}" for n in sorted(info["noticias"]))
            if info["delitos"]:
                c.extend(["", "## Delitos ocurridos"] + [f"- {self._wiki_link(d)}" for d in sorted(info["delitos"])])
            c.append("")
            ruta.write_text("\n".join(c), encoding="utf-8")

        for obj, nids in idx_objetos.items():
            ruta = self.vault / "Objetos" / f"{slugify(obj)}.md"
            c = [
                "---",
                "tipo: Objeto",
                f'nombre: "{obj}"',
                "---",
                "",
                f"# {obj}",
                "",
                "## Noticias donde fue incautado o mencionado",
            ]
            c.extend(f"- {enlace_obsidian(n)}" for n in sorted(nids))
            c.append("")
            ruta.write_text("\n".join(c), encoding="utf-8")

    def escribir_indice(self, noticias: list[dict]) -> Path:
        ruta_indice = self.vault / "00_Indice.md"

        delitos_totales: set[str] = set()
        lugares_totales: set[str] = set()
        personas_totales: set[str] = set()
        organizaciones_totales: set[str] = set()

        for n in noticias:
            delitos_totales.update(self._extraer_texto(d) for d in (n.get("delitos") or []) if self._extraer_texto(d))
            lugares_totales.update(self._extraer_texto(l) for l in (n.get("lugares") or []) if self._extraer_texto(l))
            organizaciones_totales.update(self._extraer_texto(o) for o in (n.get("organizaciones") or []) if self._extraer_texto(o))
            for p in n.get("personas") or []:
                if isinstance(p, dict):
                    nom = self._extraer_texto(p.get("nombre"))
                else:
                    nom = self._extraer_texto(p)
                if nom:
                    personas_totales.add(nom)

        lineas: list[str] = [
            "# Grafo de Conocimiento: Noticias Delictuales",
            "",
            "Bóveda generada automáticamente a partir del pipeline de análisis delictual.",
            "",
            "## Resumen General",
            f"- **Total de noticias procesadas:** {len(noticias)}",
            f"- **Tipos de delitos registrados:** {len(delitos_totales)}",
            f"- **Lugares identificados:** {len(lugares_totales)}",
            f"- **Organizaciones identificadas:** {len(organizaciones_totales)}",
            f"- **Personas nombradas:** {len(personas_totales)}",
            "",
            "---",
            "",
            "## Noticias Procesadas",
        ]

        for n in sorted(noticias, key=lambda x: str(x.get("id_noticia", ""))):
            nid = n.get("id_noticia", "")
            tit = n.get("titulo", "Sin título")
            lineas.append(f"- {enlace_obsidian(nid)}: {tit}")

        lineas.extend(["", "## Delitos Principales"])
        for d in sorted(delitos_totales):
            lineas.append(f"- {self._wiki_link(d)}")

        lineas.extend(["", "## Lugares Relevantes"])
        for l in sorted(lugares_totales):
            lineas.append(f"- {self._wiki_link(l)}")

        lineas.extend(["", "## Organizaciones"])
        for o in sorted(organizaciones_totales):
            lineas.append(f"- {self._wiki_link(o)}")

        lineas.append("")
        ruta_indice.write_text("\n".join(lineas), encoding="utf-8")
        return ruta_indice

    def escribir_vault(self, noticias: list[dict]) -> None:
        self._asegurar_carpetas()
        for data in noticias:
            self.escribir_noticia(data)
        self.escribir_entidades(noticias)
        self.escribir_indice(noticias)