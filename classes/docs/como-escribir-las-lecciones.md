# Cómo escribir las lecciones

Esta guía explica cómo se escribe el contenido de la web. No hace falta saber
programar: se escriben archivos de texto normales y la web se construye sola.

---

## 1. Cómo funciona, en dos minutos

Tú escribes **archivos de texto**. Un programa los lee y construye la web.

1. Editas o creas un archivo en GitHub y guardas los cambios (*Commit changes*).
2. GitHub revisa lo que has escrito y construye la web. Tarda un par de minutos.
3. La web queda publicada en **anapons.net**.

Si te equivocas en algo, **la web no cambia**: se queda como estaba, sana y salva.
GitHub te avisa de dónde está el fallo y te dice qué arreglar. No se puede romper
nada de forma permanente, así que escribe con tranquilidad.

---

## 2. Cómo se edita en GitHub

Todo el contenido vive en GitHub. No hace falta instalar nada: se edita desde el
navegador, igual que se rellena un formulario.

La dirección es **github.com/JoseBlanca/anapons**, y para poder escribir tienes que
haber aceptado antes la invitación que te llega por correo.

### Cambiar algo que ya existe

1. Ve abriendo carpetas hasta llegar al archivo: `classes` → `content` → `6G` → …
2. Pulsa el **lápiz ✏️** que hay arriba a la derecha del archivo.
3. Haz los cambios.
4. Pulsa el botón verde **Commit changes…** arriba a la derecha.
5. Se abre un cuadro. Puedes dejar lo que pone o escribir una frase corta que
   explique el cambio (*«añado dos frases con ESTAR»*). Deja marcada la opción
   **Commit directly to the `main` branch**, que es la que viene puesta.
6. Pulsa **Commit changes**. Ya está.

En dos o tres minutos el cambio se ve en la web.

### Añadir una actividad a una lección que ya existe

1. Entra en la carpeta de la lección.
2. Arriba a la derecha: **Add file** → **Create new file**.
3. Escribe el nombre del archivo, con su número delante: `05-mas-practica.md`.
4. Escribe o pega el contenido.
5. **Commit changes…**, igual que antes.

### Crear una lección nueva

Aquí hay un truco que no se ve a simple vista: **GitHub no tiene ningún botón para
crear carpetas**. Las carpetas se crean solas al escribir el nombre del archivo con
barras `/`.

1. **Add file** → **Create new file**.
2. En la casilla del nombre, escribe la ruta completa de un tirón:

   ```
   classes/content/6G/01-primer-semestre-a/05-los-colores/_indice.md
   ```

   Verás que, según escribes cada `/`, GitHub va creando las carpetas.
3. Escribe la ficha de la lección:

   ```markdown
   +++
   titulo = "Los colores"
   titulo_de = "Die Farben"
   categoria = "vocabulario"
   icono = "🎨"
   estado = "borrador"
   +++

   Aquí va la explicación.
   ```
4. **Commit changes…**

Con `estado = "borrador"` la lección no se publica hasta que tú quieras, así que
puedes crearla vacía y llenarla poco a poco. Después, ya dentro de esa carpeta, vas
añadiendo las actividades con **Add file**.

### El editor grande, para cuando haya que hacer varias cosas

Estando en el repositorio, pulsa la tecla del **punto `.`** del teclado. Se abre un
editor completo dentro del navegador, mucho más cómodo para crear varios archivos
seguidos, copiar y pegar entre ellos o cambiar nombres.

Para guardar en ese editor: icono **Source Control** en la columna de la izquierda
(parece un pequeño árbol de ramas), escribe una frase arriba y pulsa el **✓**.

Para volver, cierra la pestaña.

### Saber si ha ido bien

Al lado del último cambio aparece una marca:

| Marca | Qué significa |
|---|---|
| 🟠 círculo naranja | Se está construyendo la web. Espera un minuto |
| ✓ verde | Todo bien, el cambio ya está publicado |
| ✗ roja | Hay algo que arreglar. La web sigue como estaba |

Si sale la roja, pínchala para ver qué falla: en la sección 10 está explicado.

### Ver la web

**anapons.net** — y las clases, en **anapons.net/classes/**.

Si acabas de guardar un cambio y no lo ves, espera un poco y recarga la página con
<kbd>Ctrl</kbd>+<kbd>F5</kbd> (o <kbd>Cmd</kbd>+<kbd>Shift</kbd>+<kbd>R</kbd> en un Mac).

---

## 3. Dónde vive el contenido

Todo está dentro de la carpeta `content/`, en tres niveles:

```
content/
  site.toml                       ← ajustes generales de la web
  6G/                             ← una CLASE
    _indice.md
    01-primer-semestre-a/         ← un SEMESTRE
      _indice.md
      01-la-casa/                 ← una LECCIÓN
        _indice.md                ← de qué va la lección y su explicación
        01-palabras.md            ← una ACTIVIDAD
        02-contrarios.md          ← otra actividad
        03-donde-esta-el-gato.md  ← otra actividad
```

Siempre son esos tres niveles: **clase → semestre → lección**, y dentro de la
lección, las actividades.

En cada carpeta hay un archivo especial llamado **`_indice.md`**, que describe esa
carpeta. Todos los demás archivos de una lección son actividades.

---

## 4. Cómo es un archivo por dentro

Todos los archivos tienen la misma forma: una **ficha** arriba, entre dos líneas
de `+++`, y debajo el **contenido**.

```markdown
+++
tipo = "opcion"
titulo = "Contrarios"
instruccion = "Elige el contrario."
instruccion_de = "Wähle das Gegenteil."
+++

encima de

- [x] debajo de
- [ ] al lado de
```

Reglas de la ficha:

- La primera línea del archivo tiene que ser `+++`, sin nada más.
- Cada dato va en su línea, con el signo `=` en medio.
- **El texto siempre va entre comillas**: `titulo = "La casa"`.
- Las listas van entre corchetes: `etiquetas = ["casa", "localizacion"]`.
- `true` y `false` van sin comillas: `barajar = false`.

---

## 5. Los datos de cada ficha

### `site.toml` (ajustes generales)

| Dato | Para qué sirve |
|---|---|
| `titulo` | El nombre de la web |
| `titulo_de` | El nombre en alemán *(opcional)* |
| `cursos` | Qué clases se publican y en qué orden: `["6G", "7G"]` |

Una clase que no esté en `cursos` **no se publica**, aunque tenga su carpeta. Es
una forma cómoda de preparar una clase sin enseñarla todavía.

### `_indice.md` de una clase o de un semestre

| Dato | Obligatorio | Para qué sirve |
|---|---|---|
| `titulo` | sí | `"Clase 6G"`, `"Primer semestre A"` |
| `titulo_de` | no | El mismo título en alemán |
| `estado` | no | `"borrador"` para no publicarlo todavía |

Lo que escribas **debajo** de la ficha aparece como texto de presentación.

### `_indice.md` de una lección

| Dato | Obligatorio | Para qué sirve |
|---|---|---|
| `titulo` | sí | `"La casa y la localización"` |
| `titulo_de` | no | El título en alemán |
| `categoria` | sí | `"vocabulario"`, `"gramatica"` o `"microbloque"` |
| `icono` | no | Un emoji: `"🏠"` |
| `etiquetas` | no | Para buscar y reutilizar: `["casa", "verbos"]` |
| `estado` | no | `"borrador"` para no publicarla todavía |

La `categoria` decide bajo qué apartado sale la lección en la página del semestre.

Debajo de la ficha va **la explicación de la lección**, que aparece antes de las
actividades. Ahí puedes usar **negrita**, *cursiva* y listas.

### Cualquier actividad

| Dato | Obligatorio | Para qué sirve |
|---|---|---|
| `tipo` | sí | Uno de los siete de la sección 7 |
| `titulo` | sí | El título de la actividad |
| `titulo_de` | no | El título en alemán |
| `instruccion` | no | La orden: *"Completa las frases."* |
| `instruccion_de` | no | La misma orden en alemán |
| `nivel` | no | `"basico"` (por defecto), `"repaso"` o `"desafio"` |
| `barajar` | no | `false` para que las opciones no se mezclen |
| `etiquetas` | no | `["casa", "presente"]` |
| `estado` | no | `"borrador"` para no publicarla todavía |

---

## 6. Escribir en dos idiomas

Los alumnos ven un botón **Deutsch: an / aus** arriba a la derecha. Cuando lo
apagan, desaparece de golpe todo lo que está en alemán. Hay dos maneras de marcar
algo como alemán:

**En la ficha**, añadiendo `_de` al nombre del dato:

```toml
titulo = "La casa y la localización"
titulo_de = "Das Haus und die Ortsangaben"
instruccion = "Completa las frases."
instruccion_de = "Ergänze die Sätze."
```

**En las explicaciones**, con un bloque `::: de`:

```markdown
Con **HAY** hablamos de cosas indeterminadas.

::: de
Mit **HAY** spricht man über unbestimmte Dinge.
:::
```

> **Importante:** un dato acabado en `_de` necesita siempre su pareja en español.
> `titulo_de` sin `titulo` da error.

---

## 7. Los siete tipos de actividad

Hay siete tipos y no se pueden inventar más. Si necesitas uno nuevo, se puede
añadir, pero hay que programarlo.

| `tipo` | Qué hace el alumno |
|---|---|
| `vocabulario` | Lee una lista de palabras con su traducción |
| `opcion` | Elige la respuesta correcta |
| `huecos` | Escribe la palabra que falta |
| `pareja` | Une cada palabra con su pareja |
| `orden` | Coloca las palabras en el orden correcto |
| `libre` | Escribe libremente y compara con un modelo |
| `nota` | No hace nada: es una explicación entre actividades |

### La ayuda en alemán: el símbolo `>`

En casi todos los tipos puedes añadir una línea que empiece por `>`. Es **la ayuda
que aparece cuando el alumno ya ha contestado**: la explicación, la traducción o
la pista. Funciona igual en todos los tipos, así que solo hay que aprenderlo una vez.

---

### `vocabulario` — una lista de palabras

Los títulos con `##` crean grupos. Cada palabra va en su línea, con la traducción
detrás de un `=`. La traducción se puede dejar en blanco.

```markdown
+++
tipo = "vocabulario"
titulo = "La casa"
instruccion = "Busca relaciones entre las palabras."
instruccion_de = "Finde Verbindungen zwischen den Wörtern."
+++

## Lugares

la cocina = die Küche
el baño = das Badezimmer

## Localización

encima de = auf / über
entre ... y ... = zwischen ... und ...
```

---

### `opcion` — elegir la respuesta

La pregunta va sola en una línea. Debajo, las opciones: `- [x]` es la correcta y
`- [ ]` las demás. Hacen falta **al menos dos opciones** y **al menos una correcta**.

```markdown
+++
tipo = "opcion"
titulo = "Busca la pista"
instruccion = "Elige HAY o ESTAR."
instruccion_de = "Wähle HAY oder ESTAR."
barajar = false
+++

una lámpara

- [x] HAY
- [ ] ESTAR

> „una" ist ein unbestimmter Artikel → HAY.

la lámpara

- [ ] HAY
- [x] ESTAR

> „la" ist ein bestimmter Artikel → ESTAR.
```

Cosas útiles:

- **Las opciones se mezclan solas** cada vez que se abre la página, para que el
  alumno no aprenda «la primera siempre es la buena». Si el orden importa (por
  ejemplo `-AR`, `-ER`, `-IR`), pon `barajar = false` en la ficha.
- Si marcas **varias opciones con `[x]`**, el alumno tendrá que elegirlas todas.

> **Cuidado:** cada línea suelta se convierte en una pregunta nueva. Si quieres que
> una pregunta ocupe dos renglones, escríbela en una sola línea aunque sea larga.

---

### `huecos` — completar la frase

Una frase por línea. Lo que va **entre llaves `{ }`** es el hueco que el alumno
tiene que rellenar.

```markdown
+++
tipo = "huecos"
titulo = "Ahora conjuga"
instruccion = "Completa con la forma correcta."
instruccion_de = "Ergänze mit der richtigen Form."
+++

Yo {estudio} español. (estudiar)
> Ich lerne Spanisch.

Mi hermana {lee} mucho. (leer)
> Meine Schwester liest viel.
```

Cosas útiles:

- Puedes poner **varios huecos** en la misma frase.
- **No hace falta escribir la versión sin tilde.** Escribe solo `{está}`. Si el
  alumno escribe `esta`, no se le da por mala: le sale en naranja
  *«Casi: revisa los acentos»*, que es justo lo que tiene que corregir.
- Las mayúsculas y los espacios sobrantes no cuentan: `ESTÁN` vale igual que `están`.
- La barra `|` es para respuestas **de verdad distintas**, no para tildes:
  `{comparten|se reparten}`. La primera es la que se enseña como solución.
- Lo que pongas entre paréntesis es texto normal, útil para dar el infinitivo.

---

### `pareja` — unir parejas

Una pareja por línea, separadas por ` = `. Hacen falta **al menos dos parejas**, y
la columna de la izquierda no puede repetirse.

```markdown
+++
tipo = "pareja"
titulo = "Contrarios"
instruccion = "Relaciona las parejas."
instruccion_de = "Ordne die Gegensätze zu."
+++

- encima de = debajo de
- delante de = detrás de
- dentro de = fuera de
```

La columna de la derecha se mezcla sola. El alumno toca una palabra de la izquierda
y después su pareja de la derecha.

---

### `orden` — ordenar las palabras

Escribe la frase **bien escrita**, una por línea. El programa la despieza y mezcla
las palabras. Hacen falta al menos tres piezas.

```markdown
+++
tipo = "orden"
titulo = "Ordena la frase"
instruccion = "Coloca las palabras en el orden correcto."
instruccion_de = "Bringe die Wörter in die richtige Reihenfolge."
+++

La cama está [al lado de] la ventana.
> Das Bett steht neben dem Fenster.

En mi habitación hay tres fotos.
```

Los **corchetes `[ ]`** mantienen unidas varias palabras que no quieres separar,
como *[al lado de]*: así van juntas en una sola pieza.

---

### `libre` — escribir libremente

El alumno escribe lo que quiera. No se corrige nada, pero puede ver un modelo.

```markdown
+++
tipo = "libre"
titulo = "Describe tú"
instruccion = "Escribe al menos cuatro frases: dos con HAY y dos con ESTAR."
instruccion_de = "Schreibe mindestens vier Sätze."
nivel = "desafio"
+++

Piensa en tu habitación. ¿Qué hay? ¿Dónde está cada cosa?

::: modelo
En la habitación hay una cama. Hay muchos libros.
La cama está junto a la ventana. Los libros están en la estantería.
:::
```

Lo que hay dentro de `::: modelo` está escondido hasta que el alumno pulsa
**Ver un modelo**. Lo que él escriba se guarda en su navegador, así que no lo pierde
si recarga la página.

---

### `nota` — una explicación en medio

Sirve para explicar algo entre dos actividades, en vez de amontonarlo todo arriba.

```markdown
+++
tipo = "nota"
titulo = "Recuerda"
+++

**¿Qué hay? → HAY** · **¿Dónde está / están? → ESTAR**

::: de
Frage nach der Existenz → HAY. Frage nach dem Ort → ESTAR.
:::
```

---

## 8. Los nombres de los archivos

Esta es la parte que más fallos da, así que merece la pena leerla despacio.

**Solo minúsculas, números y guiones.** Nada de tildes, ni eñes, ni espacios, ni
mayúsculas:

| Bien | Mal | Por qué |
|---|---|---|
| `01-la-casa` | `01-La Casa` | Mayúsculas y espacio |
| `02-el-presente` | `02-el-presénte` | Tilde |
| `03-hay-estar` | `03-hay/estar` | Barra |

La única excepción son las carpetas de las clases, que llevan su código tal cual:
`6G`, `7R`.

**El número del principio decide el orden.** `01-`, `02-`, `03-`… Se ordenan por
ese número, no por orden alfabético.

Ese número **no aparece en la dirección de la web**. La carpeta `01-la-casa` se
publica en `anapons.net/classes/6g/primer-semestre-a/la-casa/`. Eso significa que
**puedes renumerar cuando quieras** sin romper los enlaces que ya hayas dado a los
alumnos.

Deja huecos entre los números (10, 20, 30) si crees que vas a intercalar cosas más
adelante. Dos archivos no pueden llevar el mismo número en la misma carpeta.

---

## 9. Trabajos a medias

Para dejar algo empezado sin que lo vean los alumnos, ponle `estado` en la ficha:

```toml
+++
titulo = "El pretérito indefinido"
categoria = "gramatica"
estado = "borrador"
+++
```

Un borrador no se publica, y tampoco se publica nada de lo que tenga dentro. Puedes
dejarlo así todo el tiempo que quieras. Cuando esté listo, borra esa línea o
escribe `estado = "publicado"`.

---

## 10. Cuando algo va mal

Después de guardar un cambio, GitHub revisa lo escrito. Pueden pasar dos cosas:

**Sale una marca verde ✓** — todo bien, la web se actualiza en un par de minutos.

**Sale una marca roja ✗** — hay algo que arreglar. La web **sigue como estaba**;
no se ha estropeado nada. Pincha en la marca roja y verás el aviso, señalando la
línea exacta:

```
01-contrarios.md, línea 9
  error: the question "una lámpara" has no correct option
  mark the right one by changing its [ ] to [x]
```

Los avisos están en inglés, pero siempre dicen **el archivo**, **la línea** y **qué
hacer**. Los más frecuentes:

| Lo que dice | Lo que pasa |
|---|---|
| *has no correct option* | Ninguna opción tiene `[x]` |
| *needs at least two options* | Solo hay una opción |
| *a gap is opened with { but never closed* | Falta cerrar una llave `}` |
| *the sentence "…" has no gap* | Una frase de `huecos` sin llaves |
| *unknown setting "titolo" — did you mean "titulo"?* | Una errata en la ficha |
| *is not a valid name* | Un nombre de archivo con tildes o mayúsculas |
| *is not one of the allowed values* | Por ejemplo `categoria = "Gramatica"` con mayúscula |
| *this folder has no `_indice.md`* | Falta el archivo que describe la carpeta |

Si un aviso no se entiende, dínoslo: la idea es que se entiendan todos, y si uno no
se entiende, es un fallo nuestro y lo cambiamos.

---

## 11. Chuleta

```markdown
+++
tipo = "..."            ← vocabulario, opcion, huecos, pareja, orden, libre, nota
titulo = "..."          ← siempre entre comillas
instruccion = "..."
instruccion_de = "..."  ← en alemán, opcional
nivel = "desafio"       ← basico (normal), repaso, desafio
barajar = false         ← para que no se mezclen las opciones
estado = "borrador"     ← para no publicarlo todavía
+++
```

| Símbolo | Para qué |
|---|---|
| `{respuesta}` | Un hueco que rellenar |
| `{esta\|se encuentra}` | Dos respuestas igual de válidas |
| `- [x]` / `- [ ]` | Opción correcta / incorrecta |
| `izquierda = derecha` | Una pareja, o una palabra y su traducción |
| `[al lado de]` | Palabras que van juntas al ordenar |
| `> ...` | La ayuda en alemán, después de contestar |
| `## Título` | Un grupo de vocabulario |
| `::: de` … `:::` | Un trozo en alemán |
| `::: modelo` … `:::` | La respuesta modelo de una actividad `libre` |

**Las tres reglas que evitan casi todos los fallos:**

1. Nombres de archivo en minúsculas, sin tildes y sin espacios.
2. El texto de la ficha, siempre entre comillas.
3. Cada opción empieza por `- [ ]` o por `- [x]`, y una lleva la `x`.
