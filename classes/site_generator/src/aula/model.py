"""The in-memory shape of the content tree.

Three fixed levels below the site — curso, semestre, leccion — with activities
inside a lesson. Section 2 of the spec.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .activities import Body
from .blocks import Segment

CATEGORIAS = {"vocabulario", "gramatica", "microbloque"}
NIVELES = {"basico", "repaso", "desafio"}
ESTADOS = {"publicado", "borrador"}


@dataclass
class Actividad:
    slug: str
    path: Path
    tipo: str
    titulo: str
    body: Body
    titulo_de: str = ""
    instruccion: str = ""
    instruccion_de: str = ""
    nivel: str = "basico"
    barajar: bool = False
    etiquetas: list[str] = field(default_factory=list)
    estado: str = "publicado"


@dataclass
class Leccion:
    slug: str
    path: Path
    titulo: str
    categoria: str
    titulo_de: str = ""
    icono: str = ""
    etiquetas: list[str] = field(default_factory=list)
    estado: str = "publicado"
    prose: list[Segment] = field(default_factory=list)
    actividades: list[Actividad] = field(default_factory=list)


@dataclass
class Semestre:
    slug: str
    path: Path
    titulo: str
    titulo_de: str = ""
    estado: str = "publicado"
    prose: list[Segment] = field(default_factory=list)
    lecciones: list[Leccion] = field(default_factory=list)


@dataclass
class Curso:
    slug: str
    codigo: str
    path: Path
    titulo: str
    titulo_de: str = ""
    estado: str = "publicado"
    prose: list[Segment] = field(default_factory=list)
    semestres: list[Semestre] = field(default_factory=list)


@dataclass
class Site:
    version: int
    titulo: str
    base_url: str
    path: Path
    titulo_de: str = ""
    cursos: list[Curso] = field(default_factory=list)

    def walk(self):
        """Yield ``(curso, semestre, leccion)`` for every lesson in the site."""
        for curso in self.cursos:
            for semestre in curso.semestres:
                for leccion in semestre.lecciones:
                    yield curso, semestre, leccion


def lesson_id(curso: Curso, semestre: Semestre, leccion: Leccion) -> str:
    """Stable identifier, used for progress in ``localStorage``. Must not drift."""
    return f"{curso.slug}/{semestre.slug}/{leccion.slug}"
