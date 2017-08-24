# What to see

Difference between the translation of virtual address to physical address of the same page in SGX SW and HW modes.

Translation using this program: http://fivelinesofcode.blogspot.ch/2014/03/how-to-translate-virtual-to-physical.html

## SW Mode

* EPC page:

```
7f285160a000-7f2861621000 rw-p 00000000 00:00 0 
Size:             262236 kB
Rss:              262236 kB
Pss:              262236 kB
Shared_Clean:          0 kB
Shared_Dirty:          0 kB
Private_Clean:         0 kB
Private_Dirty:    262236 kB
Referenced:       262236 kB
Anonymous:        262236 kB
AnonHugePages:         0 kB
ShmemPmdMapped:        0 kB
Shared_Hugetlb:        0 kB
Private_Hugetlb:       0 kB
Swap:                  0 kB
SwapPss:               0 kB
KernelPageSize:        4 kB
MMUPageSize:           4 kB
Locked:                0 kB
VmFlags: rd wr mr mw me ac sd 
```

```
$ sudo ./a.out 14426 7f285160a000
Big endian? 0
Vaddr: 0x7f285160a000, Page_size: 4096, Entry_size: 8
Reading /proc/14426/pagemap at 0x3f9428b050
[0]0x66 [1]0xbf [2]0x1d [3]0x0 [4]0x0 [5]0x0 [6]0x80 [7]0x81 
Result: 0x81800000001dbf66
PFN: 0x1dbf66
```

* Mapped file:

```
$ sudo ./a.out 14426 7f287330a000 
Big endian? 0
Vaddr: 0x7f287330a000, Page_size: 4096, Entry_size: 8
Reading /proc/14426/pagemap at 0x3f94399850
[0]0xb5 [1]0xd5 [2]0x1e [3]0x0 [4]0x0 [5]0x0 [6]0x80 [7]0x81 
Result: 0x81800000001ed5b5
PFN: 0x1ed5b5
```

* Probably unallocated random page:

```
$ sudo ./a.out 14426 541654
Big endian? 0
Vaddr: 0x541654, Page_size: 4096, Entry_size: 8
Reading /proc/14426/pagemap at 0x2a08
[0]0x0 [1]0x0 [2]0x0 [3]0x0 [4]0x0 [5]0x0 [6]0x0 [7]0x0 
Result: 0x0
Page not present
```

## HW Mode

* EPC page:

```
7f52e0254000-7f52f0254000 rw-s 20254000 00:06 483                        /dev/isgx
Size:             262144 kB
Rss:                   0 kB
Pss:                   0 kB
Shared_Clean:          0 kB
Shared_Dirty:          0 kB
Private_Clean:         0 kB
Private_Dirty:         0 kB
Referenced:            0 kB
Anonymous:             0 kB
AnonHugePages:         0 kB
ShmemPmdMapped:        0 kB
Shared_Hugetlb:        0 kB
Private_Hugetlb:       0 kB
Swap:                  0 kB
SwapPss:               0 kB
KernelPageSize:        4 kB
MMUPageSize:           4 kB
Locked:                0 kB
VmFlags: rd wr sh mr mw me ms pf io dc de dd sd 
```

```
$ sudo ./a.out 14004 7f52e0254000
Big endian? 0
Vaddr: 0x7f52e0254000, Page_size: 4096, Entry_size: 8
Reading /proc/14004/pagemap at 0x3fa97012a0
[0]0x0 [1]0x0 [2]0x0 [3]0x0 [4]0x0 [5]0x0 [6]0x80 [7]0x0 
Result: 0x80000000000000
Page not present
```

* Mapped file:

```
$ sudo ./a.out 14004 7f53096cb000
Big endian? 0
Vaddr: 0x7f53096cb000, Page_size: 4096, Entry_size: 8
Reading /proc/14004/pagemap at 0x3fa984b658
[0]0xe0 [1]0x58 [2]0x1f [3]0x0 [4]0x0 [5]0x0 [6]0x80 [7]0x81 
Result: 0x81800000001f58e0
PFN: 0x1f58e0
```

* Probably unallocated random page:

```
$ sudo ./a.out 14004 78657646
Big endian? 0
Vaddr: 0x78657646, Page_size: 4096, Entry_size: 8
Reading /proc/14004/pagemap at 0x3c32b8
[0]0x0 [1]0x0 [2]0x0 [3]0x0 [4]0x0 [5]0x0 [6]0x0 [7]0x0 
Result: 0x0
Page not present
```

