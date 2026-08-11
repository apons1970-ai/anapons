# Verbos — Spanische Verben üben

Conjugation trainer for German-speaking students. Plain HTML, CSS and JavaScript:
no build step and no dependencies, so it is copied into the site as it is.

```
index.html          the page
styles.css
js/verbs.js         the data: VERBS, TENSES and the person labels
js/conjugator.js    the engine that builds every form
js/app.js           the practice UI
tests/              the conjugation checker
```

## Adding a verb

Add an entry to `VERBS` in `js/verbs.js`. Regular verbs need only the translation:

```js
'cantar': { de: 'singen' },
```

Irregular ones override just the forms the engine cannot work out. The fields are
listed at the top of `js/verbs.js`; `stemChange`, `preterite`, `futureStem`,
`presSubj`, `participio`, `gerundio` and `imperTu` cover everything currently used.

**Then run the checker**, and add a case to it for any verb whose forms are not
obvious:

```sh
node verbs/tests/check-conjugations.mjs
```

It verifies known forms and confirms no verb produces an empty tense. It runs in
CI on every push, because a wrong form here teaches a student wrong Spanish and
nothing else would catch it.

## What the engine does and does not handle

Handled: regular `-ar`/`-er`/`-ir`, stem changes (`e-ie`, `o-ue`, `u-ue`, `e-i`)
applied to the right persons only, spelling changes before `e` for `-car`/`-gar`/
`-zar`, compound tenses built with *haber*, the imperfect subjunctive derived from
the third person plural preterite, and both imperatives.

Not handled automatically: consonant changes in `-ger`/`-gir` (*coger* → *coja*),
`-guir`, and `-cer`/`-cir` (*vencer* → *venza*). No such verb is in the list today.
If one is added, give it an explicit `presSubj` — and add a checker case.
