# Pyconlang
A collection of Python utilities for conlanging.

### Installing
Requires `python >= 3.10`:
```shell
$ pip install git+https://github.com/neta-elad/pyconlang.git
```

No need to install Lexurgy separately, 
since it is bundled with Pyconlang.
However, you do need Java 8 or higher installed
(per Lexurgy's requirements).

## How to Use
Initialize a new project:
```shell
$ pyconlang init -n Simatsan -a Biblaridion simatsan
$ cd simatsan
```

Run an interactive 
[Lexurgy](https://github.com/def-gthill/lexurgy) 
session:
```shell
$ pyconlang repl
```

Compile the reference grammar and lexicon:
```shell
$ pyconlang book compile
```
or continuously watch for changes and re-compile:
```shell
$ pyconlang book watch
```

For more information and help:
```shell
$ pyconlang --help
```

## Book Format
Pyconlang uses 
[Markdown](https://daringfireball.net/projects/markdown/),
Lexurgy,
and its own lexicon file-format 
to generate a reference grammar and lexicon
for your conlang.
The book's style is heavily inspired by
David J. Peterson's template.

Under the hood, Pyconlang uses
[Python-Markdown](https://python-markdown.github.io/)
with several extensions to support
[including files](https://github.com/neurobin/mdx_include)
and [extended markup](https://python-markdown.github.io/extensions/).

Sound changes are defined in `changes.lsc`, 
and applied using Lexurgy.

### Lexicon
Pyconlang's lexicon is defined in `lexicon.txt`.
Each line defines one of three types of records: 
`entry`, `affix`, and `template`.
No line breaks are allowed inside the definition of a single record.

You define basic entries using the `entry` declaration:
```
entry <stone> *apak (n.) stone, pebble 
```

For some entries,
you may want to define
its form in some mid-point
in the conlang's evolution.
This is done using the `@rule` syntax:
```
entry <hard> *apaki@after-palatalization (adj.) hard, strong, stable 
```

When applying sound changes to this entry,
only rules after (and including) `after-palatalization`
will apply.
You may find it useful to create explicit no-op rules
in `changes.lsc`:
```
after-palatalization:
    unchanged
```

Note that spaces are allowed
when defining entries,
so you need not restrict yourself to single words:
```
entry <to eat 27 strawberries> *mata (v.) to eat 27 strawberries, to be gluttonous
```

You can also define affixes, 
to be used when inserting entries:
```
affix .PL *ikim
affix COL. *ma

entry <gravel> <stone>.PL (n.) gravel, a pile of stones
entry <monument> COL.<stone> (n.) monument, memorial site
```
Affixes can also be defined in some mid-point
(using the `@rule` syntax)
or by using compounds (`COL.<pile>`).

Additionally,
you can define lexical sources of affixes,
and a short description:
```
affix .PL *ikim (<big> <pile>) plural suffix for all nouns
```
When there is exactly one lexical source,
you may omit the affix's form:
```
affix .PL (<pile>)
```

Sometimes, a group of entries should be displayed
with a list of forms. 
For example, all nouns show their collective and plural form.
This is accomplished by templates:
```
template &noun $ $.PL COL.$

entry &noun <apple> *saka (n.) apple, any kind of tree-fruit
```

You can see the diagrams for the lexicon syntax
[here](https://htmlpreview.github.io/?https://github.com/neta-elad/pyconlang/blob/main/diagrams.html).

#### Example
Given the sound changes `changes.lsc`:
```
Class vowel {a, e, i, o, u}

palatalization:
    k => ʃ / _ i

after-palatalization:
    unchanged

intervocalic-voicing:
    {p, t, k, s} => {b, d, g, z} / @vowel _ @vowel

romanizer:
    ʃ => sh
```

and the lexicon `lexicon.txt`:
```
template &noun $ $.PL COL.$
    
affix .PL *ikim@after-palatalization (<big> <pile>) plural suffix for all nouns
affix COL. (<pile>)

entry <big> *iki (adj.) big, great
entry <pile> *ma (n.) pile, heap

entry &noun <stone> *apak (n.) stone, pebble
entry <gravel> <stone>.PL (n.) gravel, a pile of stones
entry <monument> COL.<stone> (n.) monument, memorial site
```

The following entries will appear in the book:
> ...
> ## A
> **abagigim** [abagigim] _\*apak_ + _\*ikim_ (n.) gravel, a pile of stones
> 
> **abak**, **abagigim**, **maabak** [abak] _\*apak_ (n.) stone, pebble
> 
> ...
> ## I
> **ishi** [iʃi] _\*iki_ (adj.) big, great
> 
> ...
> ## M
> **ma** [ma] _\*ma_ (n.) pile, heap
>
> **maabak** [maabak] _\*ma_ + _\*apak_ (n.) monument, memorial site
>
> ...

### Markdown Extensions
Inline translations (using the lexicon)
can be inserted between two hash signs:
```
**An example: #*aki@after-palatalization <stone>.PL#.**
```
will turn out as
> **An example: agi abagigim.**



## TODO
- [ ] Complete example project
- [x] Custom error types?
- [ ] ? Combined, general repl
  - [ ] Working with proto-forms
  - [ ] Working with lexicon
    - [ ] Defining words, affixes and templates in session
    - [ ] Saving session
    - [ ] Search for a word
  - [ ] Working with book
    - [ ] Compile
- [ ] More powerful affixes:
  - [ ] Branched affixes (depending on stem phonology / metadata)
  - [ ] Frozen affixes (i.e. affixes defined in the modern language)
  - [ ] Affixes with sound changes (e.g. voice initial consonant)
  - [ ] Standalone affixes
- [ ] `repl`: Interactive session with Lexurgy
  - [x] Enter proto form, get romanized modern form
  - [x] Get phonetic modern form
  - [x] Get simplified (no accents) romanized modern form
  - [x] Traces
  - [x] History
  - [ ] Auto-complete
  - [x] Error handling
- [ ] `evolve`: Evolving forms and auto-glomination
  - [x] Evolve and auto-glominate forms at the correct point of time
  - [x] Handle stress
  - [x] Lexurgy error handling
  - [x] Traces
  - [x] Better cache
  - [ ] Working with deromanizer and custom romanizers
  - [ ] Evolve affixes with empty stem
- [ ] `lexicon`: Interactive lexicon
  - [x] Define word by canonical
  - [ ] Find by canonical, proto, affix, or definition
  - [x] Protos to take affixes as well
  - [x] Batch evolve, using dependency graph?
  - [ ] Better cache
  - [ ] On-the-fly affixes? Syntax for compounding two words without an explicit affix
  - [ ] ? Change the order of canonical and template name, and make record declarations optional
  - [ ] Affixes with empty stem
- [ ] `translator`: Automatic translation according to gloss
  - [x] Evolve each form (with affixes)
  - [x] Match-up forms and glosses
  - [ ] Better cache
  - [ ] Full-text search over everything
  - [ ] Affixes with empty stem
  (proto, modern, phonetic, definitions, etc.) 
  [whoosh](https://whoosh.readthedocs.io/en/latest/parsing.html)
- [ ] `book`: Generate a grammar/lexicon reference with less boilerplate
  - [x] Conlang-to-English lexicon, with entries, affixes and templates:
  - [x] Only rebuild lexicon when changed
  - [ ] Affixes list
  - [ ] Phonology tables
  - [ ] Conjugation tables
  - [x] Inline translation
  - [x] Robust against errors