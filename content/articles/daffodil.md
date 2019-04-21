Title: Apache Daffodil
Date: 2019-04-07
Category: projects
Tags: Big Data, library, XML, JSON

Let's start the blog with [Apache Daffodil](https://daffodil.apache.org). Daffodil presents itself as _"an open-source implementation of the Data Format Description Language to convert between fixed format data and XML/JSON"_; basically, by using Daffodil, one should be able to read data saved into an "obscure" format and convert them into an easy-to-use format, provided that a schema of the original data format is available.

Daffodil's approach is different from using a data serialization format that includes a schema (e.g. Apache Avro or Protobuf): it is _descriptive_ rather than _prescriptive_, meaning that it allows the data to be interpreted by using only additional information rather than additional software. Daffodil uses DFDL schemas to convert raw data into an abstract model called _infoset_, which can be represented in a [variety of formats](https://daffodil.apache.org/infoset/) including XML and JSON.

The main tasks that Daffodil can perform are _parsing_, _unparsing_, and _testing_ (plus a few more). Parsing is the task of converting data into one or more infosets, while unparsing is the reverse task of converting an infoset into the original format; testing uses the Test Data Markup Language (TDML) to check that parsing and unparsing work correctly, either as single tasks or in a chain. In order to parse or unparse data, we need to use a schema; some publicly available schemas can be found on [Github](https://github.com/DFDLSchemas), but most likely a custom schema needs to be developed for a specific dataset.

Let's see now how the whole machinery works. In the following I will assume that you are using a Linux environment and that you are starting from scratch. You should be able to follow the same steps on MacOS, while if you are using Windows you might need to perform some of the steps manually or to write some additional code (for instance, some Java or Python code to preprocess the files); as an alternative, you can just use the [associated repo](https://github.com/nvitucci/apothem-resources) where you will find all the files you need.

### Example data

Since I am a sort of astronomy geek, I used the [Bright Star Catalogue](http://tdc-www.harvard.edu/catalogs/bsc5.html) as an example data source. The BSC is a catalog of more than 9,000 objects visible to the naked eye, delivered as a compressed fixed-length format file with many fields of different types (see the section _"Byte-by-byte Description of file: catalog"_ of the [bsc5.readme](http://tdc-www.harvard.edu/catalogs/bsc5.readme) file). Since it does not use separators, we cannot parse it as a CSV-like file; we need to parse it in a different way. Let's [download](http://tdc-www.harvard.edu/catalogs/bsc5.dat.gz) and decompress it:

    :::bash
    $ wget -q http://tdc-www.harvard.edu/catalogs/bsc5.dat.gz
    $ gunzip bsc5.dat.gz

We can check how the file looks like:

    :::text
    $ head bsc5.dat
       1          BD+44 4550      3 36042          46           000001.1+444022000509.9+451345114.44-16.88 6.70  +0.07 +0.08         A1Vn               -0.012-0.018      -018      195  4.2  21.6AC   3
       2          BD-01 4525      6128569                       235956.2-010330000503.8-003011 98.33-61.14 6.29  +1.10 +1.02        gG9                 +0.045-0.060      +014V
       3 33    PscBD-06 6357     281285721002I         Var?     000013.0-061601000520.1-054227 93.75-65.93 4.61  +1.04 +0.89 +0.54   K0IIIbCN-0.5       -0.009+0.089 +.014-006SB1O < 17  2.5   0.0     3*
       4 86    PegBD+12 5063     87 917012004                   000033.8+125023000542.0+132346106.19-47.98 5.51  +0.90               G5III              +0.045-0.012      -002V?
       5          BD+57 2865    123 21085          61  V640 Cas 000101.8+575245000616.0+582612117.03-03.92 5.96  +0.67 +0.20         G5V                +0.263+0.030 +.047-012V          0.8   1.4      *
       6          CD-4914337    142214963      W                000108.4-493751000619.0-490430321.61-66.38 5.70  +0.52 +0.05         G1IV               +0.565-0.038 +.050+003SB         5.7   5.4      *
       7 10    CasBD+63 2107    144 109782005                   000114.4+633822000626.5+641146118.06  1.75 5.59  -0.03 -0.19         B9III             e+0.008 0.000      -000V     153                 *
       8          BD+28 4704    166 73743          69     33    000125.2+282811000636.8+290117111.26-32.83 6.13  +0.75 +0.33         K0V                +0.380-0.182 +.067-008V          2.6 158.6AB   4*
       9          CD-23    4    2031660531003                   000143.0-233947000650.1-230627 52.21-79.14 6.18  +0.38 +0.05         A7V                +0.100-0.045      +003V
      10          BD-18 6428    256147090                       000211.8-175639000718.2-172311 74.36-75.90 6.19  +0.14 +0.10         A6Vn               -0.018+0.036      -009V?    195                 *


A deeper inspection reveals that the file is not correctly formatted because not all the rows have the same length. In order to make writing a working DFDL schema easier, let's fix this by padding all the rows to a length of 197 (the sum of the lengths of all the fields as described in the `bsc5.readme` file) and creating a new file:

    :::bash
    $ awk '{printf "%-197s\n", $0}' bsc5.dat > bsc5_padded.dat

Let's extract the first two lines into a sample file that we will use in the examples:

    :::bash
    $ head -n 2 bsc5_padded.dat > bsc5_padded_sample.dat

Now we can continue with the DFDL schema definition.

### DFDL schema

A basic DFDL schema should look like the following:

    :::xml
    <?xml version="1.0" encoding="UTF-8"?>
    <xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns:fn="http://www.w3.org/2005/xpath-functions"
      xmlns:dfdl="http://www.ogf.org/dfdl/dfdl-1.0/" xmlns:ex="http://example.com"
      targetNamespace="http://example.com" elementFormDefault="unqualified">

      <xs:include schemaLocation="org/apache/daffodil/xsd/DFDLGeneralFormat.dfdl.xsd" />

      <xs:annotation>
        <xs:appinfo source="http://www.ogf.org/dfdl/">
          <dfdl:format ref="ex:GeneralFormat" />
        </xs:appinfo>
      </xs:annotation>

      <xs:element name="record" type="xs:string" dfdl:lengthKind="explicit" dfdl:length="197" dfdl:lengthUnits="characters" />
    </xs:schema>

Here we are declaring:

- an XML schema with a custom namespace `http://example.com`;
- the inclusion of a `DFDLGeneralFormat.dfdl.xsd` XML schema;
- an annotation that DFDL will use to determine some default values for the schema properties;
- an element that represents the data being interpreted, along with its type and some DFDL properties.

Let's create a `v1` folder and write this XML content into `v1/bsc.dfdl.xsd`.

### Parsing

In order to try and parse our sample data using this schema, we need to download the Apache Daffodil binaries from the [Daffodil releases page](https://daffodil.apache.org/releases/); at the time of writing, the most recent version is the [2.3.0](https://www.apache.org/dyn/closer.lua/incubator/daffodil/2.3.0/bin/apache-daffodil-2.3.0-incubating-bin.tgz). Let's decompress the .tgz file into our current folder and run the following command:

    :::text
    $ apache-daffodil-2.3.0-incubating-bin/bin/daffodil parse -s v1/bsc.dfdl.xsd bsc5_padded_sample.dat
    <?xml version="1.0" encoding="UTF-8" ?>
    <ex:record xmlns:ex="http://example.com">   1          BD+44 4550      3 36042          46           000001.1+444022000509.9+451345114.44-16.88 6.70  +0.07 +0.08         A1Vn               -0.012-0.018      -018      195  4.2  21.6AC   3 </ex:record>
    [warning] Left over data. Consumed 1576 bit(s) with at least 1592 bit(s) remaining.

This is our first Daffodil infoset! Yes, we do get a warning, but we start to see where we are headed. Now let's take a closer look at the `xs:element` we have declared in the schema:

    :::xml
    <xs:element name="record" type="xs:string" dfdl:lengthKind="explicit" dfdl:length="197" dfdl:lengthUnits="characters" />

- its name is `record`;
- it is a `xs:string`;
- it has a predefined length (`dfdl:lengthKind="explicit"`);
- the length is 197 units (`dfdl:length="197"`)
- the length is measured in characters (`dfdl:lengthUnits="characters"`).

The parser correctly read the first 197 characters of our sample file, then it stopped. We need to specify that the file actually contains a _sequence_ of lines _separated_ by a newline, so we replace the `record` definition with the following:

    :::xml
    ...
    <xs:element name="file">
      <xs:complexType>
        <xs:sequence dfdl:separator="%NL;" dfdl:separatorPosition="postfix">
          <xs:element name="record" type="xs:string" dfdl:lengthKind="explicit" dfdl:length="197" dfdl:lengthUnits="characters" maxOccurs="unbounded" />
        </xs:sequence>
      </xs:complexType>
    </xs:element>
    ...

We wrapped the previous `record` within a `xs:sequence` and added a `maxOccurs="unbounded"` property to declare that it can occur an unlimited number of times; the sequence is parsed by using newlines as postfix record separators and is part of a parent `xs:element` called `file`. Let's create a `bsc.dfdl.xsd` file with the updated element in a `v2` folder and run the parser again:

    :::text
    $ apache-daffodil-2.3.0-incubating-bin/bin/daffodil parse -s v2/bsc.dfdl.xsd bsc5_padded_sample.dat
    <?xml version="1.0" encoding="UTF-8" ?>
    <ex:file xmlns:ex="http://example.com">
      <record>   1          BD+44 4550      3 36042          46           000001.1+444022000509.9+451345114.44-16.88 6.70  +0.07 +0.08         A1Vn               -0.012-0.018      -018      195  4.2  21.6AC   3 </record>
      <record>   2          BD-01 4525      6128569                       235956.2-010330000503.8-003011 98.33-61.14 6.29  +1.10 +1.02        gG9                 +0.045-0.060      +014V                          </record>
    </ex:file>

Great, no more leftover bits! The records are not very informative though, since we haven't described the fields. We need to extend the definition further by stating that the `record` is itself a sequence of fixed-length fields, each with its own name:

    :::xml
    ...
    <xs:element name="file">
      <xs:complexType>
        <xs:sequence dfdl:separator="%NL;" dfdl:separatorPosition="postfix">
          <xs:element name="record" maxOccurs="unbounded" />
            <xs:complexType>
              <xs:sequence>
                <xs:element name="HR" type="xs:string" dfdl:lengthKind="explicit" dfdl:length="4" dfdl:lengthUnits="characters" />
                <xs:element name="Name" type="xs:string" dfdl:lengthKind="explicit" dfdl:length="10" dfdl:lengthUnits="characters" />
                <xs:element name="DM" type="xs:string" dfdl:lengthKind="explicit" dfdl:length="11" dfdl:lengthUnits="characters" />
                <xs:element name="HD" type="xs:string" dfdl:lengthKind="explicit" dfdl:length="6" dfdl:lengthUnits="characters" />
                ...
              </xs:sequence>
            </xs:complexType>
          </xs:element>
        </xs:sequence>
      </xs:complexType>
    </xs:element>
    ...

The updated version can be found in the `bsc.dfdl.xsd` file in the `v3` folder. When we run the parser on the new file we get this:

    :::text
    <?xml version="1.0" encoding="UTF-8" ?>
    <ex:file xmlns:ex="http://example.com">
      <record>
        <HR>   1</HR>
        <Name>          </Name>
        <DM>BD+44 4550 </DM>
        <HD>     3</HD>
        ...
      </record>
      <record>
        <HR>   2</HR>
        <Name>          </Name>
        <DM>BD-01 4525 </DM>
        <HD>     6</HD>
        ...
      </record>
    </ex:file>

Let's run the parser again, now saving the result into `v3/bsc5_padded_sample.xml`:

    :::bash
    $ apache-daffodil-2.3.0-incubating-bin/bin/daffodil parse -s v3/bsc.dfdl.xsd bsc5_padded_sample.dat > v3/bsc5_padded_sample.xml

We are now ready to try Daffodil's unparsing capabilities.

### Unparsing

Let's run the unparser on the infoset:

    :::text
    $ apache-daffodil-2.3.0-incubating-bin/bin/daffodil unparse -s v3/bsc.dfdl.xsd v3/bsc5_padded_sample.xml
       1          BD+44 4550      3 36042          46           000001.1+444022000509.9+451345114.44-16.88 6.70  +0.07 +0.08         A1Vn               -0.012-0.018      -018      195  4.2  21.6AC   3 
       2          BD-01 4525      6128569                       235956.2-010330000503.8-003011 98.33-61.14 6.29  +1.10 +1.02        gG9                 +0.045-0.060      +014V                          

The output looks very similar to our original `bsc5_padded_sample.dat` file. Let's compare the two just to make sure:

    :::bash
    $ apache-daffodil-2.3.0-incubating-bin/bin/daffodil unparse -s v3/bsc.dfdl.xsd v3/bsc5_padded_sample.xml > v3/bsc5_padded_sample_unparsed.dat
    $ diff -s bsc5_padded_sample.dat v3/bsc5_padded_sample_unparsed.dat

The `diff` command reports that the two files are identical, which means that we successfully reconstructed the source file from the derived infoset; now, if we add a new record using the schema we created and then we unparse the infoset, we will get as an output an updated file in the original format. This doesn't mean, of course, that the updated file will be valid; we have been pretty shallow in defining the schema, so all we can be sure about is that the new file will have the same structure as the original file.

### Testing

Daffodil provides a way to check that not only parsing and unparsing work as separate tasks, but also that a sequence of parsing and unparsing leave the original file unchanged; this is done by defining test cases using the Test Data Markup Language ([TDML](https://daffodil.apache.org/tdml/)). In order to replicate the `diff` test, we can create the `bsc.tdml` file in the `v3` folder as follows:

    :::xml
    <?xml version="1.0" encoding="UTF-8"?>
    <testSuite suiteName="Namespaces"
      xmlns:dfdl="http://www.ogf.org/dfdl/dfdl-1.0/"
      xmlns:tdml="http://www.ibm.com/xmlns/dfdl/testData"
      defaultRoundTrip="onePass">

      <tdml:parserTestCase name="bsc_test" root="file"
        model="bsc.dfdl.xsd" description="Test parsing and unparsing"
        roundTrip="onePass">
        <tdml:document>
          <tdml:documentPart type="file">../bsc5_padded_sample.dat</tdml:documentPart>
        </tdml:document>
        <tdml:infoset>
          <tdml:dfdlInfoset type="file">bsc5_padded_sample.xml</tdml:dfdlInfoset>
        </tdml:infoset>
      </tdml:parserTestCase>
    </testSuite>

Then, we run the following command:

    :::text
    $ apache-daffodil-2.3.0-incubating-bin/bin/daffodil test v3/bsc.tdml
    Creating DFDL Test Suite for v3/bsc.tdml
    [Pass] bsc_test

    Total: 1, Pass: 1, Fail: 0, Not Found: 0

We can see that the "one-pass" chain (i.e. a chain of parsing the data, unparsing the result, and comparing the original data with the unparsed data) is successful, although we have "cheated" a little since we created the test infoset via a parsing task rather than manually. Anyway, this is a useful and quick way to test that the schema we are developing actually behaves as we expect in both directions.

### Improving the schema

At this point we realize that we converted our fields to strings, but we haven't really added much. This may be all we need to feed the data into a pipeline for further cleaning and processing, but we can actually make the schema more useful. We could start with trimming the strings so that they can be used straight away; we can add some properties to the `dfdl:format` element:

    :::xml
    <dfdl:format ref="ex:GeneralFormat"
      textStringPadCharacter="%SP;"
      textPadKind="padChar"
      textTrimKind="padChar"
      textStringJustification="center"
    />

Here we are basically using space (`"%SP;"`) as a character to pad with (while unparsing) or to trim (while parsing), and we pad/trim both sides of a string. If we try and parse again, we will get this:

    :::text
    <?xml version="1.0" encoding="UTF-8" ?>
    <ex:file xmlns:ex="http://example.com">
      <record>
        <HR>1</HR>
        <Name></Name>
        <DM>BD+44 4550</DM>
        <HD>3</HD>
        ...
      </record>
      <record>
        <HR>2</HR>
        <Name></Name>
        <DM>BD-01 4525</DM>
        <HD>6</HD>
        ...
      </record>
    </ex:file>

Anyway, if we save the result of the parsing to `bsc5_padded_sample.xml` in the `v4` folder and then define a new test `bsc.tdml` using such result as the `tdml:dfdlInfoset`, the test will fail. The reason of the difference between the original file and the unparsed file is that some fields, after being trimmed, could not be padded back correctly; we can see this more clearly by saving the result of the unparsing task to `v4/bsc5_padded_sample_unparsed.dat` and comparing it to the original `bsc5_padded_sample.dat` file.

In short, if we want to extend the schema and keep making use of the unparsing capability, we need to take extra care. It is better to start by extending the definition of one or more fields and checking the results after the change; for instance, if we want to interpret a field as a floating-point number and still be able to write the field back into its original format, we need to make sure that there are no padding, conversion, or precision errors.

Let's say that we want to interpret the field `HD` as an integer (example in the `v5` folder); then, we need to change its declaration from this:

    :::xml
    <xs:element name="HD" type="xs:string" dfdl:lengthKind="explicit" dfdl:length="6" dfdl:lengthUnits="characters" />

to this:

    :::xml
    <xs:element name="HD" type="xs:int" dfdl:lengthKind="explicit" dfdl:length="6" dfdl:lengthUnits="characters" dfdl:textPadKind="padChar" dfdl:textTrimKind="padChar" dfdl:textNumberPadCharacter="%SP;" dfdl:textNumberJustification="right" dfdl:textNumberPattern="#" />

Although the `dfdl:textNumberPadCharacter` and `dfdl:textNumberJustification` are redundant, since they have the same default value in the [DFDL General Format schema](https://github.com/apache/incubator-daffodil/blob/master/daffodil-lib/src/main/resources/org/apache/daffodil/xsd/DFDLGeneralFormat.dfdl.xsd), it is clear that just changing the type from `xs:string` to `xs:int` is not enough. The important properties here are `dfdl:textPadKind` and `dfdl:textTrimKind` (since they are needed to instruct the parser and the unparser to actually use the pad character), and `dfdl:textNumberPattern` (since otherwise the default pattern would include a group separator and convert a number string such as "123456" to "123,456"). The test in the `v5` folder includes these changes, so it will run successfully.

If you try and run the parser on the full dataset using the schema defined in the `v5` folder, you will get a warning about leftover data. The reason is that not all records contain a value for the `HD` field that can be parsed as an integer; we should then allow the `HD` element to be _nillable_ by adding the following attributes:

    :::xml
    nillable="true" dfdl:nilKind="literalValue" dfdl:nilValue="%ES;"

In this way, when the trimmed value equals an empty string, the element is considered null and no conversion is attempted. You can find the updated schema in the `v6` folder.

**UPDATE:** I extended the schema further by adding the same `xs:int` pattern to other elements, namely `HR`, `SAO`, and `FK5`. I also took the chance to experiment with the declaration of a new type, and things got interesting because of the peculiar behaviour I wanted to replicate.

The new fields to parse/unparse represent the [right ascension](https://en.wikipedia.org/wiki/Right_ascension) (RA) and the [declination](https://en.wikipedia.org/wiki/Declination) (DE) in the *hours/minutes/seconds* and *degrees/arcminutes/arcseconds* formats respectively; if we exclude RA seconds, all the other fields encode integers as zero-padded two-digit strings. The interesting part is that these fields can be empty, so we cannot use the previous pattern: if we were just to trim the "0" character we would get a null value when the field is "00", which is actually a legitimate value. The solution is to skip the trimming part and designate a double space as the "null value", since the length of the empty field is still two. We can do this by using the property `dfdl:nilValue="%WSP;%WSP;"`, so that the new type looks like this:

    :::xml
    <xs:simpleType name="twoDigitIntOrNull" dfdl:lengthKind="explicit" dfdl:length="2" dfdl:lengthUnits="characters" dfdl:textPadKind="padChar" dfdl:textNumberPadCharacter="0" dfdl:nilKind="literalValue" dfdl:nilValue="%WSP;%WSP;">
      <xs:restriction base="xs:int" />
    </xs:simpleType>

After defining this new type, the fields can be defined as in this example:

    :::xml
    <xs:element name="RAh1900" type="ex:twoDigitIntOrNull" nillable="true" />

For the sake of completeness the combination `dfdl:textPadKind="padChar" dfdl:textNumberPadCharacter="0"` in this case can be replaced by `dfdl:textNumberPattern="00" dfdl:textStandardZeroRep="00"`, so that a value of zero can still be correctly unparsed; this is not always necessarily the case, as we can see with the RA *seconds* field that we have skipped. The field encodes a decimal number as a string with two digits to the left of the decimal point and one digit to the right, so if we were to use the same approach the zero value would be unparsed to "0000"; we can do this instead:

    :::xml
    <xs:simpleType name="fourDigitDoubleOrNull" dfdl:lengthKind="explicit" dfdl:length="4" dfdl:lengthUnits="characters" dfdl:textNumberPattern="00.0" dfdl:textStandardZeroRep="00.0" dfdl:nilKind="literalValue" dfdl:nilValue="%WSP;%WSP;%WSP;%WSP;">
      <xs:restriction base="xs:double" />
    </xs:simpleType>

and define the RA seconds fields as in this example:

    :::xml
    <xs:element name="RAs1900" type="ex:fourDigitDoubleOrNull" nillable="true" />

You can find the updated schema in the `v7` folder of the associated repository.

### Using a different infoset representation

So far we have parsed the data into XML, but what if we prefer JSON instead? We just need to add a `-I json` in the parse/unparse command as follows:

    :::text
    $ apache-daffodil-2.3.0-incubating-bin/bin/daffodil parse -s v3/bsc.dfdl.xsd -I json bsc5_padded_sample.dat
    {
      "file": {
        "record": [
          {
            "HR": "   1",
            "Name": "          ",
            "DM": "BD+44 4550 ",
            "HD": "     3",
            ...
          },
          {
            "HR": "   2",
            "Name": "          ",
            "DM": "BD-01 4525 ",
            "HD": "     6",
            ...
          }
        ]
      }
    }

We can save the output to a .json file and process it further. JSON is not the only alternative: [other representations](https://daffodil.apache.org/infoset/) are available as well.

### Conclusions

We have touched on the main advantages of using Apache Daffodil and, without going too much into the details of DFDL, we created a schema to successfully parse and unparse scientific data. We only used the standalone binaries, but Daffodil is available also as a Java/Scala library and as an [Apache Nifi](https://nifi.apache.org/) processor.

One thing to be aware of is the size of the source data: the binaries by default load the whole dataset in memory before starting to process it, which might result in a huge memory footprint or heap space errors. A possible solution in this case would be to split the source file into multiple files, which might be easier when the source is in a text format and harder if it is in a binary format; if this is not practical, it might be worth looking into the streaming capabilities of the Daffodil API.