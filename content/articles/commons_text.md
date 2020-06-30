Title: Apache Commons Text
Date: 2020-06-30
Category: projects
Tags: library, Apache Commons, text processing
Status: published

Today we are back to the [Apache Commons](https://commons.apache.org/) project with a library for string manipulation and comparison, [Apache Commons Text](http://commons.apache.org/proper/commons-text/). The library can be a lightweight alternative to larger NLP libraries or a good complement to the powerful `StringUtils` class from the [Apache Commons Lang](http://commons.apache.org/proper/commons-lang/) library. What I really like of Commons Text, besides the "base" operations on strings, is the collection of string similarity measures that allow to quantify _how much_ two strings are close to each other, as we will see in detail in the `text.similarity` section.

The Commons Text library contains a few packages which we will explore one by one. We will just skip the `text.lookup` and `text.matcher` packages because they only contain one very specialized class each, which I do not consider very interesting.

[TOC]

### Setting up

The latest version of Commons Text is 1.8, which is based on Java 8; therefore, we will use Java 8 in the code examples. As we have done in the [Apache Commons Collections article]({filename}/articles/commons_collections.md), we will use the library by means of a `pom.xml` like the following:

    :::xml

    <groupId>blog.apothem</groupId>
    <artifactId>apache-commons-text-example</artifactId>
    <version>0.0.1-SNAPSHOT</version>

    <dependencies>
        <dependency>
            <groupId>org.apache.commons</groupId>
            <artifactId>commons-text</artifactId>
            <version>1.8</version>
        </dependency>
    </dependencies>

Again, we will create a class with a `main` method and write all the code there; the complete code is available as always in the [Apothem resources repository](https://github.com/nvitucci/apothem-resources/tree/master/apache-commons-text).

### The `text` package

In the main package we can find a few classes dedicated to alphabet conversion (`AlphabetConverter`), case change (`CaseUtils`), escaping (`StringEscapeUtils`), substitution (`StringSubstitutor`), tokenization (`StringTokenizer`), string building (`TextStringBuilder`) and word utilities (`WordUtils`). The `StringTokenizer` just adds some functionalities to Java's `StringTokenizer`, and I couldn't find a useful use case for the `AlphabetConverter`; therefore, we won't see any examples of these classes.

#### `CaseUtils`

The `CaseUtils` class contains only one static method `toCamelCase`, which converts a string to [camel case](https://en.wikipedia.org/wiki/Camel_case) based on a delimiter and optionally capitalizes the first letter:

    :::java
    String string = "java-programming-language";

    // Capitalizes the first letter
    System.out.println(CaseUtils.toCamelCase(string, true, '-'));
    // Does not capitalize the first letter
    System.out.println(CaseUtils.toCamelCase(string, false, '-'));

<!-- -->

    :::text
    JavaProgrammingLanguage
    javaProgrammingLanguage

#### `StringEscapeUtils`

The `StringEscapeUtils` class contains several methods to escape a string given a language such as HTML or XML, or a format like CSV:

    :::java
    String string = "<a>Department, R&D</a>";

    System.out.println(StringEscapeUtils.escapeHtml4(string));
    System.out.println(StringEscapeUtils.escapeXml11(string));
    System.out.println(StringEscapeUtils.escapeCsv(string));

<!-- -->

    :::text
    &lt;a&gt;Department, R&amp;D&lt;/a&gt;
    &lt;a&gt;Department, R&amp;D&lt;/a&gt;
    "<a>Department, R&D</a>"

Escaping can also be included in a string builder to interactively escape only some parts of a string:

    :::java
    System.out.println(
            StringEscapeUtils
                    .builder(StringEscapeUtils.ESCAPE_HTML4)
                    .append("R&D dept: ")
                    .escape(string)
                    .toString());

<!-- -->

    :::text
    R&D dept: &lt;a&gt;Department, R&amp;D&lt;/a&gt;

#### `StringSubstitutor`

The `StringSubstitutor` is a different take on string interpolation than `String.format()`, closer to the approach that Scala and Kotlin use; it requires the creation of a map containing the variables to substitute in a template string, which can be used both with a static method and with a `StringSubstitutor` instance:

    :::java
    Map<String, String> substitutions = new HashMap<>();
    substitutions.put("city", "London");
    substitutions.put("country", "England");

    // With static method
    System.out.println(
            StringSubstitutor.replace("${city} is the capital of ${country}", substitutions));

    // With StringSubstitutor object
    StringSubstitutor sub = new StringSubstitutor(substitutions);
    System.out.println(sub.replace("${city} is the capital of ${country}"));

<!-- -->

    :::text
    London is the capital of England

The `StringSubstitutor` can also create an _interpolator_, a lookup-based substitutor that can calculate values such as the Base64 encoding of a string:

    :::java
    StringSubstitutor interpolator = StringSubstitutor.createInterpolator();
    System.out.println(interpolator.replace("Base64 encoder: ${base64Encoder:Secret password}"));

<!-- -->

    :::text
    Base64 encoder: U2VjcmV0IHBhc3N3b3Jk

and many more (check out [the docs](http://commons.apache.org/proper/commons-text/apidocs/org/apache/commons/text/StringSubstitutor.html) for a complete list).

#### `TextStringBuilder`

This class can be considered as an "enriched" `StringBuilder` that adds more methods, for instance to append some fixed-length padding to the string that is being created:

    :::java
    String header = "Header";

    TextStringBuilder builder = new TextStringBuilder();
    System.out.println(builder.appendPadding(header.length(), '-').toString());

<!-- -->

    :::text
    Header
    ------

and [much more](http://commons.apache.org/proper/commons-text/apidocs/org/apache/commons/text/TextStringBuilder.html) (e.g. to delete and replace characters, add separators, etc.).

#### `WordUtils`

The `WordUtils` class contains methods for:

- word/sentence abbreviation:

        :::java
        String longString = "This is a very long string, from https://www.example.org";

        // Take at least 9 characters, cutting to 12 characters if no space is found before
        System.out.println(WordUtils.abbreviate(longString, 9, 12, " ..."));
        // Take at least 10 characters, cutting to 12 characters if no space is found before
        System.out.println(WordUtils.abbreviate(longString, 10, 12, " ..."));
        // Take at least 10 characters, then cut on the first space wherever it is
        System.out.println(WordUtils.abbreviate(longString, 10, -1, " ..."));

    <!-- -->

        :::text
        This is a ...
        This is a ve ...
        This is a very ...

- initials extraction:

        :::java
        String allLower = "all lower but ONE";

        System.out.println(WordUtils.initials(allLower));

    <!-- -->

        :::text
        albO

- case change (strange enough, with the exception of camel case conversion that, as we have seen, is in its own `CaseUtils` class):

        :::java
        String allLower = "all lower but ONE";
        String allCapitalized = "All Capitalized But ONE";

        // Doesn't lowercase the uppercase characters
        System.out.println(WordUtils.capitalize(allLower));
        // Lowercases everything, then capitalizes the first letter of each word
        System.out.println(WordUtils.capitalizeFully(allLower));
        // Lowercases the first letter of each word
        System.out.println(WordUtils.uncapitalize(allCapitalized));
        // Swaps the case of each character
        System.out.println(WordUtils.swapCase(allLower));

    <!-- -->

        :::text
        All Lower But ONE
        All Lower But One
        all capitalized but oNE
        ALL LOWER BUT one

- paragraph wrapping:

        :::java
        String longString = "This is a very long string, from https://www.example.org";

        // Line length is 10, uses '\n' as a line break, does not break words longer than the line
        System.out.println(
                WordUtils.wrap(longString, 10, "\n", false) + "\n");

        // Line length is 10, uses '\n' as a line break, breaks words longer than the line
        System.out.println(
                WordUtils.wrap(longString, 10, "\n", true) + "\n");

        // Line length is 10, uses '\n' as a line break, breaks words longer than the line, also breaks on commas
        System.out.println(
                WordUtils.wrap(longString, 10, "\n", true, ",") + "\n");

    <!-- -->

        :::text
        This is a
        very long
        string,
        from
        https://www.example.org

        This is a
        very long
        string,
        from
        https://ww
        w.example.
        org

        This is a 
        very long 
        string
         from http
        s://www.ex
        ample.org


### The `text.diff` package

This package features some classes to show how a diff between two strings is calculated. In particular, the `StringComparator` class can be used to create a script that transforms one string into another:

    :::java
    String s1 = "hyperspace";
    String s2 = "cyberscape";

    StringsComparator comparator = new StringsComparator(s1, s2);
    EditScript<Character> script = comparator.getScript();

    System.out.println("Longest Common Subsequence length (number of \"keep\" commands): " +
            script.getLCSLength());
    System.out.println("Effective modifications (number of \"insert\" and \"delete\" commands): " +
            script.getModifications());

<!-- -->

    :::text
    Longest Common Subsequence length (number of "keep" commands): 6
    Effective modifications (number of "insert" and "delete" commands): 8

and by implementing a visitor class we can see each `insert`, `delete` and `keep` operation (see the code in the repository for an example implementation).

### The `text.translate` package

In this package we can find classes for translating the characters of a string into different characters, for instance via lookup to transform a string in its [leetspeak](https://en.wikipedia.org/wiki/Leet) equivalent:

    :::java
    Map<CharSequence, CharSequence> translation = new HashMap<>();
    translation.put("e", "3");
    translation.put("l", "1");
    translation.put("t", "7");

    String s1 = "Let it be!";

    LookupTranslator lookupTranslator = new LookupTranslator(translation);

<!-- -->

    :::text
    L37 i7 b3!

or to convert a string into Unicode characters and viceversa:

    :::java
    String s1 = "Let it be!";

    UnicodeEscaper unicodeEscaper = new UnicodeEscaper();
    UnicodeUnescaper unicodeUnescaper = new UnicodeUnescaper();

    String unicodeString = unicodeEscaper.translate(s1);

    System.out.println(unicodeString);
    System.out.println(unicodeUnescaper.translate(unicodeString));

<!-- -->

    :::text
    \u004C\u0065\u0074\u0020\u0069\u0074\u0020\u0062\u0065\u0021
    Let it be!

### The `text.similarity` package

The classes contained in this package let us perform some basic data integration tasks by giving us a measure of how close two strings are; this is done by introducing the concepts of _string distance_ and _string similarity_.

A string distance is a metric that obeys the usual metric axioms:

- _d(a, b) >= 0_ (non-negativity axiom: a distance cannot be negative);
- _d(a, b) = 0_ if and only if _a = b_ (identity axiom);
- _d(a, b) = d(b, a)_ (symmetry axiom);
- triangle inequality: _d(a, c) ≤ d(a, b) + d(b, c)_.

A string similarity measure is more "relaxed" than a metric distance since it does neither enforce the triangle inequality nor the identity axiom. Keeping this in mind, the [Jaro-Winkler distance](https://en.wikipedia.org/wiki/Jaro%E2%80%93Winkler_distance), for instance, is not strictly a metric distance but rather a similarity measure; nevertheless, it is common to refer to it as a distance in terms of "complement of similarity", i.e. _distance = 1 - similarity_. Another thing worth noting is that all the distances and similarities in Commons Text are based on characters except for the _cosine_ distance and similarity, which is based on _words_ (or _tokens_).

There are many things to consider when choosing what the most appropriate similarity measure could be for a certain use case, although some [general suggestions](https://www.kdnuggets.com/2019/01/comparison-text-distance-metrics.html) can be made; furthermore, for even more string similarity goodness, other Java libraries such as [this one](https://github.com/tdebatty/java-string-similarity) should be checked out.

#### String similarity

In the following examples we will use the two strings `s1 = "hyperspace"` and `s2 = "cyberscape"`. The available similarity measures are:

- the [Jaccard similarity](https://en.wikipedia.org/wiki/Jaccard_index), which captures the number of common characters (here `a`, `c`, `e`, `p`, `r`, `s`, `y`) divided by the number of all characters (here `a`, `b`, `c`, `e`, `h`, `p`, `r`, `s`, `y`), hence _7 / 9 = 0.777777..._:

        :::java
        JaccardSimilarity jaccard = new JaccardSimilarity();
        System.out.println("Jaccard similarity: " + jaccard.apply(s1, s2));

    <!-- -->

        :::text
        Jaccard similarity: 0.7777777777777778

- the [Jaro-Winkler similarity](https://en.wikipedia.org/wiki/Jaro%E2%80%93Winkler_distance), which takes into account both matching characters and transpositions correcting them with a scaling factor:

        :::java
        JaroWinklerSimilarity jaroWinkler = new JaroWinklerSimilarity();
        System.out.println("Jaro-Winkler similarity: " + jaroWinkler.apply(s1, s2));

    <!-- -->

        :::text
        Jaro-Winkler similarity: 0.8250000000000001

- the [longest common subsequence (LCS)](https://en.wikipedia.org/wiki/Longest_common_subsequence_problem), which finds the longest sequence of characters (not necessarily adjacent), which in this case would be `y, e, r, s, a, e` of length 6:

        :::java
        LongestCommonSubsequence lcs = new LongestCommonSubsequence();
        System.out.println("Longest Common Subsequence similarity: " + lcs.apply(s1, s2));

    <!-- -->

        :::text
        Longest Common Subsequence similarity: 6


- the fuzzy score, a custom matching algorithm based on a specific locale (for lowercasing), where one point is given for every matched character and subsequent matches yield two bonus points; the second string is treated as a query on the first string, so long common character sequences get a higher score:

        :::java
        FuzzyScore fuzzyScore = new FuzzyScore(Locale.ENGLISH);
        System.out.println("Fuzzy score similarity: " + fuzzyScore.fuzzyScore(s1, s2));
        System.out.println("Fuzzy score similarity: " + fuzzyScore.fuzzyScore(s1, "space"));

    <!-- -->

        :::text
        Fuzzy score similarity: 1
        Fuzzy score similarity: 13

#### Token similarity

The similarity measures we have seen so far can be used on any string because they are based on single characters; what if instead we want to measure the similarity between _sentences_, i.e. combinations of words (or _tokens_) separated by a delimiter such as whitespace? Although a string itself can be seen as a sequence of one-character tokens, tokens usually consist of few characters; therefore, a token distance will look at tokens as the base elements to compare.

The only token similarity measure that Commons Text offers out of the box is the [cosine similarity](https://en.wikipedia.org/wiki/Cosine_similarity), which works on _vectors_ of tokens (along with their counts) by multiplying them using the [dot product](https://en.wikipedia.org/wiki/Dot_product) and dividing the result by the product of their norms. In order to understand how it works, we need to tokenize and transform a sentence into vectors:

    :::java
    String s1 = "string similarity";
    String s2 = "string distance";

    Map<CharSequence, Integer> vector1 = new HashMap<>();
    Map<CharSequence, Integer> vector2 = new HashMap<>();

    for (String token : s1.split(" ")) {
        vector1.put(token, vector1.getOrDefault(token, 0) + 1);
    }

    for (String token : s2.split(" ")) {
        vector2.put(token, vector2.getOrDefault(token, 0) + 1);
    }

Once we have the two vectors, we can just call the `cosineSimilarity` method from a `CosineSimilarity` instance:

    :::java
    CosineSimilarity cosine = new CosineSimilarity();
    System.out.println("Cosine similarity: " + cosine.cosineSimilarity(vector1, vector2));

<!-- -->

    :::text
    Cosine similarity: 0.4999999999999999

The result (besides rounding errors) is 0.5, because we have:

- two vectors of length 3 (because there are 3 different tokens);
- each vector has two elements whose value is 1 (as each token appears once in each sentence) and one element whose value is 0 (e.g. `"similarity"` is not included in the second sentence, and `"distance"` is not included in the first);
- the dot product of the vectors `[1, 1, 0]` and `[1, 0, 1]` is equal to 1;
- the norm of each vector (square root of the sum of each element squared) is equal to the square root of 2 (about 1.414), so their product is equal to 2;
- the cosine similarity, which is the dot product divided by the product of the norms, is _1 / 2 = 0.5_.

If we add one more `"string"` token to the second vector (thus representing a sentence like `"string distance string"`) the cosine similarity will change, because the second vector will become `[2, 0, 1]` with norm equal to the square root of 5 (about 2.236), and the dot product will become 2, hence the cosine similarity _2 / (1.414 * 2.236) = 0.632..._:

    :::java
    vector2.put("string", vector2.getOrDefault("string", 0) + 1);
    System.out.println("Cosine similarity: " + cosine.cosineSimilarity(vector1, vector2));

<!-- -->

    :::text
    Cosine similarity: 0.6324555320336759

#### String distance

Given again the two strings `s1 = "hyperspace"` and `s2 = "cyberscape"`, we have the following string distances:

- the [Hamming distance](https://en.wikipedia.org/wiki/Hamming_distance), i.e. the number of different characters (which requires the strings to be compared to be of equal length):

        :::java
        HammingDistance hamming = new HammingDistance();
        System.out.println("Hamming distance: " + hamming.apply(s1, s2));

    <!-- -->

        :::text
        Hamming distance: 4

- the Jaccard distance, defined as _1 - Jaccard similarity_, hence _1 - 0.777777... = 0.222222..._:

        :::java
        JaccardDistance jaccard = new JaccardDistance();
        System.out.println("Jaccard distance: " + jaccard.apply(s1, s2));

    <!-- -->

        :::text
        Jaccard distance: 0.2222222222222222

- the Jaro-Winkler distance, defined as _1 - Jaro-Winkler similarity_, hence it should be _1 - 0.825 = 0.175_ **but it is not** at the moment (see the [Jira ticket](https://issues.apache.org/jira/browse/TEXT-104)):

        :::java
        JaroWinklerDistance jaroWinkler = new JaroWinklerDistance();
        System.out.println("Jaro-Winkler distance: " + jaroWinkler.apply(s1, s2));

    <!-- -->

        :::text
        Jaro-Winkler distance: 0.8250000000000001

- the longest common subsequence (LCS) distance, defined as the difference between the sum of the lengths of the compared strings minus twice their LCS similarity, hence _10 + 10 - 2 * 6 = 8_:

        :::java
        LongestCommonSubsequenceDistance lcs = new LongestCommonSubsequenceDistance();
        System.out.println("Longest Common Subsequence distance: " + lcs.apply(s1, s2));

    <!-- -->

        :::text
        Longest Common Subsequence distance: 8

- the well-known [Levenshtein distance](https://en.wikipedia.org/wiki/Levenshtein_distance), which takes into account character additions, deletions and substitutions:

        :::java
        LevenshteinDistance levenshtein = new LevenshteinDistance();
        System.out.println("Levenshtein distance: " + levenshtein.apply(s1, s2));

    <!-- -->

        :::text
        Levenshtein distance: 4

    and can be parameterized with a threshold above which the distance will be returned as -1:

        :::java
        LevenshteinDistance levenshteinWithThreshold = new LevenshteinDistance(3);
        // Returns -1 since the actual distance, 4, is higher than the threshold
        System.out.println("Levenshtein distance: " + levenshteinWithThreshold.apply(s1, s2));

    <!-- -->

        :::text
        Levenshtein distance: -1

    or used with its `Detailed` version to retrieve the details of the calculation:

        :::java
        LevenshteinDetailedDistance levenshteinDetailed = new LevenshteinDetailedDistance();
        System.out.println("Levenshtein detailed distance: " + levenshteinDetailed.apply(s1, s2));

    <!-- -->

        :::text
        Levenshtein detailed distance: Distance: 4, Insert: 0, Delete: 0, Substitute: 4

#### Token distance

The only available token distance is the cosine distance, simply defined as _1 - cosine similarity_. Building from the previous examples with `s1 = "string similarity"` and `s2 = "string distance"`, where the cosine similarity were 0.5 and about 0.632 respectively, we will have a cosine distance of 0.5 and about 0.368 respectively:

    :::java
    CosineDistance cosine = new CosineDistance();
    System.out.println("Cosine distance: " + cosine.apply(s1, s2));
    System.out.println("Cosine distance: " + cosine.apply(s1, s2 + " string"));

<!-- -->

    :::text
    Cosine distance: 0.5000000000000001
    Cosine distance: 0.3675444679663241

The `CosineDistance` class tokenizes the sentences before calculating the similarity; the tokenization process is similar to what we did in our token similarity example (although it uses a different regex).

### Conclusions

Commons Text is a very feature-rich library for string processing, and should be part of everybody's toolkit since it can save from reinventing the wheel in many occasions. It may sometimes be difficult to understand the design choices behind the grouping of some classes and methods, but the library is actively developed and different solutions may be added in future releases.