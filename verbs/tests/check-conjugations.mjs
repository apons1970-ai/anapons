/* Checks the conjugation engine against known-correct Spanish.
 *
 * Run with:  node verbs/tests/check-conjugations.mjs
 *
 * This exists because a wrong form here teaches a student wrong Spanish, and
 * nothing else would catch it. Add a case whenever you add a verb whose forms
 * are not obvious, or whenever you touch conjugator.js.
 */
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import vm from "node:vm";

const dir = join(dirname(fileURLToPath(import.meta.url)), "..", "js");
const context = vm.createContext({});
for (const file of ["verbs.js", "conjugator.js"]) {
  vm.runInContext(readFileSync(`${dir}/${file}`, "utf8"), context);
}
// `const` at script top level lives in the lexical scope, not on the global
// object, so copy the three names across explicitly.
vm.runInContext("globalThis.__app = { VERBS, TENSES, Conjugator };", context);
const { VERBS, TENSES, Conjugator } = context.__app;

let fallos = 0;
const esperado = (verbo, tiempo, formas) => {
  const salida = Conjugator.conjugate(verbo)[tiempo];
  const obtenido = salida.join(", ");
  const querido = formas.join(", ");
  if (obtenido !== querido) {
    fallos++;
    console.log(`WRONG  ${verbo} / ${tiempo}`);
    console.log(`         got: ${obtenido}`);
    console.log(`      wanted: ${querido}`);
  }
};

// --- regular verbs, the three conjugations
esperado("hablar", "presente", ["hablo", "hablas", "habla", "hablamos", "habláis", "hablan"]);
esperado("comer", "presente", ["como", "comes", "come", "comemos", "coméis", "comen"]);
esperado("vivir", "presente", ["vivo", "vives", "vive", "vivimos", "vivís", "viven"]);
esperado("hablar", "imperfecto", ["hablaba", "hablabas", "hablaba", "hablábamos", "hablabais", "hablaban"]);
esperado("comer", "indefinido", ["comí", "comiste", "comió", "comimos", "comisteis", "comieron"]);
esperado("hablar", "futuro", ["hablaré", "hablarás", "hablará", "hablaremos", "hablaréis", "hablarán"]);
esperado("hablar", "condicional", ["hablaría", "hablarías", "hablaría", "hablaríamos", "hablaríais", "hablarían"]);

// --- stem changes, which must not reach nosotros/vosotros
esperado("pensar", "presente", ["pienso", "piensas", "piensa", "pensamos", "pensáis", "piensan"]);
esperado("contar", "presente", ["cuento", "cuentas", "cuenta", "contamos", "contáis", "cuentan"]);
esperado("jugar", "presente", ["juego", "juegas", "juega", "jugamos", "jugáis", "juegan"]);
esperado("querer", "presente", ["quiero", "quieres", "quiere", "queremos", "queréis", "quieren"]);
esperado("volver", "presente", ["vuelvo", "vuelves", "vuelve", "volvemos", "volvéis", "vuelven"]);
// ...and must not reach the preterite of a regular stem-changer
esperado("pensar", "indefinido", ["pensé", "pensaste", "pensó", "pensamos", "pensasteis", "pensaron"]);

// --- spelling changes before e
esperado("buscar", "indefinido", ["busqué", "buscaste", "buscó", "buscamos", "buscasteis", "buscaron"]);
esperado("llegar", "indefinido", ["llegué", "llegaste", "llegó", "llegamos", "llegasteis", "llegaron"]);
esperado("empezar", "indefinido", ["empecé", "empezaste", "empezó", "empezamos", "empezasteis", "empezaron"]);
// stem change and spelling change at once
esperado("empezar", "presenteSubj", ["empiece", "empieces", "empiece", "empecemos", "empecéis", "empiecen"]);
esperado("jugar", "presenteSubj", ["juegue", "juegues", "juegue", "juguemos", "juguéis", "jueguen"]);
esperado("buscar", "presenteSubj", ["busque", "busques", "busque", "busquemos", "busquéis", "busquen"]);

// --- imperfect subjunctive, built off the third person plural preterite
esperado("hablar", "imperfectoSubj", ["hablara", "hablaras", "hablara", "habláramos", "hablarais", "hablaran"]);
esperado("ser", "imperfectoSubj", ["fuera", "fueras", "fuera", "fuéramos", "fuerais", "fueran"]);
esperado("hacer", "imperfectoSubj", ["hiciera", "hicieras", "hiciera", "hiciéramos", "hicierais", "hicieran"]);
esperado("leer", "imperfectoSubj", ["leyera", "leyeras", "leyera", "leyéramos", "leyerais", "leyeran"]);

// --- compound tenses and irregular participles
esperado("hablar", "perfecto", ["he hablado", "has hablado", "ha hablado", "hemos hablado", "habéis hablado", "han hablado"]);
esperado("hacer", "perfecto", ["he hecho", "has hecho", "ha hecho", "hemos hecho", "habéis hecho", "han hecho"]);
esperado("volver", "pluscuamperfecto", ["había vuelto", "habías vuelto", "había vuelto", "habíamos vuelto", "habíais vuelto", "habían vuelto"]);
esperado("escribir", "futuroPerfecto", ["habré escrito", "habrás escrito", "habrá escrito", "habremos escrito", "habréis escrito", "habrán escrito"]);

// --- imperatives (tú, usted, nosotros, vosotros, ustedes)
esperado("hablar", "imperativoAfirm", ["habla", "hable", "hablemos", "hablad", "hablen"]);
esperado("comer", "imperativoAfirm", ["come", "coma", "comamos", "comed", "coman"]);
esperado("hacer", "imperativoAfirm", ["haz", "haga", "hagamos", "haced", "hagan"]);
esperado("tener", "imperativoAfirm", ["ten", "tenga", "tengamos", "tened", "tengan"]);
esperado("hablar", "imperativoNeg", ["no hables", "no hable", "no hablemos", "no habléis", "no hablen"]);
esperado("hacer", "imperativoNeg", ["no hagas", "no haga", "no hagamos", "no hagáis", "no hagan"]);

// --- strongly irregular verbs
esperado("ser", "presente", ["soy", "eres", "es", "somos", "sois", "son"]);
esperado("ir", "imperfecto", ["iba", "ibas", "iba", "íbamos", "ibais", "iban"]);
esperado("tener", "futuro", ["tendré", "tendrás", "tendrá", "tendremos", "tendréis", "tendrán"]);
esperado("poder", "condicional", ["podría", "podrías", "podría", "podríamos", "podríais", "podrían"]);
esperado("ver", "indefinido", ["vi", "viste", "vio", "vimos", "visteis", "vieron"]);
esperado("preferir", "presente", ["prefiero", "prefieres", "prefiere", "preferimos", "preferís", "prefieren"]);

// --- every verb, every tense: nothing may come out empty or undefined
let vacios = 0;
for (const verbo of Object.keys(VERBS)) {
  const conj = Conjugator.conjugate(verbo);
  for (const t of TENSES) {
    const formas = conj[t.key];
    if (!Array.isArray(formas) || formas.some((f) => !f || f.includes("undefined") || f === "—")) {
      vacios++;
      console.log(`EMPTY  ${verbo} / ${t.key}: ${JSON.stringify(formas)}`);
    }
  }
}

console.log(`${Object.keys(VERBS).length} verbs x ${TENSES.length} tenses checked`);
console.log(`${fallos} wrong forms, ${vacios} empty tenses`);
process.exit(fallos + vacios === 0 ? 0 : 1);
