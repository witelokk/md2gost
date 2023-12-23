import marko
from pathlib import Path

markdown= """
[test](#hello)

<a id="test"></a>hello

1. hello
   
   world

1. what is going on

sdg

   asdf asdf
"""

print(marko.convert(markdown))
