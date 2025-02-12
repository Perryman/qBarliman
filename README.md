# qBarliman

qBarliman is a cross-platform, python3, Qt6 fork of Barliman, a joint work between [Will Byrd](https://github.com/webyrd/) and [Greg Rosenblatt](https://github.com/gregr).

The goal of this project is to increase availability and expandability of those wanting to learn and experiment with the miniKanren language and relatoinal interpreters.

For more details on Barliman, see the [miniKanren relational interpreter README](minikanren/rel-interp/README.md).

> [!WARNING]
>
> ## STATUS: unstable, not ready for use
>
> - major refactoring in progress
> - see [TODO.md](TODO.md)

---

## Running qBarliman

### Prerequisites

- Python 3.10+
- Chez Scheme

### Clone and install

```sh
git clone https://github.com/perryman/qBarliman.git
cd qBarliman
pip install -r requirements.txt
```

### Run

```sh
python3 qBarliman
```

### DPI

Qt uses your QT_SCALE_FACTOR environment variable for DPI scaling.
The following example launches at 1.5x scale.

```sh
QT_SCALE_FACTOR=1.5 && python qBarliman.py
```

#### Windows

##### Adding to PATH in powershell

```powershell
# Example for Chez Scheme 10.1.0. Adjust the path as needed.
[System.Environment]::SetEnvironmentVariable("PATH", $env:PATH + "C:\Program Files (x86)\Chez Scheme 10.0.1\bin\ti3nt\", [System.EnvironmentVariableTarget]::User)
# Save path to environment variable
$env:PATH = [System.Environment]::GetEnvironmentVariable("PATH", [System.EnvironmentVariableTarget]::User)

```

---

## Project Structure

```sh
├── qBarliman
│   ├── constants.py
│   ├── controllers
│   │   ├── editor_window_controller.py
│   ├── minikanren
│   │   ├── core
│   │   ├── rel-interp
│   │   └── templates
│   ├── operations
│   │   └── run_scheme_operation.py
│   ├── utils
│   │   ├── constrained_splitter.py
│   │   └── iterable_helpers.py
│   └── widgets
│       ├── scheme_editor_text_view.py
│       └── spinner_widget.py
├── qBarliman.py
├── README.md
└── requirements.txt
```

---

### Barliman in action

[Relational Interpreters, Program Synthesis, and Barliman - Code Mesh 2017](https://www.youtube.com/watch?v=RVDCRlW1f1Y)

[Clojure/conj 2016 talk](https://www.youtube.com/watch?v=er_lLvkklsk)

---

## The default "miniScheme" language

(give grammar and semantics for the default language)

As in Scheme, in miniScheme duplicate variable names of definitions at the same scoping level, or duplicate `lambda` or `letrec` bindings, are illegal. However, Barliman does not currently detect these violations. For example, Barliman will not complain about the expression `((lambda (x x) x) 3 4)`, the behavior of which is unspecified. Probably the parser should enforce that the variable names are distinct.

The `lambda` and `letrec` forms do not contain an implicit `begin`.

## The `lambda` form supports multiple arguments, `(lambda (x y z) y)`, and a single "variadic" argument, `(lambda x x)`, but currently doesn't support the full Scheme variadic syntax, `(lambda (x y . z) x)`

## Credits

Thanks to Will Byrd, Greg Rosenblatt, Nada Amin, Michael Ballantyne, among others, for inspiring this fork. See [CREDITS.md](CREDITS.md) for the original project's credits.
