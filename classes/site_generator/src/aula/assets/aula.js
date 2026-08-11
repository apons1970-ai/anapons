/* Interaction for the lesson activities.
 *
 * The HTML is already complete and readable without this file; everything here is
 * an addition: shuffling, checking answers, revealing the German help, and
 * remembering what has been done. No build step, no dependencies. */

(function () {
  "use strict";

  var CLAVE = "aula:v1:";

  /* ------------------------------------------------------------- utilities */

  function normaliza(texto) {
    return String(texto == null ? "" : texto).trim().toLowerCase().replace(/\s+/g, " ");
  }

  /* Strip accents but keep ñ, which is a letter of its own and not an accent. */
  function sinAcentos(texto) {
    return texto
      .replace(/\u00f1/g, "\u0001")
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .replace(/\u0001/g, "\u00f1");
  }

  /* An answer that is right except for the accents gets its own verdict, so the
     student is told what to fix instead of just being marked wrong. */
  function juzga(valor, respuestas) {
    var escrito = normaliza(valor);
    if (!escrito) return "vacio";
    for (var i = 0; i < respuestas.length; i++) {
      if (normaliza(respuestas[i]) === escrito) return "bien";
    }
    for (var j = 0; j < respuestas.length; j++) {
      if (sinAcentos(normaliza(respuestas[j])) === sinAcentos(escrito)) return "casi";
    }
    return "mal";
  }

  function baraja(elementos) {
    var copia = elementos.slice();
    for (var i = copia.length - 1; i > 0; i--) {
      var j = Math.floor(Math.random() * (i + 1));
      var temporal = copia[i];
      copia[i] = copia[j];
      copia[j] = temporal;
    }
    return copia;
  }

  /* Reorder a container's children in place. */
  function barajaHijos(contenedor) {
    baraja(Array.prototype.slice.call(contenedor.children)).forEach(function (hijo) {
      contenedor.appendChild(hijo);
    });
  }

  function hijos(elemento, selector) {
    return Array.prototype.slice.call(elemento.querySelectorAll(selector));
  }

  function marca(elemento, estado, texto) {
    elemento.className = elemento.className.replace(/\b(bien|casi|mal)\b/g, "").trim();
    if (estado) elemento.className += " " + estado;
    if (texto !== undefined) elemento.textContent = texto;
  }

  /* ------------------------------------------------------------- storage */

  /* Every read and write is guarded: private browsing and blocked storage must
     degrade to "no progress saved", never to a broken page. */
  function guarda(clave, valor) {
    try {
      localStorage.setItem(CLAVE + clave, valor);
    } catch (e) {}
  }

  function lee(clave) {
    try {
      return localStorage.getItem(CLAVE + clave);
    } catch (e) {
      return null;
    }
  }

  function anotaResultado(actividad, aciertos, total) {
    var id = actividad.getAttribute("data-id");
    if (!id) return;
    guarda(id, aciertos + "/" + total);
    actualizaLeccion();
  }

  /* A lesson counts as done when every activity that can be checked is fully
     correct. The semester page only reads this one key per lesson. */
  function actualizaLeccion() {
    var leccion = document.querySelector(".leccion[data-leccion]");
    if (!leccion) return;
    var comprobables = hijos(leccion, '.actividad[data-id]').filter(function (actividad) {
      return ["opcion", "huecos", "orden", "pareja"].indexOf(
        actividad.getAttribute("data-tipo")
      ) !== -1;
    });
    if (!comprobables.length) return;
    var completas = comprobables.every(function (actividad) {
      var valor = lee(actividad.getAttribute("data-id"));
      if (!valor) return false;
      var partes = valor.split("/");
      return partes[0] === partes[1];
    });
    guarda("leccion:" + leccion.getAttribute("data-leccion"), completas ? "hecho" : "empezado");
  }

  function marcaLeccionesHechas() {
    hijos(document, "a.leccion[data-leccion]").forEach(function (enlace) {
      if (lee("leccion:" + enlace.getAttribute("data-leccion")) === "hecho") {
        var insignia = enlace.querySelector(".hecho");
        if (insignia) insignia.hidden = false;
      }
    });
  }

  /* ------------------------------------------------------------- language */

  function preparaIdioma() {
    var boton = document.getElementById("cambiar-idioma");
    if (!boton) return;
    var raiz = document.documentElement;
    var sincroniza = function () {
      boton.setAttribute("aria-pressed", raiz.classList.contains("sin-aleman") ? "false" : "true");
    };
    sincroniza();
    boton.addEventListener("click", function () {
      raiz.classList.toggle("sin-aleman");
      guarda("aleman", raiz.classList.contains("sin-aleman") ? "no" : "si");
      sincroniza();
    });
  }

  /* --------------------------------------------------------------- shared */

  function preparaAcciones(actividad, comprobar, reiniciar) {
    var botonComprobar = actividad.querySelector(".comprobar");
    var botonReiniciar = actividad.querySelector(".reiniciar");
    if (botonComprobar) {
      botonComprobar.addEventListener("click", function () {
        comprobar();
        if (botonReiniciar) botonReiniciar.hidden = false;
      });
    }
    if (botonReiniciar) {
      botonReiniciar.addEventListener("click", function () {
        reiniciar();
        botonReiniciar.hidden = true;
      });
    }
  }

  function puntua(actividad, aciertos, total) {
    var marcador = actividad.querySelector(".marcador");
    if (marcador) {
      marca(
        marcador,
        aciertos === total ? "bien" : aciertos ? "casi" : "mal",
        aciertos + " de " + total + (aciertos === total ? " · ¡muy bien!" : "")
      );
    }
    anotaResultado(actividad, aciertos, total);
  }

  function ocultaAyudas(actividad) {
    hijos(actividad, ".ayuda").forEach(function (ayuda) {
      ayuda.hidden = true;
    });
  }

  /* --------------------------------------------------------------- opcion */

  function preparaOpcion(actividad) {
    var preguntas = hijos(actividad, ".pregunta");

    preguntas.forEach(function (pregunta) {
      var varias = pregunta.getAttribute("data-varias") === "si";
      if (actividad.getAttribute("data-barajar") === "si") {
        barajaHijos(pregunta.querySelector(".opciones"));
      }
      hijos(pregunta, ".opcion").forEach(function (opcion) {
        opcion.addEventListener("click", function () {
          var elegida = opcion.getAttribute("aria-pressed") === "true";
          if (!varias) {
            hijos(pregunta, ".opcion").forEach(function (otra) {
              otra.setAttribute("aria-pressed", "false");
            });
          }
          opcion.setAttribute("aria-pressed", elegida ? "false" : "true");
          marca(pregunta.querySelector(".resultado"), "", "");
        });
      });
    });

    function comprobar() {
      var aciertos = 0;
      preguntas.forEach(function (pregunta) {
        var opciones = hijos(pregunta, ".opcion");
        var elegidas = opciones.filter(function (opcion) {
          return opcion.getAttribute("aria-pressed") === "true";
        });
        var resultado = pregunta.querySelector(".resultado");
        var ayuda = pregunta.querySelector(".ayuda");

        if (!elegidas.length) {
          marca(resultado, "mal", "Elige una respuesta.");
          return;
        }
        var bien = opciones.every(function (opcion) {
          var esperada = opcion.getAttribute("data-correcta") === "si";
          return esperada === (opcion.getAttribute("aria-pressed") === "true");
        });
        opciones.forEach(function (opcion) {
          if (opcion.getAttribute("aria-pressed") !== "true") return;
          marca(opcion, opcion.getAttribute("data-correcta") === "si" ? "bien" : "mal");
        });
        if (bien) {
          aciertos++;
          marca(resultado, "bien", "✓ Correcto");
        } else {
          marca(resultado, "mal", "✗ Todavía no");
          if (ayuda) ayuda.hidden = false;
        }
      });
      puntua(actividad, aciertos, preguntas.length);
    }

    function reiniciar() {
      preguntas.forEach(function (pregunta) {
        hijos(pregunta, ".opcion").forEach(function (opcion) {
          opcion.setAttribute("aria-pressed", "false");
          marca(opcion, "");
        });
        marca(pregunta.querySelector(".resultado"), "", "");
      });
      ocultaAyudas(actividad);
      marca(actividad.querySelector(".marcador"), "", "");
    }

    preparaAcciones(actividad, comprobar, reiniciar);
  }

  /* --------------------------------------------------------------- huecos */

  function preparaHuecos(actividad) {
    var datos = actividad.querySelector("script.respuestas");
    var respuestas;
    try {
      respuestas = JSON.parse(datos.textContent);
    } catch (e) {
      return;
    }
    var frases = hijos(actividad, ".frase");

    frases.forEach(function (frase) {
      hijos(frase, ".hueco").forEach(function (hueco) {
        hueco.addEventListener("input", function () {
          marca(frase, "");
          marca(frase.querySelector(".resultado"), "", "");
        });
      });
    });

    function comprobar() {
      var aciertos = 0;
      frases.forEach(function (frase, indice) {
        var huecos = hijos(frase, ".hueco");
        var resultado = frase.querySelector(".resultado");
        var ayuda = frase.querySelector(".ayuda");
        var esperadas = respuestas[indice] || [];
        var veredictos = huecos.map(function (hueco, posicion) {
          return juzga(hueco.value, esperadas[posicion] || []);
        });

        if (veredictos.indexOf("vacio") !== -1) {
          marca(frase, "mal");
          marca(resultado, "mal", "Completa la frase.");
        } else if (veredictos.indexOf("mal") !== -1) {
          marca(frase, "mal");
          marca(resultado, "mal", "✗ Todavía no");
          if (ayuda) ayuda.hidden = false;
        } else if (veredictos.indexOf("casi") !== -1) {
          marca(frase, "casi");
          marca(resultado, "casi", "Casi: revisa los acentos.");
        } else {
          aciertos++;
          marca(frase, "bien");
          marca(resultado, "bien", "✓ Correcto");
          if (ayuda) ayuda.hidden = false;
        }
      });
      puntua(actividad, aciertos, frases.length);
    }

    function reiniciar() {
      frases.forEach(function (frase) {
        hijos(frase, ".hueco").forEach(function (hueco) {
          hueco.value = "";
        });
        marca(frase, "");
        marca(frase.querySelector(".resultado"), "", "");
      });
      ocultaAyudas(actividad);
      marca(actividad.querySelector(".marcador"), "", "");
    }

    preparaAcciones(actividad, comprobar, reiniciar);
  }

  /* --------------------------------------------------------------- pareja */

  function preparaPareja(actividad) {
    var derecha = actividad.querySelector(".columna.derecha");
    var fichas = hijos(actividad, ".ficha");
    var total = hijos(actividad, ".columna.izquierda .ficha").length;
    var elegida = null;
    var emparejadas = 0;

    if (actividad.getAttribute("data-barajar") === "si") barajaHijos(derecha);

    function limpia() {
      if (elegida) elegida.setAttribute("aria-pressed", "false");
      elegida = null;
    }

    fichas.forEach(function (ficha) {
      var esIzquierda = ficha.parentNode.parentNode.className.indexOf("izquierda") !== -1;
      ficha.addEventListener("click", function () {
        if (esIzquierda) {
          var yaElegida = elegida === ficha;
          limpia();
          if (!yaElegida) {
            elegida = ficha;
            ficha.setAttribute("aria-pressed", "true");
          }
          return;
        }
        if (!elegida) return;

        if (elegida.getAttribute("data-par") === ficha.getAttribute("data-par")) {
          [elegida, ficha].forEach(function (parte) {
            parte.className += " emparejada bien";
            parte.setAttribute("aria-pressed", "false");
          });
          elegida = null;
          emparejadas++;
          var marcador = actividad.querySelector(".marcador");
          marca(
            marcador,
            emparejadas === total ? "bien" : "",
            emparejadas + " de " + total + (emparejadas === total ? " · ¡muy bien!" : "")
          );
          if (emparejadas === total) anotaResultado(actividad, total, total);
        } else {
          marca(ficha, "mal");
          setTimeout(function () {
            marca(ficha, "");
          }, 600);
          limpia();
        }
        actividad.querySelector(".reiniciar").hidden = false;
      });
    });

    actividad.querySelector(".reiniciar").addEventListener("click", function () {
      limpia();
      emparejadas = 0;
      fichas.forEach(function (ficha) {
        ficha.className = "ficha";
        ficha.setAttribute("aria-pressed", "false");
      });
      marca(actividad.querySelector(".marcador"), "", "");
      if (actividad.getAttribute("data-barajar") === "si") barajaHijos(derecha);
      actividad.querySelector(".reiniciar").hidden = true;
    });
  }

  /* ---------------------------------------------------------------- orden */

  function preparaOrden(actividad) {
    var frases = hijos(actividad, ".frase");

    frases.forEach(function (frase) {
      var piezas = frase.querySelector(".piezas");
      var respuesta = frase.querySelector(".respuesta");
      if (actividad.getAttribute("data-barajar") === "si") barajaHijos(piezas);

      hijos(frase, ".pieza").forEach(function (pieza) {
        pieza.addEventListener("click", function () {
          /* One listener, two behaviours: where the piece currently sits decides. */
          (pieza.parentNode === respuesta ? piezas : respuesta).appendChild(pieza);
          marca(frase.querySelector(".resultado"), "", "");
        });
      });
    });

    function comprobar() {
      var aciertos = 0;
      frases.forEach(function (frase) {
        var puestas = hijos(frase.querySelector(".respuesta"), ".pieza");
        var resultado = frase.querySelector(".resultado");
        var ayuda = frase.querySelector(".ayuda");
        var esperadas = hijos(frase, ".pieza").length;

        if (puestas.length < esperadas) {
          marca(resultado, "mal", "Usa todas las palabras.");
          return;
        }
        var bien = puestas.every(function (pieza, posicion) {
          return Number(pieza.getAttribute("data-pieza")) === posicion;
        });
        if (bien) {
          aciertos++;
          marca(resultado, "bien", "✓ Correcto");
          if (ayuda) ayuda.hidden = false;
        } else {
          marca(resultado, "mal", "✗ Todavía no");
        }
      });
      puntua(actividad, aciertos, frases.length);
    }

    function reiniciar() {
      frases.forEach(function (frase) {
        var piezas = frase.querySelector(".piezas");
        hijos(frase.querySelector(".respuesta"), ".pieza").forEach(function (pieza) {
          piezas.appendChild(pieza);
        });
        if (actividad.getAttribute("data-barajar") === "si") barajaHijos(piezas);
        marca(frase.querySelector(".resultado"), "", "");
      });
      ocultaAyudas(actividad);
      marca(actividad.querySelector(".marcador"), "", "");
    }

    preparaAcciones(actividad, comprobar, reiniciar);
  }

  /* ---------------------------------------------------------------- libre */

  function preparaLibre(actividad) {
    var escritura = actividad.querySelector(".escritura");
    var id = actividad.getAttribute("data-id");
    if (escritura && id) {
      var guardado = lee("texto:" + id);
      if (guardado) escritura.value = guardado;
      escritura.addEventListener("input", function () {
        guarda("texto:" + id, escritura.value);
      });
    }

    var boton = actividad.querySelector(".ver-modelo");
    var modelo = actividad.querySelector(".modelo");
    if (boton && modelo) {
      boton.addEventListener("click", function () {
        modelo.hidden = !modelo.hidden;
        boton.setAttribute("aria-expanded", modelo.hidden ? "false" : "true");
        boton.textContent = modelo.hidden ? "Ver un modelo" : "Ocultar el modelo";
      });
    }
  }

  /* ----------------------------------------------------------------- init */

  var preparadores = {
    opcion: preparaOpcion,
    huecos: preparaHuecos,
    pareja: preparaPareja,
    orden: preparaOrden,
    libre: preparaLibre
  };

  function inicia() {
    preparaIdioma();
    marcaLeccionesHechas();
    hijos(document, ".actividad[data-tipo]").forEach(function (actividad) {
      var preparador = preparadores[actividad.getAttribute("data-tipo")];
      if (preparador) preparador(actividad);
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", inicia);
  } else {
    inicia();
  }
})();
