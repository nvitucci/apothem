Title: Apache Commons Collections
Date: 2020-03-31
Category: projects
Tags: library, Apache Commons

With this article I'll take a break from large Apache projects to focus again on a single, easy-to-integrate library. [Apache Commons Collections](https://commons.apache.org/proper/commons-collections/) is part of the larger [Apache Commons](https://commons.apache.org/) project, a fantastic collection of libraries that cover very specific domains or use cases such as [CSV files processing](https://commons.apache.org/proper/commons-csv/), [command line arguments parsing](https://commons.apache.org/proper/commons-cli/), [string processing](https://commons.apache.org/proper/commons-text/), and many more.

The Collections component was created to add more collections and to expand on the existing Java collections' capabilities at a time when functional programming (especially in Java) was not yet widespread. Some solutions have actually been included in the most recent versions of Java itself (the [FluentIterable](https://commons.apache.org/proper/commons-collections/javadocs/api-4.4/index.html), for instance, has been "replaced" by Java 8's [Stream](https://docs.oracle.com/javase/8/docs/api/java/util/stream/package-summary.html)), while many other still provide useful additions and good alternatives to other widespread libraries such as [Guava](https://github.com/google/guava/wiki/NewCollectionTypesExplained). The collection types that first brought me to Apache Commons Collections are the `MultiSet` and the `MultiMap`, also because they have a native counterpart in Python, and the `LRUMap` as a simple cache; I also found the `SetUtils` extremely useful, since they added some mathematical (and functional) foundation to operations between sets. Let's go through some examples and see!

### Setting up

The latest version of Commons Collections is 4.4, which is based on Java 8; therefore, I will use Java 8 in the following. Although there are newer Java versions, the 8 is the oldest long-term support (LTS) version and is still prevalent in the Big Data world; it makes then for a good balance between "legacy" versions and the newest versions. I will not make use of lambdas in most examples, in order to make the code more readable and all the involved types explicit.

I find that the easiest way to get started with a Java library is by creating a Maven project. All the major IDEs support the creation of Maven projects, so that all you need to do is to give a name to your project and edit the `pom.xml` file to include lines like the following:

    :::xml

    <groupId>blog.apothem</groupId>
    <artifactId>apache-commons-collection-example</artifactId>
    <version>0.0.1-SNAPSHOT</version>

    <dependencies>
        <dependency>
            <groupId>org.apache.commons</groupId>
            <artifactId>commons-collections4</artifactId>
            <version>4.4</version>
        </dependency>
    </dependencies>

You are then ready to build the project and start tinkering with the examples. For a very easy start, I would just create a class with a `main` method and write all the code there; otherwise, another very good approach is to make the examples as test classes by using a testing framework such as [JUnit](https://junit.org/junit5/), but since this would require a bit more setup and some knowledge of testing, I would leave this as an "exercise for the reader". If you just want to grab a ready project with all the examples and run it, check out the [Apothem resources repository](https://github.com/nvitucci/apothem-resources/tree/master/apache-commons-collections)!

### Collection types

Let's now see what types of collection are available. First of all, a general remark that the project makes on its user guide: most collections are not thread-safe unless said otherwise, so they should be `synchronized` accordingly when thread safety is needed.

#### _Bag_

`Bag`s are collections where each element can appear many times. We will skip them because the `MultiSet` type is set to replace them (see the [release notes](https://commons.apache.org/proper/commons-collections/release_4_1.html) of version 4.1).

#### _BidiMap_

A `BidiMap` is a bidirectional map, namely a map where the key-to-value relation can be inverted, and the values effectively be used as keys in the _inverted map_. This collection type enables, among the other things, the creation of mappings between IDs as in the following example:

    :::java
    BidiMap<String, Integer> bidiMap = new DualHashBidiMap<>();

    bidiMap.put("string-id-1", 1);
    bidiMap.put("string-id-3", 3);
    bidiMap.put("string-id-2", 2);

    System.out.println(String.format(
        "Using key '%s' to retrieve value %d", "string-id-1", bidiMap.get("string-id-1")));
    System.out.println(String.format(
        "Using value %d to retrieve key '%s'", 1, bidiMap.getKey(1)));

<!-- -->

    :::text
    Using key 'string-id-1' to retrieve value 1
    Using value 1 to retrieve key 'string-id-1'

Here we have used a `DualHashBidiMap`, namely a `BidiMap` backed by two `HashMap`s, but like for the standard `Map` we have three different implementations:

    :::java
    BidiMap<String, Integer> bidiMap = new DualHashBidiMap<>();
    BidiMap<String, Integer> bidiMap = new DualLinkedHashBidiMap<>();
    BidiMap<String, Integer> bidiMap = new DualTreeBidiMap<>();

If we need to use `TreeMap`s, there is actually a fourth implementation which is especially optimized for this use case:

    :::java
    BidiMap<String, Integer> bidiMap = new TreeBidiMap<>();

All the implementations offer the same methods, notably:

- `get` to get a value by its key (as in the standard `Map`);

        :::java
        System.out.println(String.format(
                "Using key '%s' to retrieve value %d", "string-id-1", bidiMap.get("string-id-1")));

    <!-- -->

        :::text
        Using key 'string-id-1' to retrieve value 1

- `getKey` to get a key by its value, in "reverse" with respect to the common usage;

        :::java
        System.out.println(String.format(
                "Using value %d to retrieve key '%s'", 1, bidiMap.getKey(1)));

    <!-- -->

        :::text
        Using value 1 to retrieve key 'string-id-1'

- `entrySet` to get all the `Map.Entry` key-value pairs (note: here `getKey` is the usual method of `Map.Entry`):

        :::java
        for (Map.Entry<String, Integer> entry : bidiMap.entrySet())
            System.out.println(String.format(
                    "Key: '%s', value: %d", entry.getKey(), entry.getValue()));

    <!-- -->

        :::text
        Key: 'string-id-2', value: 2
        Key: 'string-id-3', value: 3
        Key: 'string-id-1', value: 1

- `inverseBidiMap` to get the inverted map, as in the following example:

        :::java
        for (Map.Entry<Integer, String> entry : bidiMap.inverseBidiMap().entrySet())
            System.out.println(String.format(
                    "Key: %d, value: '%s'", entry.getKey(), entry.getValue()));

    <!-- -->

        :::text
        Key: 1, value: 'string-id-1'
        Key: 2, value: 'string-id-2'
        Key: 3, value: 'string-id-3'

One thing to be careful about is that `BidiMap`s do not strictly check for value uniqueness, so inverting a `BidiMap` with repeated values can lead to unexpected behaviour (see a "bad BidiMap" example on the repo).

#### _MultiMap_

A `MultiMap` is a `Map` whose values are collections (lists or sets) of values, similar to Python's [defaultdict](https://docs.python.org/2/library/collections.html#collections.defaultdict). When instantiated with the default constructor, the map is initialized with a capacity of 16 and each list or set with a capacity of 3:

    :::java
    ArrayListValuedHashMap<String, String> multiMap = new ArrayListValuedHashMap<>();

Other constructors are available to manually set both capacities:

    :::java
    int initialMapCapacity = 32;
    int initialListCapacity = 10;

    ArrayListValuedHashMap<String, String> multiMap = new ArrayListValuedHashMap<>(initialListCapacity);
    ArrayListValuedHashMap<String, String> multiMap = new ArrayListValuedHashMap<>(initialMapCapacity, initialListCapacity);

The elements can be inserted in the usual way, but inserting more than one element with the same key does not result in overwriting:

    :::java
    multiMap.put("language", "Java");
    multiMap.put("language", "Python");
    multiMap.put("language", "C++");
    multiMap.put("skill", "Good");
    multiMap.put("skill", "Excellent");

    for (String key : multiMap.keySet())
        System.out.println(String.format(
                "Key '%s' contains values: %s", key, String.join(", ", multiMap.get(key))));

<!-- -->

    :::text
    Key 'skill' contains values: Good, Excellent
    Key 'language' contains values: Java, Python, C++

The `keySet` method here is used to obtain the unique keys, whereas the `keys` method is used to obtain all the keys as a `MultiSet` (with counts):

    :::java
    System.out.println(String.format(
            "Keys in the map (with counts): %s", multiMap.keys()));
    System.out.println(String.format(
            "Unique keys in the map: %s", multiMap.keySet()));

<!-- -->

    :::text
    Keys in the map (with counts): [skill:2, language:3]
    Unique keys in the map: [skill, language]

Since there are actually five "pairs", the map size is `5`:

    :::java
    System.out.println(String.format(
            "The map has %s elements", multiMap.size()));

<!-- -->

    :::text
    The map has 5 elements

This is also reflected by listing all the values in the map using the `values` method:

    :::java
    System.out.println(String.format(
            "Values in the map: %s", multiMap.values()));

<!-- -->

    :::text
    Values in the map: [Good, Excellent, Java, Python, C++]

The examples we have seen so far make use of the `ArrayListValuedHashMap` implementation, which arranges the values corresponding to each key in an `ArrayList`. The `HashSetValuedHashMap` can be used to arrange the values in `HashSet`s instead.

#### _MultiSet_

A `MultiSet` is a `Set` that allows for multiple occurrences of each element, keeping track of their count. It is similar to Python's [Counter](https://docs.python.org/2/library/collections.html#collections.Counter) and can be very useful when a count of the occurrences of an object in a set is needed, for instance in text processing applications.

The initialization and the insertion of elements are straightforward:

    :::java
    MultiSet<String> multiSet = new HashMultiSet<>();

    multiSet.add("Java");
    multiSet.add("programming");
    multiSet.add("Python");
    multiSet.add("programming");

Let's start with counting the objects in the map:

    :::java
    System.out.println(String.format(
            "There are %d elements in the multiset", multiSet.size()));
    System.out.println(String.format(
            "There are %d unique elements in the multiset", multiSet.uniqueSet().size()));

<!-- -->

    :::text
    There are 4 elements in the multiset
    There are 3 unique elements in the multiset

Since we have inserted four elements, the total count will be `4`; the unique elements instead are three, since `"Python"` is repeated twice. We can iterate through the elements of the set in two different ways:

- by iterating through the "pairs", getting the element itself and its count from each pair:

        :::java
        for (MultiSet.Entry s : multiSet.entrySet())
            System.out.println(String.format("\t'%s' appears %d time(s)", s.getElement(), s.getCount()));

- by iterating through the unique elements, getting the count using each element as a key:

        :::java
        for (String s : multiSet.uniqueSet())
            System.out.println(String.format("\t'%s' appears %d time(s)", s, multiSet.getCount(s)));

In both cases we obtain the following result:

    :::text
    'Java' appears 1 time(s)
    'programming' appears 2 time(s)
    'Python' appears 1 time(s)

#### _CircularFifoQueue_

The `Queue` type is already present in Java, so the main addition from Commons Collection is a circular FIFO queue, a fixed size queue where the oldest elements are replaced by the newer elements when it reaches capacity. A `CircularFifoQueue` is created with the size as a parameter for the constructor:

    :::java
    int size = 2;
    CircularFifoQueue<String> queue = new CircularFifoQueue<>(size);

Let's add one element and check 1) how many elements are there in the queue and 2) whether the queue is at full capacity:

    :::java
    queue.add("A");
    System.out.println(String.format(
            "Elements: %d out of %d, queue at full capacity?: %b",
            queue.size(), queue.maxSize(), queue.isAtFullCapacity()));

<!-- -->

    :::text
    Elements: 1 out of 2, queue at full capacity?: false

Now let's insert one more element and check again:

    :::java
    queue.add("B");
    System.out.println(String.format(
            "Elements: %d out of %d, queue at full capacity?: %b",
            queue.size(), queue.maxSize(), queue.isAtFullCapacity()));

<!-- -->

    :::text
    Elements: 2 out of 2, queue at full capacity?: true

Since the capacity is set to `2`, with two elements the queue is at full capacity. Let's check what the elements are:

    :::java
    System.out.println(new ArrayList<>(queue));

<!-- -->

    :::text
    [A, B]

What if we now add one more element?

    :::java
    queue.add("C");

    System.out.println(new ArrayList<>(queue));

<!-- -->

    :::text
    [B, C]

Obviously the queue is still at full capacity, but the first element `"A"` has been dropped to make room for the new element `"C"`.

Besides the methods just shown, `CircularFifoQueue` has the same methods of a standard `Queue` (including `poll` and `remove` to remove and return the head of the queue, and `element` and `peek` to return the head of the queue without removing it); there is also an `isFull` method to determine whether the queue is full, which always returns `false` since a circular queue can never be full.

#### _Trie_

A `Trie` implements a rather interesting data structure called [trie](https://en.wikipedia.org/wiki/Trie) (from re**trie**val), which is mostly used for search using prefixes. A trie is similar to a tree with an important difference: a node of the trie does not contain the value that is being searched, but the _path_ to the node does; as such, tries are very good at prefix search. The trie implementation that Commons Collections offers is called `PatriciaTree` (from the acronym PATRICIA, "Practical Algorithm to Retrieve Information Coded in Alphanumeric"), a type of compressed trie. Let's see an example.

    :::java
    Trie<String, Integer> trie = new PatriciaTrie<>();

    trie.put("car", 1);
    trie.put("cart", 2);
    trie.put("carton", 3);
    trie.put("cartridge", 4);
    trie.put("cartography", 5);
    trie.put("caravan", 6);
    trie.put("carbon", 7);
    trie.put("castle", 8);
    trie.put("coal", 9);

Here we just created a `PatriciaTree` and put several keys that share common prefixes; it is important to note that the type of the keys of a `PatriciaTree` should extend `String`. Let's suppose we want to find the values associated to all the keys starting with `"car"`; we can use the `prefixMap` method:

    :::java
    System.out.println(String.format(
        "Values for prefix '%s': %s", prefix, trie.prefixMap("car")));

<!-- -->

    :::text
    Values for prefix 'car': {car=1, caravan=6, carbon=7, cart=2, cartography=5, carton=3, cartridge=4}

If we want to see the keys preceding or following a specific key, we can use the `headMap` and `tailMap` methods:

    :::java
    System.out.println(String.format(
            "Keys before 'cart': %s", trie.headMap("cart")));
    System.out.println(String.format(
            "Keys after 'cart': %s", trie.tailMap("cart")));

<!-- -->

    :::text
    Keys before for 'cart': {car=1, caravan=6, carbon=7}
    Keys after 'cart': {cart=2, cartography=5, carton=3, cartridge=4, castle=8, coal=9}

Furthermore, if we want to see the keys between any two entries, we can use the `subMap` method:

    :::java
    System.out.println(String.format(
            "Keys between 'cart' and 'carton': %s", trie.subMap("cart", "carton")));

<!-- -->

    :::text
    Keys between 'cart' and 'carton': {cart=2, cartography=5}

#### _LRUMap_

A `LRUMap` is basically a limited-size cache where the least recently used (LRU) elements are evicted to leave room for new elements when the cache is full. The LRU policy is quite popular in caches; the concept of "least recently used" may vary, and for instance in Commons Collections it refers to `get` and `put` operations only: if two elements are inserted one after the other and the former is retrieved once, the latter will become "least recently used". The `LRUMap` is initialized with a `maxSize` parameter:

    :::java
    int maxSize = 2;
    LRUMap<String, Integer> lruMap = new LRUMap<>(maxSize);

Elements are inserted as in a standard `Map`:

    :::java
    lruMap.put("value1", 1);
    lruMap.put("value2", 2);

and can be iterated through with the usual `entrySet` method:

    :::java
    System.out.println(String.format(
            "Elements in the map: %s", lruMap.entrySet()));

<!-- -->

    :::text
    Elements in the map: [value1=1, value2=2]

If we insert a new element, the "oldest" one (in this case the first inserted, `"value1"`) will be removed:

    :::java
    lruMap.put("value3", 3);

    System.out.println(String.format(
            "Elements in the map: %s", lruMap.entrySet()));

<!-- -->

    :::text
    Elements in the map: [value2=2, value3=3]

If we insert one more element but we read `"value2"` first, the "oldest" one to be removed will be now `"value3"`:

    :::java
    lruMap.get("value2");
    lruMap.put("value4", 4);

    System.out.println(String.format(
            "Elements in the map: %s", lruMap.entrySet()));

<!-- -->

    :::text
    Elements in the map: [value2=2, value4=4]

It's important to note that, in order to use `LRUMap` as a cache in a real multithreaded environment, we should make it thread-safe; an easy way is by wrapping it with the `Collections.synchronizedMap` method.

#### _MultiKeyMap_
A `MultiKeyMap` is a `Map` where the keys are composite, such as `firstName` and `lastName` in a map that associates persons to document IDs. It can be instantiated like a standard `Map`:

    :::java
    MultiKeyMap<String, String> multiKeyMap = new MultiKeyMap<>();

with the important difference that the key can be actually made of up to 5 fields of the same type (`String` in the example). New elements can be added with `put` by just inserting all the key components one after the other and before the value:

    :::java
    multiKeyMap.put("John", "Doe", "id1");
    multiKeyMap.put("Jane", "Doe", "id2");

and then they can be read with `get` in a similar fashion:

    :::java
    System.out.println(String.format(
            "Using key '%s': %s", "(\"John\", \"Doe\")", multiKeyMap.get("John", "Doe")));

<!-- -->

    :::text
    Using key '("John", "Doe")': id1

This class can be very useful when implementing a structure such as a database table, as it makes it simple to use complex keys. It cannot be used, though, if a key must have components of different types.

### Utils

Besides new or refined collection types, Commons Collections offers several utility classes. A few examples:

- `FluentIterator`: a `Stream` precursor to enable some functional programming capabilities;

- `IteratorUtils` and `IterableUtils`: similar to Python's [itertools](https://docs.python.org/2/library/itertools.html) module, they add many methods to use `Iterator`s and `Iterable`s more efficiently; for instance, given two lists:

        :::java
        List<String> list1 = Arrays.asList("one", "two", "three");
        List<String> list2 = Arrays.asList("A", "B", "C");

    we can concatenate them with the `chainedIterable` method (or its iterator-based counterpart `chainedIterator`) or interleave them with the `zippingIterable` method (or its iterator-based counterpart `zippingIterator`):

        :::java
        for (String s: IterableUtils.chainedIterable(list1, list2))
            System.out.print(s + " ");

        System.out.println();

        for (String s: IterableUtils.zippingIterable(list1, list2))
            System.out.print(s + " ");

    <!-- -->

        :::text
        one two three A B C
        one A two B three C

- `ListUtils`: list-specific utilities that enable some set-like operations (e.g. union, intersection, sum, subtraction) on lists:

        :::java
        System.out.println(String.format(
                "Union: %s", ListUtils.union(list1, list2)));
        System.out.println(String.format(
                "Intersection: %s", ListUtils.intersection(list1, list2)));
        System.out.println(String.format(
                "Sum: %s", ListUtils.sum(list1, list2)));
        System.out.println(String.format(
                "Subtract: %s", ListUtils.subtract(list1, list2)));

    <!-- -->

        :::text
        Union: [one, two, three, one, two, four]
        Intersection: [one, two]
        Sum: [three, one, two, four]
        Subtract: [three]

    allow to calculate the longest common subsequence between lists:

        :::java
        System.out.println(String.format(
                "Longest common subsequence: %s", ListUtils.longestCommonSubsequence(list1, list2)));

    <!-- -->

        :::text
        Longest common subsequence: [one, two]

    and add the capability to create lazy lists:

        :::java
        Factory<Integer> factory = () -> new Random().nextInt();

        List<Integer> lazyList = ListUtils.lazyList(new ArrayList<>(), factory);

        System.out.println(String.format(
                "Lazy list length: %d", lazyList.size()));

        lazyList.get(2);
        System.out.println(String.format(
                "Lazy list length: %d", lazyList.size()));

    <!-- -->

        :::text
        Lazy list length: 0
        Lazy list length: 3

- `SetUtils`: set-specific utilities that enable some set operations (e.g. union, intersection, disjunction, difference) which, differently from the ones that Java already offers, return new `Set`s instead of modifying the `Set`s they are applied to:

        :::java
        Set<String> set1 = new HashSet<>(Arrays.asList("one", "two", "three"));
        Set<String> set2 = new HashSet<>(Arrays.asList("one", "four"));

        System.out.println(String.format(
                "Union: %s", SetUtils.union(set1, set2)));
        System.out.println(String.format(
                "Intersection: %s", SetUtils.intersection(set1, set2)));
        System.out.println(String.format(
                "Disjunction: %s", SetUtils.disjunction(set1, set2)));
        System.out.println(String.format(
                "Difference: %s", SetUtils.difference(set1, set2)));

    <!-- -->

        :::text
        Union: [one, two, three, four]
        Intersection: [one]
        Disjunction: [two, three, four]
        Difference: [two, three]

- `CollectionUtils`: generic methods on `Collection`s, including decorators to make the underlying `Collection` synchronized, unmodifiable, filtered or validated by a predicate, etc.

### Conclusions

We have seen that the Commons Collections project provides a really vast amount of collection types, utilities, and decorators to use with existing collections. The project is very easy to integrate and the documentation, although a bit lacking in examples, is covered by an extensive and detailed Javadoc. If you find yourself making use of many collections, Commons Collections can help you in many ways.