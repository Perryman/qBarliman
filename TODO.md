# TODO ROADMAP

## Refactor Python Code
- [X] Refactor the `editor_window_controller.py` into smaller modules.
  - [ ] Refactor repeated code into abstracted functions.
- [ ] Move constants and templates into `constants.py`.
  - [ ] Refactor templates once basic functionality is working.
- [X] Organize the project structure into appropriate subfolders (`controllers`, `operations`, `utils`, `widgets`).
- [ ] Review and clean up any unused code or dependencies.

## Implementations
- [ ] Finish implementing the `run_scheme` operation in `runschemeoperation.py`.
  - [ ] Verify the correctness of the `run_scheme` operation.
- [X] Complete the implementation of GUI widgets in `scheme_editor_text_view.py` and `spinner_widget.py`.
  - [ ] Finish implementing timers (replacing spinners).

## Testing
- [ ] Ensure tests run on window creation and display result.
- [ ] Arch Linux
- [ ] Debian
- [ ] MacOS
- [ ] Windows

## Documentation
- [ ] Review and update README.md once tests pass


# original Barliman TODOs for review

## TODO:

* Matt Might suggests using properties like `(append (cons a l) s) == (cons a (append l s))` for synthesizing `append`.
* Devon Zeugel suggests using a monospace font, and perhaps swapping the tests and the definitions in the main window.  Devon suggests using the number of tests that pass to guide search for auto-repair or other synthesis.  Or, to try to maximize the number of tests that pass, then have the user take over.  Maybe use the number of tests that pass as a score/heuristic for stochastic search.
* Tom Gilray suggests being able to hover over a ,A logic variable to select/approve a suggested/guessed value for that particular subexpression.  Michael Ballantyne and other people have suggested similar notions, including a scrubber for scrubbing over/selecting a generated/guessed value for a subexpression.
* replace test input/output edit fields with multi-line edit capabilities similar to that of the 'Definitions' pane
* add paren hilighting to editor
* add "smart delete" of parens
* add add auto-indent
* add forward/backward s-expression
* add transpose s-expression
* add pretty printing of "Best Guess" definitions
* add smart editing/auto insert of gensyms in the test edit panes, similar to how smart editing/auto insert of logic variables works in the Definitions edit pane
* for 'syntax error' and 'illegal sexpression' messages for a test, potentially show whether the input, the output, or both is the problem (could be complicated in that the output might be an illegal sexpression, while the input is a syntax error, for example)
* have Barliman attempt to guess the result of a test, as the programmer types in the test (thanks Ziyao Wei!)
* show the definition guessed for each individual successful test
* show reified test inputs and outputs upon success, for all tests (would allow queries like 'quines')
* mouse hover over ,A variable should display the variable's "Best Guess" value
* allow resizing of Barliman main window
* add `let` and `cond`.
* add better error message for 'invalid syntax', at least indicating whether there is an unexpected paren/missing end paren
* Possibly replace `list` call in the "best quess" query with nested `cons` calls instead.  (Need to time this again with Greg's new improvements to the search.)  This can be an order of magnitude faster in some cases, according to my testing (variadic application is more expensive than 'cons' in the current miniScheme interpreter, apparently: see times for append-gensym-synthesis-with-cons-1 versus append-gensym-synthesis-with-list-1 tests in test-interp.scm).
* add an implicit `begin` to `lambda`, `letrec`, and `let` forms.
* parser should enforce that the variable names are distinct in `lambda` formals, `letrec` bindings and formals, and `define`'s within the same scope.
* create a version of Barliman on an open platform (Electron, Clojurescript, Lighttable, whatever).  Any help would be appreciated!  :)
* consider using ulimit or some other capability for keeping the running Scheme processes under control/keep them from using all the RAM and CPU cycles
* consider adding fields for seeing the ground results of partially-instantiated test inputs/outputs
* add full variadic syntax: `(lambda (x y . z) x)`
* consider turning the background of the "guess" pane green, or otherwise indicting the user, when a guess can be made.  Could also potentially change the code in the main definition edit pane, although this may not be friendly.
* add STLC as an example, complete with type inferencer
* perhaps be able to drag and drop subexpressions from the best guess pane onto variables in the definition pane.  And also be able to replace an extort subexpression in the definition pane with a logic variable.
* think about contextual menus/right click and also drag and shift-drag.  What should these do?
* make sure Semantics and the main Barliman windows can be reopened if the user closes them!  Currently there doesn't seem to be a way to get the window back.  Perhaps allow the user to hide the windows, but not close them?  What is the preferred Mac way?
* for the case in which a simple function is being used to generate test inputs and answers for a more complex version of the same function, may need or want a grounder to make sure answers are fully ground.  May also want a grounder for code, esp for the best guess pane.  Although grounding code may not be necessary or ideal.
* would be smart to only re-run Scheme processes when the Scheme code actually *changes* – for example, white space characters outside of an S-expr shouldn't trigger re-evaluation.  One way would be to compare "before" and "after" S-exprs to see if anything has changed.  Could run a single Scheme instance and call `equal?` to see if the code has actually changed.  This could be a big win for expensive computations.
* add ability to save and load examples/tests/semantics, and include interesting examples, such as a tiny Scheme interpreter written in Scheme, state machine using mutual recursion, examples from pearls, etc.
* add structured editor for semantics and for type inferencer (as an alternative to/in addition to the free-form editor)
* possibly move as much work as possible into NSTasks, such as loading files.
* possibly add pairs of tests as processes, once individual tests complete successfully
* add syntax-directed auto-indentation of code
* figure out how to do syntax-directed hilighlighting, and precise hilighting of syntax errors.  May not be as important if I go the structured editor route.  Although perhaps this should be an option, either way.
* add documentation/tutorial
* add paper prototype for desired features
* move 'barliman-query.scm' temporary file to a more suitable location than 'Documents' directory, or get rid of the temp file entirely
* experiment with store passing style and small step interpreters
* get rid of hardcoded path to Chez executable
* add input/output examples
* find a cleaner and more flexible way to construct the program sent to Chez
* add "accept suggested completion" button
* would be smarter/less resource intense to not launch all the tests again when the text in a single test changes.  Only that test and allTests need be re-run, in theory.  Getting the UI to display the state of everything properly may be a little subtle, though.
* differential relational interpreters
* use a meta-interpreter to let the programmer know the deepest part of the search path upon failure, to try to give a better hint as to what went wrong (thanks Nada! and halp! :))

## LONGER TERM:

* Devon Zeugel suggested looking at Mutant (https://github.com/mbj/mutant).
* mousing over a failing test should highlight subexpressions in the Definitions pane that are incompatible with that test.
* mousing over a subexpression should hilight any tests which would be incompatible with the definitions, were a logic variable to be substututed for the expression being moused over. (perhaps do this only if a modifier key is help down)
* improve editor so that typing '(' 'cons' auto completes to '(cons ,A ,B)', based on arity of cons (unless cons is shadowed).
* consider placing each of the 'definition' forms in its own edit window, with 'uses mutattion', 'uses call/cc', 'well-typed' checkboxes for each definition (inspired by Kenichi Asai's tool for teaching functional programming).
* try adding contracts/properties/specs. For example, for `append`, could add the property that the sum of `(length l)` and `(length s)` must be equal to `(length (append l s))`.  This could work with randomized testing, even for partially-instantiated definitions.  In the case of `length`, would either need to use Oleg numbers, or CLP(FD).
* related to properties, might want generators, such as a `loso` that generates flat lists of symbols, for example, or `lovo`, that generates flat lists of values, or `treevo`, that generates trees of values.  Could use these generators for specifying and testing properties.  One simple, "type" property is that `append` should work on any two `lovo`s, and, in this case, return of `lovo`.  Could extend this to talk about the lengths of the `lovo`s, etc.  Could then either enumerate or randomly generate `lovo`s QuickCheck style to try to find counter-examples with respect to the current partial (or complete) definition, or perhaps to help with synthesizing the actual code.
* automatic test generation/fuzzing
* add arithmetic to the main interpreter
* explore incremental computing with the editor
* add type inferencer
* test generation of typed test programs
* partial evaluation of the interpreter to speed up evaluation
* add support for macros
* explore predicates/generators/QuickCheck-like functionality
* explore other synthesis techniques, model checking, etc., as alternatives or additions to the miniKanren-based program synthesis in Barliman
* add tree automata support to support grammars
* add abstract interpretation for miniKanren to speed up the synthesis
* use stochastic/probabilistic extensions to miniKanren to improve synthesis capabilities.  For example, see:

 Eric Schkufza, Rahul Sharma, and Alex Aiken. 2013. Stochastic superoptimization. In Proceedings of the eighteenth international conference on Architectural support for programming languages and operating systems (ASPLOS '13). ACM, New York, NY, USA, 305-316. DOI=http://dx.doi.org/10.1145/2451116.2451150
https://cs.stanford.edu/people/sharmar/pubs/asplos291-schkufza.pdf



## POSSIBLE USE CASES:

* write simple implementation of a function, generate test from that function, then use those tests to guide the more sophisticated implementation.  Or more generally, continually test the partially-implemented function vs the fully implemented but perhaps less efficient function.

* Matt Might suggests as a use case, "automatic program repair after bug discovery," and points to work by Stephanie Forrest.  I really like this idea.  Here's how the use case might work:

You write tests and code. The tests pass. Later you find an error in the code, so you go back and add more tests, which fail.

Click a Barliman 'auto-repair' button. Barliman tries, in parallel, removing each subexpression and trying synthesis to fill in the rest.

If Barliman could use a Amazon server with dozens of hardware cores and 2TB RAM (like the new X1 server on AWS), this really could be done in parallel.

Or run locally until there's a timeout, then run again with the holes in other places. Could even try pairs of holes to keep the synthesis problem as small as possible.

Or, perhaps more practical short term until Barliman's synthesis improves...

Have Barliman try removing each subexpression and then check if any of the tests still fail. Then hilight these known bad subexpressions to help guide the user.

Greg Rosenblatt's suggestion for auto-repair: "The user may also want to mark some regions of the code as suspect, which would prioritize the area searched for problematic sub-expressions.  If the user is right, the fix could be found much sooner."



## SUSPECT IDEAS:

* could just call out to Scheme one the program becomes grounded.  However, the semantics and even the grammar may not match that of the interpreter used by miniKanren, so this seems difficult or impossible to do properly.  However, could call a (non-relational) interpreter for miniScheme.


## INTERESTING IDEAS:

* Tom Gilray suggests using a simplified intermediate representation (IR) that disallows shadowing, has `if` but not `cond`, etc.  Could have the IR be the macro expanded code.  Could possibly reverse engineer/infer macro calls that could have produced the IR.
* Tom Gilray suggests changing the interface to just have a single editor window, which allows for definitions and for test calls/results.  I suspect this is the right way to go, although it will involve significant changes to Barliman.  Tom also suggests having arrows to the right of each logic variable, showing the current value of each variable.
* perhaps use delayed goals to implement arithmetic over floating point numbers, and other tricky operations.  If the arguments do not become instantiated enough, Barliman should be non-commital (can't synthesize code, and can't prove tests are not consistent with the code until the code is more instantiated).
* Greg Ronsenblatt suggests dividing tests into a 'training' set and a 'test' set, as is done in machine learning to avoid overfitting.  Of course this could also lead into 'propety-based testing', generators, etc.
* Jonas Kölker suggests synthesizing multiple definitions, or perhaps even all of the Haskell Prelude-style list functions, simultaneously, based on the relationships between the functions, and their Quickcheck-style properties.  He also suggests using properties like `reverse (xs++ys) == reverse ys ++ reverse xs` and `map f (xs++ys) == map f xs ++ map f ys` for synthesis.


## KNOWN LIMITATIONS:

* The `Best Guess` pane cannot be resized vertically, which sometimes cuts off text.
* Non-specific error indication (the color changes for the text, but does not show which part of the text caused the error)
* Currently the UI only supports 6 tests.  Should allow more tests to be added.
* Test inputs and outputs are `NSTextField`s rather than `NSTextView`s, which makes writing longer and more complicated tests awkward.


## KNOWN ERRORS:

* `let` expressions are not parsed properly.  In particular `(let ((x)) y)` parses.  Probably other expressions are also parsed a little too laxly.
* Shadowing of syntax is no longer working.  (and and #t) => #t should result in a syntax error, unless the Definitions pane contains a defn named 'and': (define and (lambda x  x)).  In which case, (and and #t) should be legal syntax.  (Wonder if we broke this when we messed with the environment in evalo.)
* It is possible, rarely, to exit Barliman and still have a Scheme process running in the background.  Need a way to better track which processes have been started and make sure to kill them.  Or potentially use something like `ulimit` when launching a process.
* The miniKanren queries constructed by Barliman expose several local variable names and a number of global variable names that could accidentally or intentionally be used by the programmer.  Need to tighten this up.
* closing one of the windows means the window cannot be reopened!  Oops.  I'm not going to worry about this until I decide what to do with the Semantics window.
* sometimes the spinners stop spinning but are still visible

## DONE (features on the TODO list implemented since the original release of Barliman)

* Implemented monospace font, as recommended by Devon Zeugel.
* Fixed error: An illegal s-expression in the 'Definitions' edit pane will make test input/output expressions that are legal expressions appear to be illegal.
* Fixed error (by removing auto-insert of right parens): auto-insert of right parens and auto-insert of logic variables breaks 'undo'.  Guess I need to learn how 'undo' works in Cocoa...
* Fixed error: The '0' key no longer seems to work.
* Fixed error: (lambda (,A ,B) ...) should always produce a disequality constraint between A and B.
* Fixed error: Will modified the miniKanren reifier to remove unnecessary constraints involving gensyms.  Alas, he goofed it, and the reifier removes too many constraints, including some =/= and absento constraints in play when gensyms are used.
* Fixed error: scoping problem introduced by optimizing variable lookup.
* Fixed error: Inserting a new logic variable with Control-<space> doesn't replace highlighted text.  Instead, it adds the variable and keeps the hilighted text.
* changed reifier and main edit window to display constraints separately from "best guess" definition(s).
* fixed: quickly tab-deleting a test with a syntax error (for example) can leave the 'syntax error message' on an empty test
* added automatic addition of right parens, and auto-addition of logic variables (thanks Michael Ballantyne, Guannan Wei, Pierce Darragh, Michael Adams, for discussions on how this might work)
* changed reifier so that constraints involving gensym are not displayed.
* Fixed error: even if the "best guess" query terminates with success, individual test processes may still keep running, since those tests don't "know" that the best guess involving *all* the tests has succeed.  If the best guess query terminates with success, the individual test processes should be killed, and marked as successful (black text, stop the progress spinner).
* updated `letrec` to allow for zero or more bindings, and updated `begin` to allow for zero or more definitions; this allows the creation of mutually-recursive functions.
* define grammar for microScheme (and the other languages) as a miniKanren relation, and use this grammar to separately check and report whether the definition is grammatically correct.
* cancel the allTests operation if any single test fails, since in that case allTests cannot possibly succeed
* wait part of a second to see if there are more keystrokes before launching Scheme processes.  Sort of like XCode (I assume XCode is doing this).  Would be more resource friendly, less distracting, and would make typing quickly more responsive.  Could probably do this using an timer.
* add ability to change the evaluator rules and perhaps an explicit grammar as well
