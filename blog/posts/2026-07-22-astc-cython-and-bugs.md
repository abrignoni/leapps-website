---
title: ASTC, Cython, and bugs!
date: 2026-07-22
author: Bruno Constanzo
tags: [iLEAPP, iOS, artifacts, Cython]
excerpt: What do texture decompression, C-extensions for python, and LEAPPs have in common? Read to find out!
---

# ASTC, Cython, and bugs!

A couple of years ago, I started collaborating in the LEAPPs trying to make things work a little (sometimes a lot) faster. One of those early contributions was the application snapshots artifact, which required doing some Cython magic.

What is Cython you ask? ASTC? Old bugs? We'll take a look into all those things. You're probably also thinking "why are we talking about this old stuff?", well there are some good news that make it relevant today.

So without further ado, let's dive into all this!

## ASTC and astc_decomp

ASTC stands for "Adaptive Scalable Texture Compression", and is a texture compression algorithm developed by ARM and AMD ([link to paper](https://www.cs.cmu.edu/afs/cs/academic/class/15869-f11/www/readings/nystad12_astc.pdf)). It gives competitive compression ratios for textures in GPUs memory, with good visual quality too. ASTC was eventually adopted by Khronos (the group behind OpenGL and Vulkan) as part of their KTX format (Khronos Texture format).

Back in the day, Apple decided that they'd save application snapshots (screenshots, basically) in KTX format using ASTC compression. That meant iLEAPP's appSnapshots artifact needed to handle images in this format, and at the time it was written, the only way to do it was [astc_decomp](https://github.com/K0lb3/astc_decomp), a python module developed by Rudolf Kolbe to allow PIL to open this kind of images transparently, using Rich Geldreich C++ library [astc_dec](https://github.com/richgel999/astc_dec).

But the LEAPPs and PIL are written in Python, so how do we get to use this?

## Cython to the rescue

The Python everyone knows and loves is actually CPython, and nobody has to worry or think about that. CPython is the reference implementation of the Python programming language, with others including:

* RPython, PyPy's "restricted" python that allows its JIT to do straight wonders and can give your python programs 1-20x speedup without any change -- as long as your dependencies are PyPy-compatible.
* Jython, Python inside the Java Virtual Machine. You may have encountered this one if you ever tried to write a python plugin for [Autopsy](https://www.sleuthkit.org/autopsy/). Jython's main advantage is seamless integration with JAVA, and that's also its main drawback: you end up writing JAVA with Python syntax. Jython has been stuck in Python 2.7 support (which CPython EOLed back in Jan 1st 2020!), and yet again, all your dependencies have to be Jython-compatible.
* IronPython is Python inside the .NET/Mono frameworks. Similar to Jython, the integration with that environment is the pro/con of the language. It is still maintained, but yet again, all your dependencies have to be compatible with it.
* MicroPython an implementation written in C that targets microcontrollers. Supports all 3.4, most 3.5, and some features of python 3.6 onwards. Yet again, all your dependencies have to be compatible, thought if you're programming microcontrollers you're probably well aware of what you can and can't do in your target platform.

That brings us to CPython, "the one python". It is the most up to date version (3.14 stable at the time of writing, with 3.15 being a few months ahead of us). This what you think of whenever python crosses your mind. Almost all 3rd party modules and software developed in python targets this implementation, except for some specific use cases.

The CPython interpreter is written in C, and on top of that we have the Python Standard Library which is mostly written in python, with some performance-sensitive parts in C (off the top of my mind, the `re` and `pickle` modules are compiled). Because of how CPython is designed, there's a mechanism for writing "C-extension modules": you write some C, interact with the Python API, respect some boundaries and rules, and suddenly you've added C code into python. Amazing!

But writing C is not for everyone -- I myself haven't written a line of C in well over 15 years. And maybe for some reason you also need to provide a Python implementation, because maybe compiling the C parts of the code is hard on some target platform (we've got some of that ahead of us). About 25 years ago, Greg Ewing created Pyrex (that's where we got the .pyx extension!), and which then Stefan Behnel, Robert Bradshaw, and a few others forked it into Cython.

Cython is a compiler that lets you compile standard Python into C-extension modules. On its own that wouldn't really do much (just removing the interpreter loop), but there's a fantastic trick up Cython's sleeve: it lets you add type declarations into your python code, and interact with CPython's C API, and C ABI. Now that's interesting, because now Cython can turn some, most, or all of your (C|P)ython into C.

The two main uses for Cython are:
* Speeding up existing python code with C types annotations and function definitions, for which you'll use the `cdef` and `cpdef` keywords extensively. More advanced users of Cython can also define structs and such.
* Importing (actually `cimport`-ing) C libraries, and writing wrappers to expose them safely to Python land.

That second use case is what Kolbe did with astc_dec. Oh because Cython is even more awesome than what I mentioned so far, and it can also target C++. Because of course they'd pull that rabbit of the hat too.

## astc_decomp_faster

Back in 2022 [I profiled and optimized some parts of iLEAPP](https://github.com/abrignoni/iLEAPP/pull/346) and the Application Snapshots artifacts was a sore point. After some careful consideration, and a few experiments, I cloned astc_decomp and tried to figure out if it could be sped up.

With Cython you can annotate your code, from a terminal just type `cython -a mycode.pyx` and you'll get an HTML file that shows your code line per line, annotated with colors. The yellower the line, the more your code interacts with the Python API/runtime, and the slower it'll run. If you manage to remove all those interactions with python-land, then the code can be translated entirely to C, which the platform compiler will make a fantastic job optimizing. Of course that's easier said than done.

![astc_decomp main loop, it's annotated with intense yellow almost on every line](https://cdn.jsdelivr.net/gh/abrignoni/leapps-website@main/blog/images/2026-07-22-astc-cython-and-bugs/asct_decomp_og.png)
*Figure 1: astc_decomp's original loop for decompressing an ASTC image into the destination buffer. Almost every line is intensely yellow, which indicates strong interaction with the Python API, and hence slow code.*

That's what I set out to do with [astc_decomp_faster](https://github.com/bconstanzo/astc_decomp_faster), just take Kolbes code, and remove as much yellow (python interaction) as I could. The biggest issue was correctly handling the buffers that are used in the innermost loop. It took me a few rounds of trial and error (many errors) to find the memory allocation size that worked. Not so fun to iron out, because incorrect memory sizes resulted in CPython blowing up so bad that I didn't even get an error message nor a traceback, it'd just throw me back to an empty shell with no results.

All the memory that we `malloc()` must be `free()`'d, but not before converting the final image to python `bytes()`, as the original function did and PIL expects. In the end I managed to make the function entirely C compatible, up to the return statement, so Cython and the platform compiler are both happy, and we'll be happy too because we get fast code.

![astc_decomp_faster main loop, all lines are clear](https://cdn.jsdelivr.net/gh/abrignoni/leapps-website@main/blog/images/2026-07-22-astc-cython-and-bugs/asct_decomp_opt.png)
*Figure 2: astc_decomp_faster's loop for decompression, original lines have been commented and replaced by semantically equivalent, but Cython friendly code, that is converted straight to C. This results in fast compiled code (as fast as our platform's compiler can manage).*

Kolbe's repo also came with some GitHub Actions, which at the moment I barely understood, and managed to adjust so that astc_decomp_faster would auto publish [to PyPI](https://pypi.org/project/astc-decomp-faster/) which lets you pip-install it. For a while, that was enough. But then Python 3.13 came along, and some bugs with it.

## The Bug(s) of 3.13

While occasionally some people would have some trouble installing things (mostly on Windows), the binary wheels worked fine. Major Python versions, which go out in October, would generally bring some incompatibilities with them, and we'd have to wait it out one or two months before things were ironed out in between Python and Cython, and the code would compile fine once again.

Sometimes someone would still have problems compiling the code, and would require a little bit of work on our end. From one such time we dropped a .whl file directly on the repo so that it would be handy if for some reason someone had trouble.

But The Bug was actually Python 3.13. Not exactly the version itself, but 3.13 had a big re-structuring of python internals for many different reasons. I (vaguely) remember it having to do with the [Faster CPython initiative](https://github.com/faster-cpython/ideas), the work with subinterpreters (see [PEP 554](https://peps.python.org/pep-0554/) and [PEP 684](https://peps.python.org/pep-0684/)), and maybe the new and improved GIL-ectomy (see [PEP 703](https://peps.python.org/pep-0703/) and [free-threading docs](https://docs.python.org/3/howto/free-threading-python.html#freethreading-python-howto)). Take those with a grain of salt, it's been a while already and my recollection of very specific details is hazy.

The thing is that the core of Python was changing, and while standard python code won't even notice those changes, compiled C code that interacts with the Python API may. And in 3.13, there were many many changes that were noticed indeed.

For a while we thought "just another major version release, in a few weeks or months everything will be fine". Turns out it wasn't. For the past 2 years every once in a while I'd try to compile astc_decomp_faster, and fail. Windows and Mac had the most trouble, so Linux people had a way to make it work. I remember one of the most hardy bugs was related to a macro that handled some conversion between long long and python Int objects, but can't really find it. I can find discussions of the core python team [about 3.13 being a more difficult release because of the internal changes](https://discuss.python.org/t/revert-python-3-13-c-api-incompatible-changes-causing-most-troubles/38214). Certainly that tracks with our experience too.

**NOTE:** I know this whole part reads mostly a negative mood, because it affected our project for a long while, so let me be clear: **I respect and admire the work that the Python, Cython, and other core developers do, _even if some of that work ends up giving us trouble_.** They do their best to improve the foundations upon which we build our projects, and I'll always be grateful for that.

## The Fix and closing remarks

The fix was what it had always been: finally Cython 3.1 ironed out all the issues that were still lingering with 3.13 and astc_decomp_faster. And I missed the release, because the last time I tested it was still on a release candidate and not stable.

So a few weeks back, Adam Hachem called my attention that he was able to compile astc_decomp_faster with 3.14, on Windows!!! That threw me down a rabbit hole, which ended up with me updating the GitHub Actions that I had inherited from the original astc_decomp repo, and those were using outdated versions of tools and compilers.

Adam  was aware of this because [crush-forensics](https://github.com/kalink0/crush-forensics) uses astc_decomp_faster, and they had to do some python-env magic in place. Doing that, they figured that newer Cython would compile the project, and asked why we weren't doing it, and the answer was "I just wasn't aware".

Now we have wheels for Python 3.13 and 3.14 on all platforms, including Apple Silicon! When 3.15 is released in a few months, it should be smoother sailing, all thanks to the work of Cython and Python core developers. This bug-fix/update allows us to move to the newer/latest python versions, which is always a good thing! All thanks to the great open source communities that support all these projects.

