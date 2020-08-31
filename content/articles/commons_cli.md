Title: Apache Commons CLI
Date: 2020-08-31
Category: projects
Tags: library, Apache Commons, CLI, command line
Status: published

A common task when developing user-facing applications is to parse command line parameters to turn them into runtime options. The task is certainly repetitive and prone to error when it is reimplemented time and again, but another little library from the [Apache Commons](https://commons.apache.org/) project makes it definitely an easier and more enjoyable experience: enter [Apache Commons CLI](http://commons.apache.org/proper/commons-cli/)!

[TOC]

### Setting up

At the moment of writing, the most recent version of Apache Commons CLI is 1.4 (although a complete rewrite known as [CLI2](http://commons.apache.org/sandbox/commons-cli2/) is in the works, but yet unfinished).

As we have done in the [Apache Commons Text article]({filename}/articles/commons_text.md), we will use the library by means of a `pom.xml` file containing the following lines:

    :::xml

    <groupId>blog.apothem</groupId>
    <artifactId>apache-commons-cli-example</artifactId>
    <version>0.0.1-SNAPSHOT</version>

    <dependencies>
        <dependency>
            <groupId>commons-cli</groupId>
            <artifactId>commons-cli</artifactId>
            <version>1.4</version>
        </dependency>
    </dependencies>

Again, we will create a class with a `main` method and write the entire code there; the complete code is available as always in the companion [Apothem resources repository](https://github.com/nvitucci/apothem-resources/tree/master/apache-commons-cli).

### Stages of processing

Command line processing is usually made up of three stages:

1. the *definition stage*, where the options relevant to the application are defined;
1. the *parsing stage*, where the text that is passed from the command line to the application (the content of `args[]` in a typical Java `main(String args[])` method) is interpreted as a list of options with or without values;
1. the *interrogation stage*, where the options are actually used in the code.

Commons CLI has specialised classes and methods for each of the stages. Let's start with the definition stage.

#### Definition stage: the `Options` class

In this stage we define all the options with their parameters. Every option is created as an instance of the `Option` class, then all options are added to an `Options` (note the plural form) object.

A single option can be defined like the following:

    :::java
    Option verboseOption = Option.builder("v")
        .longOpt("verbose")
        .desc("Print status with verbosity.")
        .required(false)
        .hasArg(false)
        .build();

We use the static `builder` method of the `Option` class to gradually build an option with all the features we need. We can set:

- the short version of the option as a parameter of the `builder` method (`v` in this example), so that we can use it as `-v` on the command line);
- the long version of the option (`longOpt("verbose")`), so that we can use it as `--verbose`;
- a description (`desc("Print status with verbosity.")`) to show when the usage message is displayed by calling the application with the `-h` or `--help` option, as we will see later on;
- whether the parameter is required (`required()` or `required(true)`) or optional (`required(false)`);
- whether the parameter is a no-argument flag (`hasArg(false)`) or has at least one argument (`hasArg()` or `hasArg(true)`).

We can also set more advanced features as in the following two examples:

    :::java
    Option fileOption = Option.builder("f")
        .longOpt("file")
        .desc("File to be processed.")
        .required(false)
        .numberOfArgs(4)
        .argName("THEFILE")
        .valueSeparator(',')
        .build();

    Option numberOption = Option.builder("n")
        .longOpt("number")
        .desc("Number to be processed.")
        .required(false)
        .hasArg()
        .argName("number")
        .type(Number.class)
        .build();

where we also have:

- the name of the argument to show in the usage message along with the option (`argName("number")`);
- the number of arguments that a string should be parsed to (`numberOfArgs(n)` if it's not 1, in which case `hasArg()` can be used) and their separator (`valueSeparator(',')`), to be used together when we want to pass multiple values for the same option;
- the type the argument should be parsed to (`type(Number.class)`).

Once all the options have been defined with their own parameters, an `Options` object should be created and all the options should be added to it:

    :::java
    Options options = new Options();
    options.addOption(verboseOption);
    options.addOption(fileOption);
    options.addOption(numberOption);

If we want to create a help message automatically, we can use the `HelpFormatter` class with the `Options` object as in this example:

    :::java
    HelpFormatter formatter = new HelpFormatter();
    String helpHeader = "List of options:";
    String helpFooter = "------";
    formatter.setSyntaxPrefix("Usage: ");
    formatter.printHelp(80, "example", helpHeader, options, helpFooter, true);

With this code we are:

- limiting the length of each help line to 80;
- using `"example"` as a name for the command in the usage line;
- adding a header and a footer around the options;
- generating a usage line automatically (if set to `false` the usage line would consist only of the command name).

When running our application, this will show the following text:

    :::text
    Usage: example [-f <THEFILE>] [-n <number>] [-v]
    List of options:
     -f,--file <THEFILE>    File to be processed.
     -n,--number <number>   Number to be processed.
     -v,--verbose           Print status with verbosity.
    ------

#### Parsing stage: the `CommandLineParser` class

With the `Options` object initialised, we need now to create a parser to parse the content of `args[]` into options. We need therefore to create an instance of the `CommandLineParser` class whose only actual implementation at the moment is `DefaultParser`, which replaces all the other more specialised deprecated parsers like `GnuParser` and `PosixParser`:

    :::java
    CommandLineParser parser = new DefaultParser();

We are now ready to perform the actual parsing by returning a `CommandLine` object that will be used in the next stage:

    :::java
    CommandLine cmd = parser.parse(options, args);

The `parse` method can throw a `ParseException`, so it has to be used in a `try/catch` block.

#### Interrogation stage: the `CommandLine` class

Now that the `CommandLine` object is initialised as well, we can use it to get the values for the options we need.

A simple flag can be retrieved with the `hasOption` method:

    :::java
    boolean verbose = cmd.hasOption("verbose");

while a multi-valued argument can be retrieved with `getOptionValues`:

    :::java
    String[] fileNames = cmd.getOptionValues("file");

and a typed argument can be retrieved with `getParsedOptionValue`:

    :::java
    Number number = (Long) cmd.getParsedOptionValue(NUMBER_OPTION);

(In this example, it is interesting to note that we had to use the `Number` type because `getParsedOptionValue` uses the `TypeHandler` class internally, which in turn uses the `PatternOptionBuilder` class that defines `Number` (no subclasses) as a returnable type for numbers.)

#### Putting everything together

The options' values can now be used within the application. As an example, we could add a simple `println` that makes use of all of them:

    :::java
    System.out.printf(
        "%s files were provided: '%s'. Verbosity is set to '%s' and the number is %d.%n",
        fileNames.length, String.join(", ", fileNames), verbose, number);

A quick way to run Maven-based code is to use the `mvn exec:java` command, so that we do not have to deal with the classpath and the dependencies. For instance, if we put all the code in a `CliExamples` class, we can run:

    :::bash
     mvn exec:java -Dexec.mainClass=CliExamples -Dexec.args="-v -f 01.txt,02.txt,03.txt,04.txt -n 42"

and, besides the aforementioned help message, the result will be:

    :::text
    4 files were provided: '01.txt, 02.txt, 03.txt, 04.txt'. Verbosity is set to 'true' and the number is 42.

You can find the whole example in the [companion repository](https://github.com/nvitucci/apothem-resources/tree/master/apache-commons-cli).

### Conclusions

Since using an application from the command line is a common task, a library that abstracts most of the details is very welcome. Although dated, Apache Commons CLI still does a very good job and is so lightweight that it can be easily added to any existing Java-based application to add a nice user interface.
