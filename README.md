# cg_difftext
Valgrind (cachegrind) textual diff

cg_difftext helps to compare the output of two Valgrind runs:

```
$ valgrind --tool=cachegrind ./sqlite_llvm <test.sql >/dev/null
[...]
--------------------------------------------------------------------------------
           Ir       I1mr   ILmr          Dr      D1mr    DLmr          Dw      D1mw    DLmw
--------------------------------------------------------------------------------
1,278,771,731 29,231,219 35,783 359,414,267 6,707,514 528,920 197,515,528 2,594,262 171,968  PROGRAM TOTALS
 
--------------------------------------------------------------------------------
         Ir      I1mr  ILmr         Dr      D1mr    DLmr         Dw    D1mw   DLmw  file:function
--------------------------------------------------------------------------------
363,052,233 7,560,087 3,122 97,707,865 1,084,529  77,197 44,505,055 217,826 29,838  src/sqlite3.c:sqlite3VdbeExec
 95,048,357    80,721   111 33,248,107    59,086   7,273 20,173,275      91      7  src/sqlite3.c:vdbeRecordCompareWithSkip
 68,045,026   695,509 1,144 14,883,933   114,698   1,918  5,525,733 272,507 19,249  src/sqlite3.c:balance
 56,713,554 1,101,002   276 18,416,705   683,914  21,085  3,453,665   1,947     25  src/sqlite3.c:sqlite3BtreeMovetoUnpacked
[...]
```

Instead of sorting the output by overall number of instructions, cg_difftext
sorts by the biggest difference between the two compared profiles:

```
$ cg_difftext.py cachegrind.out.gcc cachegrind.out.llvm
[file_a] cachegrind.out.gcc
[file_b] cachegrind.out.llvm
    Ir:      1,210,101,457      1,278,770,879  [        68,669,422]
  I1mr:         23,202,418         29,231,219  [         6,028,801]
  ILmr:             30,817             35,783  [             4,966]
    Dr:        337,329,529        359,414,081  [        22,084,552]
  D1mr:          6,107,672          6,707,514  [           599,842]
  DLmr:            522,450            528,920  [             6,470]
    Dw:        180,346,394        197,515,342  [        17,168,948]
  D1mw:          2,646,481          2,594,262  [           -52,219]
  DLmw:            172,947            171,968  [              -979]

[func] sqlite3VdbeExec
[file] src/sqlite3.c
    Ir:        305,641,560        363,052,233  [        57,410,673]
  I1mr:          4,725,208          7,560,087  [         2,834,879]
  ILmr:              2,215              3,122  [               907]
    Dr:         84,047,121         97,707,865  [        13,660,744]
  D1mr:            694,519          1,084,529  [           390,010]
  DLmr:             67,617             77,197  [             9,580]
    Dw:         29,174,474         44,505,055  [        15,330,581]
  D1mw:            170,442            217,826  [            47,384]
  DLmw:             29,600             29,838  [               238]
[...]
```