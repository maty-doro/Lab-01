"""Persistencia final: red de notas Markdown para Obsidian.

No se usa SQLite, MongoDB ni Neo4j. Cada noticia y cada entidad debe
tener su propia nota, enlazada con [[wiki-links]].
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from collections import defaultdict

from src.config import DIR_VAULT
from src.conocimiento.utilidades import enlace_obsidian,slugify

class EscritorObsidian(ABC):
    """Contrato para generar la bóveda a partir de JSON validado."""

    @abstractmethod
    def escribir_noticia(self, data: dict) -> Path:
        """Crea obsidian_vault/Noticias/{id_noticia}.md con frontmatter y enlaces."""

    @abstractmethod
    def escribir_entidades(self, noticias: list[dict]) -> None:
        """Agrega notas de delitos, personas, organizaciones, lugares y objetos."""

    @abstractmethod
    def escribir_indice(self, noticias: list[dict]) -> Path:
        """Crea obsidian_vault/00_Indice.md."""

    @abstractmethod
    def escribir_vault(self, noticias: list[dict]) -> None:
        """Orquesta noticia + entidades + índice."""


class EscritorVaultObsidian(EscritorObsidian):
    """Implementación objetivo del laboratorio.

    Use src.conocimiento.utilidades.slugify y enlace_obsidian.
    Jerarquía esperada:
        obsidian_vault/
        ├── 00_Indice.md
        ├── Noticias/
        ├── Delitos/
        ├── Personas/
        ├── Organizaciones/
        ├── Lugares/
        ├── Objetos/
        └── Relaciones/
    """

    def __init__(self, vault: Path = DIR_VAULT) -> None:
        self.vault = vault

    def _asegurar_carpetas(self) -> None:
        carpetas = [
            "Noticias",
            "Delitos",
            "Personas",
            "Organizaciones",
            "Lugares",
            "Objetos",
            "Relaciones"
        ]
        self.vault.mkdir(parents=True, exist_ok=True)
        for carpeta in carpetas:
            (self.vault / carpeta).mkdir(parents=True, exist_ok=True)
        

    def escribir_noticia(self, data: dict) -> Path:
        # TODO(alumno): plantilla Markdown con YAML, resumen y [[enlaces]].
        id_noticia = data.get("id_noticia", "N000")
        titulo = data.get("titulo", "Sin titulo")
        fecha = data.get("fecha_publicacion")
        fuente = data.get("fuente", "")
        url = data.get("url", "")
        resumen = data.get("resumen", "")
        
        ruta = self.vault / "Noticias" / f"{id_noticia}.md"

        lineas: list[str] = [
            "---",
            f"id: {id_noticia}",
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
        
        delitos = data.get("delitos") or []
        lineas.append("## Delitos")
        if delitos:
            for delito in delitos:
                lineas.append(f"- {enlace_obsidian(delito)}")
        else:
            lineas.append("_No se mencionan delitos explicitos_")
        lineas.append("")
    
        personas = data.get("personas") or []
        lineas.append("## Personas")
        if personas:
            for p in personas:
                if isinstance(p,dict):
                    nombre = p.get("nombre", "")
                    rol = p.get("rol", "")
                    rol_str = f" ({rol})" if rol else ""
                    lineas.append(f"- {enlace_obsidian(nombre)}{rol_str}")
                else:
                    lineas.append(f"- {enlace_obsidian(str(p))}")
        else:
            lineas.append("_No se mencionan personas_")
        lineas.append("")
        
        organizaciones = data.get("organizaciones") or []
        lineas.append("## Organizaciones")
        if organizaciones:
            for org in organizaciones:
                lineas.append(f"- {enlace_obsidian(org)}")
        else:
            lineas.append("_No se mencionan organizaciones_")
        lineas.append("")
        
        lugares = data.get("lugares") or []
        lineas.append("## Lugares")
        if lugares:
            for lug in lugares:
                lineas.append(f"- {enlace_obsidian(lug)}")
        else:
            lineas.append("_No se mencionan lugares_")
        lineas.append("")
        
        objetos = data.get("objetos") or []
        lineas.append("## Objetos")
        if objetos:
            for obj in objetos:
                if isinstance(obj, dict):
                    nombre_obj = obj.get("nombre", "objeto")
                    tipo_obj = obj.get("tipo", "")
                    cant = obj.get("cantidad")
                    unidad = obj.get("unidad")
                    detalle = f" - Tipo: {tipo_obj}" if tipo_obj else ""
                    if cant is not None:
                        detalle += f", Cantidad: {cant} {unidad or ''}".strip()
                    lineas.append(f"- {enlace_obsidian(nombre_obj)}{detalle}")
                else:
                    lineas.append(f"- {enlace_obsidian(str(obj))}")
        else:
            lineas.append("_No se mencionan objetos._")
        lineas.append("")
        
        relaciones = data.get("relaciones") or []
        lineas.append("## Relaciones")
        if relaciones:
            for rel in relaciones:
                if isinstance(rel, dict):
                    orig = rel.get("origen", "")
                    t_rel = rel.get("tipo", "RELACIONADO_CON")
                    dest = rel.get("destino", "")
                    lineas.append(f"- {enlace_obsidian(orig)} --[{t_rel}]--> {enlace_obsidian(dest)}")
        else:
            lineas.append("_No se identificaron relaciones explícitas._")
        lineas.append("")

        ruta.write_text("\n".join(lineas), encoding="utf-8")
        return ruta
        
        
    def escribir_entidades(self, noticias: list[dict]) -> None:
        idx_delitos: dict[str, set[str]] = defaultdict(set)
        idx_personas: dict[str, dict[str, any]] = defaultdict(lambda: {"noticias": set(), "roles": set()})
        idx_organizaciones: dict[str, set[str]] = defaultdict(set)
        idx_lugares: dict[str, set[str]] = defaultdict(set)
        idx_objetos: dict[str, set[str]] = defaultdict(set)

        for noticia in noticias:
            nid = noticia.get("id_noticia", "")
            if not nid:
                continue

            for d in noticia.get("delitos") or []:
                if d and d.strip():
                    idx_delitos[d.strip()].add(nid)

            for p in noticia.get("personas") or []:
                if isinstance(p, dict):
                    nombre = (p.get("nombre") or "").strip()
                    rol = (p.get("rol") or "").strip()
                    if nombre:
                        idx_personas[nombre]["noticias"].add(nid)
                        if rol:
                            idx_personas[nombre]["roles"].add(rol)
                elif isinstance(p, str) and p.strip():
                    idx_personas[p.strip()]["noticias"].add(nid)

            for org in noticia.get("organizaciones") or []:
                if org and org.strip():
                    idx_organizaciones[org.strip()].add(nid)

            for lug in noticia.get("lugares") or []:
                if lug and lug.strip():
                    idx_lugares[lug.strip()].add(nid)

            for obj in noticia.get("objetos") or []:
                nombre_obj = obj.get("nombre") if isinstance(obj, dict) else str(obj)
                if nombre_obj and nombre_obj.strip():
                    idx_objetos[nombre_obj.strip()].add(nid)

        # 1. Notas de Delitos
        for delito, nids in idx_delitos.items():
            ruta = self.vault / "Delitos" / f"{slugify(delito)}.md"
            contenido = [
                "---",
                "tipo: Delito",
                f"nombre: {delito}",
                "---",
                "",
                f"# {delito}",
                "",
                "## Noticias relacionadas",
            ]
            for n in sorted(nids):
                contenido.append(f"- {enlace_obsidian(n)}")
            contenido.append("")
            ruta.write_text("\n".join(contenido), encoding="utf-8")

        # 2. Notas de Personas
        for persona, info in idx_personas.items():
            ruta = self.vault / "Personas" / f"{slugify(persona)}.md"
            roles_str = ", ".join(sorted(info["roles"])) if info["roles"] else "No especificado"
            contenido = [
                "---",
                "tipo: Persona",
                f"nombre: {persona}",
                f"roles: {roles_str}",
                "---",
                "",
                f"# {persona}",
                "",
                f"**Roles observados:** {roles_str}",
                "",
                "## Noticias relacionadas",
            ]
            for n in sorted(info["noticias"]):
                contenido.append(f"- {enlace_obsidian(n)}")
            contenido.append("")
            ruta.write_text("\n".join(contenido), encoding="utf-8")

        # 3. Notas de Organizaciones
        for org, nids in idx_organizaciones.items():
            ruta = self.vault / "Organizaciones" / f"{slugify(org)}.md"
            contenido = [
                "---",
                "tipo: Organizacion",
                f"nombre: {org}",
                "---",
                "",
                f"# {org}",
                "",
                "## Noticias relacionadas",
            ]
            for n in sorted(nids):
                contenido.append(f"- {enlace_obsidian(n)}")
            contenido.append("")
            ruta.write_text("\n".join(contenido), encoding="utf-8")

        # 4. Notas de Lugares
        for lug, nids in idx_lugares.items():
            ruta = self.vault / "Lugares" / f"{slugify(lug)}.md"
            contenido = [
                "---",
                "tipo: Lugar",
                f"nombre: {lug}",
                "---",
                "",
                f"# {lug}",
                "",
                "## Noticias relacionadas",
            ]
            for n in sorted(nids):
                contenido.append(f"- {enlace_obsidian(n)}")
            contenido.append("")
            ruta.write_text("\n".join(contenido), encoding="utf-8")

        # 5. Notas de Objetos
        for obj, nids in idx_objetos.items():
            ruta = self.vault / "Objetos" / f"{slugify(obj)}.md"
            contenido = [
                "---",
                "tipo: Objeto",
                f"nombre: {obj}",
                "---",
                "",
                f"# {obj}",
                "",
                "## Noticias relacionadas",
            ]
            for n in sorted(nids):
                contenido.append(f"- {enlace_obsidian(n)}")
            contenido.append("")
            ruta.write_text("\n".join(contenido), encoding="utf-8")

    def escribir_indice(self, noticias: list[dict]) -> Path:
        ruta_indice = self.vault / "00_Indice.md"

        delitos_totales: set[str] = set()
        lugares_totales: set[str] = set()
        personas_totales: set[str] = set()

        for n in noticias:
            for d in n.get("delitos") or []:
                if d:
                    delitos_totales.add(d.strip())
            for l in n.get("lugares") or []:
                if l:
                    lugares_totales.add(l.strip())
            for p in n.get("personas") or []:
                nom = p.get("nombre") if isinstance(p, dict) else str(p)
                if nom:
                    personas_totales.add(nom.strip())

        lineas: list[str] = [
            "# Grafo de Conocimiento: Noticias Delictuales",
            "",
            "Bóveda generada automáticamente a partir del pipeline de análisis delictual.",
            "",
            "## Resumen General",
            f"- **Total de noticias:** {len(noticias)}",
            f"- **Tipos de delitos registrados:** {len(delitos_totales)}",
            f"- **Lugares identificados:** {len(lugares_totales)}",
            f"- **Personas nombradas:** {len(personas_totales)}",
            "",
            "---",
            "",
            "## Noticias Procesadas",
        ]

        for n in sorted(noticias, key=lambda x: x.get("id_noticia", "")):
            nid = n.get("id_noticia", "")
            tit = n.get("titulo", "Sin título")
            lineas.append(f"- {enlace_obsidian(nid)}: {tit}")

        lineas.extend([
            "",
            "## Categorías de Consulta Rápida",
            "### Delitos",
        ])
        for d in sorted(delitos_totales):
            lineas.append(f"- {enlace_obsidian(d)}")

        lineas.extend([
            "",
            "### Lugares Principales",
        ])
        for l in sorted(lugares_totales):
            lineas.append(f"- {enlace_obsidian(l)}")

        lineas.append("")

        ruta_indice.write_text("\n".join(lineas), encoding="utf-8")
        return ruta_indice

    def escribir_vault(self, noticias: list[dict]) -> None:
        self._asegurar_carpetas()
        
        for data in noticias:
            self.escribir_noticia(data)
        
        self.escribir_entidades(noticias)
        self.escribir_indice(noticias)
