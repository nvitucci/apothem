Title: Apache Commons Numbers
Date: 2020-09-28
Category: projects
Tags: library, Apache Commons, numbers, math
Status: published

Although Java is probably not the first programming language to come to mind for scientific computing, there are several projects and libraries that try to bridge the gap. One prominent example is from the [Apache Commons](https://commons.apache.org/) project: [Apache Commons Math](https://commons.apache.org/proper/commons-math/), a group of specialized mathematics and statistics components, has been introduced in 2004 and is now at its 3.6.1 stable release, with version 4.0 still under development. The library includes a large number of components, ranging from linear algebra to geometry, from ordinary differential equations to complex numbers, and so on.

The difficulty in maintaining the balance between backwards compatibility and adding improvements or new functionalities has inspired the creation of lower level libraries that contain only specific components (numbers, geometric primitives, etc.) and, as such, are smaller and easier to maintain. The library that we will explore in this article, [Apache Commons Numbers](https://commons.apache.org/proper/commons-numbers/), is dedicated to different types of numbers (fractions, angles, complex numbers, etc.), while other libraries have been created in a similar fashion for [geometry](https://commons.apache.org/proper/commons-geometry/), [statistics](https://commons.apache.org/proper/commons-statistics/), and [random numbers generation](https://commons.apache.org/proper/commons-rng/). Given that the documentation is still at a very early stage for Numbers, hopefully this review will be useful to the library developers too.

[TOC]

### Setting up

The Commons Numbers library is currently in [beta stage](https://en.wikipedia.org/wiki/Software_release_life_cycle#Beta), basically meaning that it is still being tested and subject to change. While we would usually start exploring a library from its stable version and possibly add some observations about the development version, since there is no stable release for Numbers we will use the beta version throughout.

As we have done in the [Apache Commons CLI article]({filename}/articles/commons_cli.md), we will use the library by means of a `pom.xml` file. Since we need to add several components, it is more practical to also set a `commons.numbers.version` property that can be updated at once, for instance when a first release becomes available. The POM file may look like the following:

    :::xml

    <groupId>blog.apothem</groupId>
    <artifactId>apache-commons-numbers-example</artifactId>
    <version>0.0.1-SNAPSHOT</version>

    <properties>
        <commons.numbers.version>1.0-beta1</commons.numbers.version>
    </properties>

    <dependencies>
        <dependency>
            <groupId>org.apache.commons</groupId>
            <artifactId>commons-numbers-core</artifactId>
            <version>${commons.numbers.version}</version>
        </dependency>
        <dependency>
            <groupId>org.apache.commons</groupId>
            <artifactId>commons-numbers-angle</artifactId>
            <version>${commons.numbers.version}</version>
        </dependency>
        <dependency>
            <groupId>org.apache.commons</groupId>
            <artifactId>commons-numbers-arrays</artifactId>
            <version>${commons.numbers.version}</version>
        </dependency>
        <dependency>
            <groupId>org.apache.commons</groupId>
            <artifactId>commons-numbers-combinatorics</artifactId>
            <version>${commons.numbers.version}</version>
        </dependency>
        <dependency>
            <groupId>org.apache.commons</groupId>
            <artifactId>commons-numbers-complex</artifactId>
            <version>${commons.numbers.version}</version>
        </dependency>
        <dependency>
            <groupId>org.apache.commons</groupId>
            <artifactId>commons-numbers-fraction</artifactId>
            <version>${commons.numbers.version}</version>
        </dependency>
        <dependency>
            <groupId>org.apache.commons</groupId>
            <artifactId>commons-numbers-gamma</artifactId>
            <version>${commons.numbers.version}</version>
        </dependency>
        <dependency>
            <groupId>org.apache.commons</groupId>
            <artifactId>commons-numbers-primes</artifactId>
            <version>${commons.numbers.version}</version>
        </dependency>
        <dependency>
            <groupId>org.apache.commons</groupId>
            <artifactId>commons-numbers-quaternion</artifactId>
            <version>${commons.numbers.version}</version>
        </dependency>
    </dependencies>

Again, we will create a class with a `main` method and write the entire code there; the complete code is available as always in the companion [Apothem resources repository](https://github.com/nvitucci/apothem-resources/tree/master/apache-commons-numbers).

For the time being, I am skipping two components of the library, namely `Field` and `RootFinder`, since it is more difficult to create easy examples for both; I might add them as an update later on.

### Modules

In this section we will explore each component with code examples.

#### `Core`
The `Core` package contains some of the interfaces used throughout the library, but most importantly it contains some number-related utilities as static methods within the `core.ArithmeticUtils` and `core.Precision` classes. For instance, given two integer numbers $x = 256$ and $y = 6$, we can:

- calculate the (unsigned) quotient and reminder of the division $x / y$:

        :::java
        int x = 256;
        int y = 6;

        System.out.printf("%d / %d = %d%n",
                x, y, ArithmeticUtils.divideUnsigned(x, y));
        System.out.printf("%d %% %d = %d%n",
                x, y, ArithmeticUtils.remainderUnsigned(x, y));

    <!-- -->

        :::text
        256 / 6 = 42
        256 % 6 = 4

- find the [greatest common divisor](https://en.wikipedia.org/wiki/Greatest_common_divisor) (gcd) and the [least common multiple](https://en.wikipedia.org/wiki/Least_common_multiple) (lcm) between $x$ and $y$:

        :::java
        System.out.printf("gcd(%d, %d) = %d%n",
                x, y, ArithmeticUtils.gcd(x, y));
        System.out.printf("lcm(%d, %d) = %d%n",
                x, y, ArithmeticUtils.lcm(x, y));

    <!-- -->

        :::text
        gcd(256, 6) = 2
        lcm(256, 6) = 768

- calculate the powers $x^2$ and $x^y$, where the second one needs a cast to `BigInteger` since the result is too large to be contained in a `long`:

        :::java
        System.out.printf("%d ^ %d = %d%n",
                x, 2, ArithmeticUtils.pow(x, 2));
        System.out.printf("%d ^ %d = %d%n",
                x, y, ArithmeticUtils.pow(BigInteger.valueOf(x), y));

    <!-- -->

        :::text
        256 ^ 2 = 65536
        256 ^ 6 = 281474976710656

- check whether $x$ and $x + 1$ are powers of 2:

        :::java
        System.out.printf("Is %d a power of 2? %b%n",
                x, ArithmeticUtils.isPowerOfTwo(x));
        System.out.printf("Is %d + 1 a power of 2? %b%n",
                x, ArithmeticUtils.isPowerOfTwo(x + 1));

    <!-- -->

        :::text
        Is 256 a power of 2? true
        Is 256 + 1 a power of 2? false

Using the methods from the `core.Precision` class, given a decimal number $x = 1.23456789$ we can:

- round it to 2, 4 and 6 places:

        :::java
        double x = 1.23456789;

        for (int places : Arrays.asList(2, 4, 6)) {
            System.out.printf("Rounding %f to %d places = %f%n",
                    x, places, Precision.round(x, places));
        }

    <!-- -->

        :::text
        Rounding 1.234568 to 2 places = 1.230000
        Rounding 1.234568 to 4 places = 1.234600
        Rounding 1.234568 to 6 places = 1.234568

- check that it is equal to $x + 10^{-6}$ up to a certain precision $\epsilon$:

        :::java
        for (double eps : Arrays.asList(1e-3, 1e-6, 1e-9)) {
            System.out.printf("%.9f == %.9f (up to %e)? %b%n",
                    x, x + 1e-6, eps, Precision.equals(x, x + 1e-6, eps));
        }

    <!-- -->

        :::text
        1.234567890 == 1.234568890 (up to 1.000000e-03)? true
        1.234567890 == 1.234568890 (up to 1.000000e-06)? true
        1.234567890 == 1.234568890 (up to 1.000000e-09)? false

- check whether two `NaN`s are equal, using both the same `equals` method and the `equalsIncludingNaN` method which takes `NaN`s into account:

        :::java

        double nan = Double.NaN;
        double inf = Double.POSITIVE_INFINITY;

        System.out.printf("%f == %f? %b%n",
                nan, nan, Precision.equals(nan, nan));
        System.out.printf("%f - %f == %f - %f? %b%n",
                inf, inf, inf, inf, Precision.equals(inf - inf, inf - inf));
        System.out.printf("%f == %f (including NaN)? %b%n",
                nan, nan, Precision.equalsIncludingNaN(nan, nan));
        System.out.printf("%f - %f == %f - %f (including NaN)? %b%n",
                inf, inf, inf, inf, Precision.equalsIncludingNaN(inf - inf, inf - inf));

    <!-- -->

        :::text
        NaN == NaN? false
        Infinity - Infinity == Infinity - Infinity? false
        NaN == NaN (including NaN)? true
        Infinity - Infinity == Infinity - Infinity (including NaN)? true

#### `Arrays`

This package can be used for basic linear algebra operations, such as:

- calculating the norm of a vector (which is called `SafeNorm` but could probably just be called `Norm`, as there is no other norm defined):

        :::java
        double[] array1 = {0.1, 0.4, 0.1};

        System.out.printf("Norm of %s = %f%n",
                Arrays.toString(array1), SafeNorm.value(array1));

    <!-- -->

        :::text
        Norm of [0.1, 0.4, 0.1] = 0.424264

- calculating the [cosine similiarity](https://en.wikipedia.org/wiki/Cosine_similarity) and the [dot product](https://en.wikipedia.org/wiki/Dot_product) between two vectors:

        :::java
        double[] array2 = {-0.1, -0.4, -0.1};

        System.out.printf("Angle between %s and %s = %f%n",
                Arrays.toString(array1), Arrays.toString(array2), CosAngle.value(array1, array2));
        System.out.printf("dot(%s, %s) = %f%n",
                Arrays.toString(array1), Arrays.toString(array2), LinearCombination.value(array1, array2));

    <!-- -->

        :::text
        Angle between [0.1, 0.4, 0.1] and [-0.1, -0.4, -0.1] = -1.000000
        dot([0.1, 0.4, 0.1], [-0.1, -0.4, -0.1]) = -0.180000

- converting the index of a multidimensional array from a multidimensional index (e.g. _(1, 3, 2)_) to a unidimensional (linear) index (e.g. _23_) and vice versa, with the conversion logic explained in the [class Javadoc](https://commons.apache.org/proper/commons-numbers/commons-numbers-arrays/apidocs/org/apache/commons/numbers/arrays/MultidimensionalCounter.html):

        :::java
        MultidimensionalCounter counter = MultidimensionalCounter.of(4, 4, 3);
        int pos = 23;
        int[] index = {1, 3, 2};

        System.out.printf("Array of dimensions %s: position %d corresponds to index %s%n",
                Arrays.toString(counter.getSizes()), pos, Arrays.toString(counter.toMulti(pos)));
        System.out.printf("Array of dimensions %s: index %s corresponds to position %d%n",
                Arrays.toString(counter.getSizes()), Arrays.toString(index), counter.toUni(index));

    <!-- -->

        :::text
        Array of dimensions [4, 4, 3]: position 23 corresponds to index [1, 3, 2]
        Array of dimensions [4, 4, 3]: index [1, 3, 2] corresponds to position 23

It could be useful if some vector algebra functions were added (such as vector sum and scaling), although more sophisticated operations would probably be better left as part of a linear algebra-focused library.

#### `Complex`

This package contains definitions and methods for complex numbers, a type of number that is frequently used in physics and engineering. A complex number can be created in three different ways:

- using the cartesian coordinates, so $z = a + b * i$ would be expressed as the tuple $(a, b)$;
- using the polar coordinates, so $z = \rho * (cos(\theta) + i * sin(\theta))$ would be expressed as the tuple $(\rho, \theta)$ and, to convert from cartesian coordinates, $\rho = \sqrt{a^2 + b^2}$ and $\theta = atan2(a, b)$;
- using the cis (**c**os + **i s**in) form, so $z = cos(x) + i * sin(x)$ and, equivalently, $z = e^{ix}$ would be expressed by the single number $x$.

These three methods can be implemented as in the following example:

    :::java
    Complex z = Complex.ofCartesian(1, 1);
    Complex z2 = Complex.ofPolar(Math.sqrt(2), Math.PI / 4);
    Complex z3 = Complex.ofCis(Math.PI);

    System.out.printf("z: %s, z2: %s, z3: %s%n",
            z, z2, z3);

<!-- -->

    :::text
    z: (1.0,1.0), z2: (1.0000000000000002,1.0), z3: (-1.0,1.2246467991473532E-16)

We can see that, although they should theoretically be the same, $z$ and $z_2$ are not considered equal due to numerical instability:

    :::java
    System.out.printf("%s == %s? %b%n",
        z, z2, z.equals(z2));

<!-- -->

    :::text
    (1.0,1.0) == (1.0000000000000002,1.0)? false


For this reason, it would be useful to have an "almost equals" method available for complex numbers too. However, there are many other methods that, given a complex number, can:

- extract its real and imaginary part, its absolute value and its argument;
- calculate its conjugate and its squared norm;
- calculate the value of several trigonometric functions.

Examples:

    :::java
    System.out.printf("Given z = %s:%n", z);
    System.out.printf("\tRe(z) = %s, Im(z) = %s%n",
            z.real(), z.imag());
    System.out.printf("\tabs(z) = %s, arg(z) = %s%n",
            z.abs(), z.arg());
    System.out.printf("\tconj(z) = %s%n", z.conj());
    System.out.printf("\tnorm(z) = %f%n", z.norm());
    System.out.printf("\tasin(z) = %s%n", z.asin());
    System.out.printf("\tacos(z) = %s%n", z.acos());
    System.out.printf("\tatan(z) = %s%n", z.atan());
    System.out.printf("\tasinh(z) = %s%n", z.asinh());
    System.out.printf("\tacosh(z) = %s%n", z.acosh());
    System.out.printf("\tatanh(z) = %s%n", z.atanh());

<!-- -->

    :::text
    Given z = (1.0,1.0):
        	Re(z) = 1.0, Im(z) = 1.0
        	abs(z) = 1.4142135623730951, arg(z) = 0.7853981633974483
        	conj(z) = (1.0,-1.0)
        	norm(z) = 2.000000
        	asin(z) = (0.6662394324925152,1.0612750619050357)
        	acos(z) = (0.9045568943023814,-1.0612750619050357)
        	atan(z) = (1.0172219678978514,0.40235947810852507)
        	asinh(z) = (1.0612750619050357,0.6662394324925152)
        	acosh(z) = (1.0612750619050357,0.9045568943023814)
        	atanh(z) = (0.40235947810852507,1.0172219678978514)

Furthermore, given two complex numbers, it is possible to add, subtract, multiply, and divide them, and raise one to the power of the other one:

    :::java
    System.out.printf("Given z = %s anz z2 = %s:%n", z, z2);
    System.out.printf("\tz + z2 = %s%n", z.add(z2));
    System.out.printf("\tz - z2 = %s%n", z.subtract(z2));
    System.out.printf("\tz * z2 = %s%n", z.multiply(z2));
    System.out.printf("\tz / z2 = %s%n", z.divide(z2));
    System.out.printf("\tz ^ z2 = %s%n", z.pow(z2));

<!-- -->

    :::text
    Given z = (1.0,1.0) anz z2 = (1.0000000000000002,1.0):
        	z + z2 = (2.0,2.0)
        	z - z2 = (-2.220446049250313E-16,0.0)
        	z * z2 = (2.220446049250313E-16,2.0)
        	z / z2 = (0.9999999999999998,1.1102230246251563E-16)
        	z ^ z2 = (0.273957253830121,0.5837007587586148)

Using the previously seen `Precision.equals` method, we can even show [Euler's identity](https://en.wikipedia.org/wiki/Euler%27s_identity) for $z = e^{i\pi}$:

    :::java
    double eps = 1e-15;
    System.out.printf("Re(%s) == -1 up to %s? %b%n",
            z3, eps, Precision.equals(z3.real(), -1, eps));
    System.out.printf("Im(%s) == 0 up to %s? %b%n",
            z3, eps, Precision.equals(z3.imag(), 0, eps));

<!-- -->

    :::text
    Re((-1.0,1.2246467991473532E-16)) == -1 up to 1.0E-15? true
    Im((-1.0,1.2246467991473532E-16)) == 0 up to 1.0E-15? true

#### `Angle`

This package can be used to define angles from different units of measurement, namely degrees, radians, and turns (where 1 turn = 360 degrees):

    :::java
    PlaneAngle alpha = PlaneAngle.ofDegrees(180);
    PlaneAngle beta = PlaneAngle.ofRadians(Math.PI);

    System.out.printf("Angle alpha in degrees: %f%n",
            alpha.toDegrees());
    System.out.printf("Angle alpha in radians: %f%n",
            alpha.toRadians());
    System.out.printf("Angle alpha in turns: %f%n",
            alpha.toTurns());

    System.out.printf("Angle beta in degrees: %f%n",
            alpha.toDegrees());
    System.out.printf("Angle beta in radians: %f%n",
            alpha.toRadians());
    System.out.printf("Angle beta in turns: %f%n",
            alpha.toTurns());

<!-- -->

    :::text
    Angle alpha in degrees: 180.000000
    Angle alpha in radians: 3.141593
    Angle alpha in turns: 0.500000
    Angle beta in degrees: 180.000000
    Angle beta in radians: 3.141593
    Angle beta in turns: 0.500000

Angles can also be compared for equality:

    :::java
    System.out.printf("Are angles alpha and beta equal? %b%n",
            alpha.equals(beta));

<!-- -->

    :::text
    Are angles alpha and beta equal? true

The package is currently missing operations between angles, such as addition and multiplication by scalars.

#### `Fraction`

This package can be used to define fractions, where instead of a (possibly approximate) decimal value we want to use a rational number and perform operations on it. Fractions can be created from a numerator and a denominator or from a decimal value, in which case the denominator can optionally be limited to a maximum (useful to adjust the precision of the conversion):

    :::java
    List<Fraction> fractions = Arrays.asList(
            Fraction.of(4, 9),
            Fraction.of(1, 2),
            Fraction.from(0.99245),
            Fraction.from(0.99245, 10000000));

    System.out.printf("Fractions: %s%n",
            fractions.stream().map(Fraction::toString).collect(Collectors.joining(" ; ")));

<!-- -->

    :::text
    Fractions: 4 / 9 ; 1 / 2 ; 263 / 265 ; 19849 / 20000

A fraction can be:

- decomposed into numerator and denominator;
- converted to a decimal number;
- converted to its reciprocal;
- negated;
- raised to a power.

Examples:

    :::java
    System.out.printf("The fraction %s has numerator %d and denominator %d%n",
            fractions.get(0), fractions.get(0).getNumerator(), fractions.get(0).getDenominator());
    System.out.printf("%s as a decimal number: %f%n",
            fractions.get(0), fractions.get(0).doubleValue());
    System.out.printf("Reciprocal of %s: %s%n",
            fractions.get(0), fractions.get(0).reciprocal());
    System.out.printf("Additive inverse of %s: %s%n",
            fractions.get(0), fractions.get(0).negate());
    System.out.printf("(%s) ^ 3 = %s%n",
            fractions.get(0), fractions.get(0).pow(3));

<!-- -->

    :::text
    The fraction 4 / 9 has numerator 4 and denominator 9
    4 / 9 as a decimal number: 0.444444
    Reciprocal of 4 / 9: 9 / 4
    Additive inverse of 4 / 9: -4 / 9
    (4 / 9) ^ 3 = 64 / 729

A fraction can be added, subtracted, multiplied, and divided by another one:

    :::java
    System.out.printf("(%s) + (%s) = %s%n",
            fractions.get(0), fractions.get(1), fractions.get(0).add(fractions.get(1)));
    System.out.printf("(%s) - (%s) = %s%n",
            fractions.get(0), fractions.get(1), fractions.get(0).subtract(fractions.get(1)));
    System.out.printf("(%s) * (%s) = %s%n",
            fractions.get(0), fractions.get(1), fractions.get(0).multiply(fractions.get(1)));
    System.out.printf("(%s) / (%s) = %s%n",
            fractions.get(0), fractions.get(1), fractions.get(0).divide(fractions.get(1)));

<!-- -->

    :::text
    (4 / 9) + (1 / 2) = 17 / 18
    (4 / 9) - (1 / 2) = -1 / 18
    (4 / 9) * (1 / 2) = 2 / 9
    (4 / 9) / (1 / 2) = 8 / 9

#### `Primes`

This package is dedicated to [prime numbers](https://en.wikipedia.org/wiki/Prime_number), a class of numbers with many applications especially in cryptography. The `Primes` class has methods to determine whether a number is prime, to find the closest prime to a number, and to decompose a number into prime factors:

    :::java
    for (int n : Arrays.asList(2, 4, 42)) {
        System.out.printf("Is %d prime? %b%n",
                n, Primes.isPrime(n));
        System.out.printf("What is the closest prime to %d? %d%n",
                n, Primes.nextPrime(n)); // Note: why is it 2 when n = 2?
        System.out.printf("Prime factors of %d: %s%n",
                n, Primes.primeFactors(n));
    }

<!-- -->

    :::text
    Is 2 prime? true
    What is the closest prime to 2? 2
    Prime factors of 2: [2]
    Is 4 prime? false
    What is the closest prime to 4? 5
    Prime factors of 4: [2, 2]
    Is 42 prime? false
    What is the closest prime to 42? 43
    Prime factors of 42: [2, 3, 7]

#### `Quaternion`

This package introduces the concept of [quaternion](https://en.wikipedia.org/wiki/Quaternion), an extension to complex numbers that is widely used in computer graphics and robotics due to its convenience in implementing rotations around multiple axes. A quaternion is composed of two parts, a scalar and a tridimensional vector; it can therefore be created with different methods, where the simplest one sets the scalar part to zero (thus creating a so-called _pure quaternion_):

    :::java
    List<Quaternion> quaternions = Arrays.asList(
            Quaternion.of(new double[]{1, 1, 1}),
            Quaternion.of(2, new double[]{1, 1, 1}),
            Quaternion.of(0.5, 1, 1, 1));

Each quaternion can be:

- checked for "pureness";
- conjugated;
- inverted;
- normalized (as a versor) or converted to positive polar form (defined as "the unit quaternion with positive scalar part", although this could be made more clear);
- divided by a scalar, for instance by its own norm (to check that the normalization method yields the correct result).

Examples:

    :::java
    for (Quaternion q : quaternions) {
        System.out.printf("Quaternion %s%n", q);
        System.out.printf("\tIs it pure (up to 1e-10)? %b%n",
                q.isPure(1e-10));
        System.out.printf("\tConjugate: %s%n",
                q.conjugate());
        System.out.printf("\tInverse: %s%n",
                q.inverse());
        System.out.printf("\tNormalized form: %s%n",
                q.normalize());
        System.out.printf("\tPositive polar form: %s%n",
                q.positivePolarForm());
        System.out.printf("\tQuaternion divided by its norm %f: %s%n",
                q.norm(), q.divide(q.norm()));
    }

<!-- -->

    :::text
    Quaternion [0.0 1.0 1.0 1.0]
        	Is it pure (up to 1e-10)? true
    		Conjugate: [0.0 -1.0 -1.0 -1.0]
        	Inverse: [0.0 -0.3333333333333333 -0.3333333333333333 -0.3333333333333333]
        	Normalized form: [0.0 0.5773502691896258 0.5773502691896258 0.5773502691896258]
        	Positive polar form: [0.0 0.5773502691896258 0.5773502691896258 0.5773502691896258]
        	Quaternion divided by its norm 1.732051: [0.0 0.5773502691896258 0.5773502691896258 0.5773502691896258]
    Quaternion [2.0 1.0 1.0 1.0]
        	Is it pure (up to 1e-10)? false
        	Conjugate: [2.0 -1.0 -1.0 -1.0]
        	Inverse: [0.2857142857142857 -0.14285714285714285 -0.14285714285714285 -0.14285714285714285]
        	Normalized form: [0.7559289460184544 0.3779644730092272 0.3779644730092272 0.3779644730092272]
        	Positive polar form: [0.7559289460184544 0.3779644730092272 0.3779644730092272 0.3779644730092272]
        	Quaternion divided by its norm 2.645751: [0.7559289460184544 0.3779644730092272 0.3779644730092272 0.3779644730092272]
    Quaternion [0.5 1.0 1.0 1.0]
        	Is it pure (up to 1e-10)? false
        	Conjugate: [0.5 -1.0 -1.0 -1.0]
        	Inverse: [0.15384615384615385 -0.3076923076923077 -0.3076923076923077 -0.3076923076923077]
        	Normalized form: [0.2773500981126146 0.5547001962252291 0.5547001962252291 0.5547001962252291]
        	Positive polar form: [0.2773500981126146 0.5547001962252291 0.5547001962252291 0.5547001962252291]
        	Quaternion divided by its norm 1.802776: [0.2773500981126146 0.5547001962252291 0.5547001962252291 0.5547001962252291]

Two quaternions can be added, subtracted, and multiplied (the division is only allowed by a decimal number):

    :::java
    System.out.printf("%s + %s = %s%n",
            quaternions.get(0), quaternions.get(1), quaternions.get(0).add(quaternions.get(1)));
    System.out.printf("%s - %s = %s%n",
            quaternions.get(0), quaternions.get(1), quaternions.get(0).subtract(quaternions.get(1)));
    System.out.printf("%s * %s = %s%n",
            quaternions.get(0), quaternions.get(1), quaternions.get(0).multiply(quaternions.get(1)));

<!-- -->

    :::text
    [0.0 1.0 1.0 1.0] + [2.0 1.0 1.0 1.0] = [2.0 2.0 2.0 2.0]
    [0.0 1.0 1.0 1.0] - [2.0 1.0 1.0 1.0] = [-2.0 0.0 0.0 0.0]
    [0.0 1.0 1.0 1.0] * [2.0 1.0 1.0 1.0] = [-3.0 2.0 2.0 2.0]

and it is also possible to calculate the dot product between them:

    :::java
    System.out.printf("dot(%s, %s) = %s%n",
            quaternions.get(0), quaternions.get(1), quaternions.get(0).dot(quaternions.get(1)));

<!-- -->

    :::text
    dot([0.0 1.0 1.0 1.0], [2.0 1.0 1.0 1.0]) = 3.0

For more information on how quaternion algebra works, you can check the [Wikipedia page](https://en.wikipedia.org/wiki/Quaternion).

Another interesting class from this package is `Slerp`, where the only available method `apply` is used to create a [spherical linear interpolation](https://en.wikipedia.org/wiki/Slerp) (or _slerp_) between two quaternions, with the purpose of smoothly transforming the first into the second (useful for instance in 3D-rotation animation tasks). A slerp from the special quaternion $\boldsymbol{i} = (0, 1, 0, 0)$ to the other special quaternion $\boldsymbol{j} = (0, 0, 1, 0)$ can be created as follows:

    :::java
    Slerp slerp = new Slerp(Quaternion.I, Quaternion.J);

We want the transition to take place in intervals of 0.1, so we use a `for` loop:

    :::java
    System.out.printf("Slerp demo%n");
    for (double t = 0; t <= 1.0; t += 0.1) {
        System.out.printf("\tQuaternion at t = %f: %s%n",
                t, slerp.apply(t));
    }

<!-- -->

    :::text
    Slerp demo
        	Quaternion at t = 0.000000: [0.0 1.0 0.0 0.0]
        	Quaternion at t = 0.100000: [0.0 0.9876883405951378 0.15643446504023087 0.0]
        	Quaternion at t = 0.200000: [0.0 0.9510565162951536 0.30901699437494745 0.0]
        	Quaternion at t = 0.300000: [0.0 0.8910065241883679 0.45399049973954686 0.0]
        	Quaternion at t = 0.400000: [0.0 0.8090169943749475 0.5877852522924731 0.0]
        	Quaternion at t = 0.500000: [0.0 0.7071067811865476 0.7071067811865476 0.0]
        	Quaternion at t = 0.600000: [0.0 0.5877852522924731 0.8090169943749475 0.0]
        	Quaternion at t = 0.700000: [0.0 0.45399049973954686 0.8910065241883679 0.0]
        	Quaternion at t = 0.800000: [0.0 0.3090169943749475 0.9510565162951535 0.0]
        	Quaternion at t = 0.900000: [0.0 0.15643446504023104 0.9876883405951378 0.0]
        	Quaternion at t = 1.000000: [0.0 1.743934249004316E-16 1.0 0.0]

#### `Combinatorics`

This package contains several classes for common combinatorial concepts such as [factorials](https://en.wikipedia.org/wiki/Factorial) (to calculate the number of permutations of $n$ objects) and [combinations](https://en.wikipedia.org/wiki/Combination) (to calculate the number of ways $n$ objects can be arranged in groups of $k$ objects). For example, given $n = 10$, we can calculate the factorial (as a `long` and as a `double`) and log-factorial of $n$:

    :::java
    int n = 10;

    System.out.printf("%d! = %d%n",
            n, Factorial.value(n));
    System.out.printf("%d! = %f (double)%n",
            n, FactorialDouble.create().value(n));
    System.out.printf("log(%d!) = %f%n",
            n, LogFactorial.create().value(n));

<!-- -->

    :::text
    10! = 3628800
    10! = 3628800.000000 (double)
    log(10!) = 15.104413

Furthermore, given $k = 3$, we can calculate the binomial coefficient $\binom{n}{k}$ (i.e. the number of $k$-combinations of $n$ objects), both as a `long` and as a `double`, and its logarithm:

    :::java
    int k = 3;

    System.out.printf("Binomial coefficient (%d %d) = %d%n",
            n, k, BinomialCoefficient.value(n, k));
    System.out.printf("Binomial coefficient (%d %d) = %f (double)%n",
            n, k, BinomialCoefficientDouble.value(n, k));
    System.out.printf("Log of the binomial coefficient (%d %d) = %f%n",
            n, k, LogBinomialCoefficient.value(n, k));

<!-- -->

    :::text
    Binomial coefficient (10 3) = 120
    Binomial coefficient (10 3) = 120.000000 (double)
    Log of the binomial coefficient (10 3) = 4.787492

We can also calculate the combinations themselves, take their number and show some of them:

    :::java
    Combinations comb = Combinations.of(n, k);
    List<int[]> combList = new ArrayList<>();
    for (int[] element : comb) {
        combList.add(element);
    }

    System.out.printf("Number of combinations C(%d, %d): %d%n",
            n, k, combList.size());
    System.out.printf("First three combinations: %s, %s, %s%n",
            Arrays.toString(combList.get(0)), Arrays.toString(combList.get(1)),
            Arrays.toString(combList.get(2)));

<!-- -->

    :::text
    Number of combinations C(10, 3): 120
    First three combinations: [0, 1, 2], [0, 1, 3], [0, 2, 3]

One important thing that must be noted here is the potentially large size of the numbers involved. The factorial grows very quickly, so the numbers for which the factorial can fit in a `long` are very few (just up to $n = 20$); the binomial grows quickly as well, so its input is also limited (in fact it can be calculated only for $n <= 66$). This problem can be alleviated by using approximations, either using the `Double` version of both classes (i.e. `FactorialDouble` and `BinomialCoefficientDouble`) or using their logarithmic versions (i.e. `LogFactorial` and `LogBinomialCoefficient`), which in turn use the `LogGamma` class from the `Gamma` package. It would be interesting to see also a version of `Factorial` and `BinomialCoefficient` that makes use of `BigInteger`s to allow for exact calculation on larger numbers.

#### `Gamma`

This package is very specific to a certain class of mathematical functions derived from the [gamma function](https://en.wikipedia.org/wiki/Gamma_function), including:

- the [error function](https://en.wikipedia.org/wiki/Error_function) and its inverse:

        :::java
        for (double value : Arrays.asList(1., 2., 3.)) {
            System.out.printf("erf(%f) = %f%n",
                    value, Erf.value(value));
        }

        for (double value : Arrays.asList(0.9999, 0.9953, 0.8427)) {
            System.out.printf("erf^(-1)(%f) = %f%n",
                    value, InverseErf.value(value));
        }

    <!-- -->

        :::text
        erf(1.000000) = 0.842701
        erf(2.000000) = 0.995322
        erf(3.000000) = 0.999978
        erf^(-1)(0.999900) = 2.751064
        erf^(-1)(0.995300) = 1.998925
        erf^(-1)(0.842700) = 0.999998

- the _gamma_ function itself, its derivatives _digamma_ and _trigamma_, and its logarithm _log-gamma_, which are calculated in two interesting points to show their values (with $g$ being the [Euler–Mascheroni constant](https://en.wikipedia.org/wiki/Euler%E2%80%93Mascheroni_constant)):

        :::java
        System.out.printf("Gamma(1) = %f%n",
                Gamma.value(1));
        System.out.printf("Gamma(0.5) = %f (sqrt(pi))%n",
                Gamma.value(0.5));

        System.out.printf("Digamma(1) = %f (-g)%n",
                Digamma.value(1));
        System.out.printf("Digamma(0.5) = %f (-2 * ln(2) - g)%n",
                Digamma.value(0.5));

        System.out.printf("Trigamma(1) = %f (pi ** 2 / 6)%n",
                Trigamma.value(1));
        System.out.printf("Trigamma(0.5) = %f (pi ** 2 / 2)%n",
                Trigamma.value(0.5));

        System.out.printf("log-gamma(1) = %f%n",
                LogGamma.value(1));
        System.out.printf("log-gamma(0.5) = %f (log(sqrt(pi)))%n",
                LogGamma.value(0.5));

    <!-- -->

        :::text
        gamma(1) = 1.000000
        gamma(0.5) = 1.772454 (sqrt(pi))
        digamma(1) = -0.577216 (-gamma)
        digamma(0.5) = -1.963510 (-2 * ln(2) - gamma)
        trigamma(1) = 1.644934 (pi ** 2 / 6)
        trigamma(0.5) = 4.934802 (pi ** 2 / 2)
        log-gamma(1) = -0.000000
        log-gamma(0.5) = 0.572365 (log(sqrt(pi)))

Among the packages we have seen so far, this seems less connected to the concept of "number" and closer to the concept of "function".

### Conclusions

The Commons Numbers library is a good step towards a light, easily-embeddable and general purpose number library, with many common number types (especially fractions and complex numbers) and useful utilities such as the `Precision` class. The library makes these "special" numbers quite easy to use, although Java itself is still missing a much desired feature (_operator overloading_) that would make numeric computing even more appealing.

The library could be extended to add more functionalities to some number types (e.g. more operations for angles and vectors, close equality check for complex numbers) and a better integration with `BigInteger`s, but the current beta version seems very promising.