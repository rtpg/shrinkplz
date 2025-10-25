Shrinkplz
=========

`shrinkplz` is a command line tool to help shrink failing test data, similar to `git bisect`.

`shrinkplz` can take some input data causing a test failure, and then attempt shrinking it by cutting out lines from the input data until it starts passing.

At the end of the `shrinkplz` session, you should have a (locally) minimal input data for your test that is still failing.

Installation
------------

This command is available on PyPI:

``` sh
uv tool install shrinkplz
```

You can install the latest code on `main` by pointing directly at the repo:

```sh
uv tool install git+https://github.com/rtpg/shrinkplz
```

`
Use Cases
---------

- Shrinking a failing SQL script, removing irrelevant statements
- Shrinking a failing CI test run, by removing elements from the test list
- Shrinking large input data to a program until it starts working again


Quick Start
-----------


Start a shrinking session by calling:

    shrinkplz start some-test-data
    
`shrinkplz` expects a unicode file, and will attempt to shrink it by bisecting the lines themselves.

Once you've started a session, a file called `current-input` is created. This is the currently shrunk test data.

Once you have started your session, run your test with this test data or otherwise check your conditions:

    ./run_my_test.py current-input
    # ... and then investigating the result
    
Once you have finished testing the data in `current-input`, you should mark it with the `mark` command

    # if the test now passes
    shrinkplz mark pass 
    
    # if the test is still failing
    shrinkplz mark fail
    
    # if the test data is invalid (e.g. the data has become malformed)
    shrinkplz mark invalid
    
Once you mark the result, `current-input` gets replaced with another candidate for testing. 

Each mark gives `shrinkplz` more information about how it can shrink data.

 - `shrinkplz mark fail` indicates that `current-input` is enough to cause the failure, so discards any test data from the original input that isn't in `current-input`
   
 - `shrinkplz mark pass` indicates that `current-input` is missing the data that causes a failure, so we will restore the chunk of data that we removed
 
 - `shrinplz mark invalid` similarly indicates that the chunk of data shouldn't be removed, though without inferring more
 
 After shrinking as much as it can, `shrinkplz` will write out something like:
 
 ```
Completed our search!
The smallest known data is copied
to current-input
 ```
 
 From there, the session is over and `current-input` represents the result of the search
 
Script
------

Just like with `git bisect`, `shrinkplz` can be scripted. This is especially valuable for larger pieces of test data, where a shrinking session might require hundreds or thousands of test runs.

```
shrinkplz script my-test-script my-test-input 
```

`shrinkplz script` takes two inputs:

- a test script, that will be run by `shrinkplz` to determine how to mark input data. 
 
  The test script's error code determines what the marking is. A return code of 0 means to mark the data as `pass`, a return code of 125 indicates marking the data as `invalid`, and any other return code indicates a `fail`
  
- the test input to shrink

The test script is called without arguments, but just like when running a shrinking session manually, `current-input` will be available as the current input

```bash
#!/usr/bin/env bash
# an example shrink script
uv run my-prog.py < current-input
```

At the end of the `shrinkplz script` session, `current-input` will be the shrunk test data


