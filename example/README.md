This directory contains an example:

- `my-test-input`,  a program that fails if the test data includes `D` + `U` + `V` + `W`. Test data is passed into standard input

- `my-test-script`, test data that can be passed into standard input


If you call `shrinkplz` in this directory as follows:

``` sh
shrinkplz script ./my-test-script my-test-input
```

Then `shrinkplz` will run and shrink `my-test-input` down to exactly the failing test combo (placed inside `current-input`)
