Title: Apache Rya
Date: 2019-08-31
Category: projects
Tags: Big Data, Semantic Web

Since I have been working with Semantic Web technologies for quite some time, I was looking forward to explore new Apache projects within the area. [Apache Rya](https://rya.incubator.apache.org/) fit the purpose perfectly, as it is a SPARQL-enabled triplestore for Big Data, promising to scale to billions of triples across multiple nodes. If you are completely lost after this terminology, you can take a look at the [Wikipedia article](https://en.wikipedia.org/wiki/Semantic_Web) and the [W3C presentation](https://www.w3.org/2009/Talks/0615-SanJose-tutorial-IH/Slides.pdf) to get an idea of the subject.

Rya runs on top of another Apache project, [Accumulo](https://accumulo.apache.org/) (a distributed key/value store), and is deployed as a Web service. Since Accumulo by itself requires a fairly complex installation procedure as it is based on [Apache Hadoop](https://hadoop.apache.org/) and [Apache Zookeeper](https://zookeeper.apache.org/), we will use yet another great Apache project, [Apache Fluo](http://fluo.apache.org/) (or, more specifically, its subproject [Fluo Uno](https://github.com/apache/fluo-uno)), to simplify the whole procedure; we will then use a well-known server, [Apache Tomcat](http://tomcat.apache.org/), to run it.

In this article we will see how to get a single-machine Rya instance up and running and how to perform basic operations; scalability, management, and more complex operations will be covered in another article. As usual, the reference operating system will be CentOS 7 (if possible, an empty/fresh instance).

## Preparing the environment

### Installing Tomcat

First of all we need to have Tomcat installed and running. On CentOS 7 it is just a matter of running the following two commands (both requiring `sudo` rights):

    :::bash
    $ sudo yum install tomcat
    $ sudo service tomcat start

### Prerequisites for Fluo Uno

In the following, we will download and use Fluo Uno to setup a single-machine Accumulo instance; its sibling project, [Fluo Muchos](https://github.com/apache/fluo-muchos), can be used instead to create a real cluster in Amazon's EC2.

In order to use Fluo Uno, we need to have Java 8, *wget*, *maven*, and *git* already installed; if any of these components is missing, it can be installed with `sudo yum install`. We also need to install the *shasum* program (**not** the *sha1sum* or the similar ones that are likely already installed), which is contained in the *perl-Digest-SHA* package, and we might install *curl* to test Rya's API. A quick way to install all the needed packages is to run:

    :::bash
    $ sudo yum install java wget maven git perl-Digest-SHA curl

Once all the components are present, we need to export the Java path. If Java has been installed under, say, `/usr/lib/jvm/java-1.8.0`, we need to run:

    :::bash
    $ export JAVA_HOME=/usr/lib/jvm/java-1.8.0

Now, in order for Hadoop to work correctly, we need to make sure we can log into localhost with SSH:

    :::bash
    $ ssh localhost

If this does not work, we need to create a local pair of SSH keys. First of all, let's make sure that we do not really have any SSH keys:

    :::bash
    $ ls ~/.ssh

If no results are returned, we can run this command:

    :::bash
    $ ssh-keygen

which will create a default RSA key. If, instead, some keys are already present, try to debug the error and, before running the keygen, back them up first. Once the keys are created, they need to be added to the list of authorized keys:

    :::bash
    $ cat ~/.ssh/id_rsa.pub >> ~/.ssh/authorized_keys

Now, `ssh localhost` should successfully open a new shell.

### Downloading and using Fluo Uno

We are now ready to clone Fluo Uno from Github:

    :::bash
    git clone https://github.com/apache/fluo-uno.git

and enter the directory:

    :::bash
    cd fluo-uno

Since at the time of writing Rya supports Accumulo only up to version 1.7, we need to add the next two lines at the beginning of `./conf/uno.conf` to ensure compatibility:

    :::text
    HADOOP_VERSION=2.9.0
    ACCUMULO_VERSION=1.7.3

After saving, we can run the following commands:

    :::bash
    $ ./bin/uno fetch accumulo
    $ ./bin/uno setup accumulo

If everything ran successfully, we should see an output like this:

    :::text
    Apache Hadoop 3.2.0 is running
        * NameNode status: http://localhost:9870/
        * ResourceManager status: http://localhost:8088/
        * view logs at /path/to/fluo-uno/install/logs/hadoop
    Apache ZooKeeper 3.4.14 is running
        * view logs at /path/to/fluo-uno/install/logs/zookeeper
    Apache Accumulo 2.0.0 is running
        * Accumulo Monitor: http://localhost:9995/
        * view logs at /path/to/fluo-uno/install/logs/accumulo
    Setup complete.

If the output is different or some errors are displayed, try checking the `./install/logs` folder to debug.

## Installing Rya

Once the environment is ready as detailed in the previous sections, we can clone Rya:

    :::bash
    $ git clone https://github.com/apache/incubator-rya

and build it:

    :::bash
    $ cd incubator-rya
    $ mvn clean install

(the last command will take a while to complete because all the tests are run, which is highly recommended).

When Maven has finished building, we run the following command to deploy Rya on Tomcat:

    :::bash
    $ sudo cp ./web/web.rya/target/web.rya.war /var/lib/tomcat/webapps/

Before we can use Rya, we need to create an `environment.properties` file with the following content:

    :::text
    # Accumulo instance name
    instance.name=uno
    # Accumulo Zookeepers
    instance.zk=localhost:2181
    # Accumulo username
    instance.username=root
    # Accumulo password
    instance.password=secret

    # Rya Table Prefix
    rya.tableprefix=triplestore_
    # To display the query plan
    rya.displayqueryplan=true

then assign it to the Tomcat user (usually `tomcat`), move it into the Web application classpath and restart Tomcat:

    :::bash
    $ sudo chown tomcat:tomcat environment.properties
    $ sudo mv environment.properties /var/lib/tomcat/webapps/web.rya/WEB-INF/classes
    $ sudo service tomcat restart

In order to test that Rya is deployed and configured successfully, we can run:

    :::bash
    $ curl -I "localhost:8080/web.rya/queryrdf"

which should give 200 as the status code. Yay, we have a running Rya instance!

## Examples

Let's open the SPARQL endpoint on `http://localhost:8080/web.rya/sparqlQuery.jsp`. Rya's SPARQL endpoint supports SPARQL Update, so we can insert some example triples using the following query (inspired by Rya's documentation):

    :::sparql
    INSERT DATA
    {
        GRAPH <http://example.com/mygraph>
        {
            <http://mynamespace/ProductType1> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://mynamespace/ProductType> .
            <http://mynamespace/ProductType1> <http://www.w3.org/2000/01/rdf-schema#label> "Thing" .
            <http://mynamespace/ProductType1> <http://purl.org/dc/elements/1.1/publisher> <http://mynamespace/Publisher1> .
        }
    }

then retrieve them with another SPARQL query and selecting *JSON* as the result format:

    :::sparql
    SELECT *
    WHERE
    {
        GRAPH ?g
        {
            ?s ?p ?o .
        }
    }

which should give a result similar to the following (the order of the fields might be different):

    :::json
    {
       "head" : {
          "vars" : [
             "g",
             "s",
             "p",
             "o"
          ]
       },
       "results" : {
          "bindings" : [
             {
                "s" : {
                   "value" : "http://mynamespace/ProductType1",
                   "type" : "uri"
                },
                "o" : {
                   "value" : "http://mynamespace/Publisher1",
                   "type" : "uri"
                },
                "g" : {
                   "type" : "uri",
                   "value" : "http://example.com/mygraph"
                },
                "p" : {
                   "type" : "uri",
                   "value" : "http://purl.org/dc/elements/1.1/publisher"
                }
             },
             {
                "o" : {
                   "value" : "http://mynamespace/ProductType",
                   "type" : "uri"
                },
                "s" : {
                   "value" : "http://mynamespace/ProductType1",
                   "type" : "uri"
                },
                "p" : {
                   "value" : "http://www.w3.org/1999/02/22-rdf-syntax-ns#type",
                   "type" : "uri"
                },
                "g" : {
                   "value" : "http://example.com/mygraph",
                   "type" : "uri"
                }
             },
             {
                "g" : {
                   "type" : "uri",
                   "value" : "http://example.com/mygraph"
                },
                "p" : {
                   "value" : "http://www.w3.org/2000/01/rdf-schema#label",
                   "type" : "uri"
                },
                "o" : {
                   "value" : "Thing",
                   "type" : "literal"
                },
                "s" : {
                   "type" : "uri",
                   "value" : "http://mynamespace/ProductType1"
                }
             },
             {
                "o" : {
                   "type" : "literal",
                   "value" : "3.0.0"
                },
                "s" : {
                   "value" : "urn:org.apache.rya/2012/05#rts",
                   "type" : "uri"
                },
                "p" : {
                   "value" : "urn:org.apache.rya/2012/05#version",
                   "type" : "uri"
                }
             }
          ]
       }
    }

We can get the same result using the `queryrdf` REST endpoint:

    :::bash
    $ curl "localhost:8080/web.rya/queryrdf" -d query.resultformat=json --data-urlencode query="SELECT * WHERE {GRAPH ?g {?s ?p ?o}}"

## Conclusions

Like other Apache projects still in incubation, Rya's documentation and examples may be still somewhat incomplete or difficult to follow. My aim was to try and streamline the installation process, and to provide a couple examples which allow a user to quickly see that everything is working correctly. A more complex setup and more interesting examples to come soon!