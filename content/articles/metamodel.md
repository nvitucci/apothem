Title: Apache MetaModel
Date: 2019-05-31
Category: projects
Tags: Big Data, library, database

It's a few years now since I've got the "[polyglot persistence](https://martinfowler.com/bliki/PolyglotPersistence.html)" bug, first out of interest, then out of necessity. Given the abundance of data models and storage technologies available today, it is crucial to be aware of the strengths and weaknesses of each solution; furthermore, more often than not, an architecture that integrates several types of solutions is desirable or needed.

Leaving architectural questions aside, the main question in this polyglot scenario is: how to read and interpret data from disparate data sources in a reliable and uniform fashion? Is it better to create a data lake out of all the sources, or to take a federated approach where every query is dispatched to its appropriate database? The Apache project we will work with today, [MetaModel](https://metamodel.apache.org/), aims at providing tools to deal with such challenges.

### Main concepts

Apache MetaModel provides _"a common interface for discovery, exploration of metadata and querying of different types of data sources"_, which means that, through the use of concepts such as _datasets_, _tables_, and _columns_, it exposes a basic abstraction common to all the data sources it can connect to; such abstract data model can then be queried using SQL as an "interlanguage". It is important to note that, as stated on the website, _"MetaModel *isn't* a data mapping framework"_; in other words its main intended usage is not to integrate different terminologies within the same domain, but rather to make it easy to add new datasources and to maximize the usage of metadata.

MetaModel is not the only library to provide tools for data integration. A similar approach is offered by other Apache projects such as [Spark](https://spark.apache.org/) or [Drill](https://drill.apache.org/), but MetaModel might be better suited than such Big Data tools in scenarios where the main challenge is the diversity in the data and the schema variability rather than the scale; it can be plugged into an existing project with no additional setup and it offers many convenience methods to start using data sources (including plain CSV, JSON and XML files!) right away. Now let's see how to include MetaModel in a project, along with a few examples.

(Note: in some sections of this article I will make use of Docker for convenience. If you don't want to use Docker at the moment, you can just skip those sections; otherwise, make sure to [install it](https://docs.docker.com/install/) in order to follow.)

### Setup

The best way to get started with MetaModel is to include it as a Maven dependency. If you use an IDE such as Eclipse or IntelliJ, all you need to do is to create a new `apache-metamodel-example` Maven project; otherwise, you can have a look [here](https://maven.apache.org/guides/getting-started/maven-in-five-minutes.html) to get an idea of how to install and work with Maven. In any case, as usual you will find a fully working project on the [associated repository](https://github.com/nvitucci/apothem-resources) under the `apache-metamodel` folder.

The content of the `pom.xml` file should look like the following:

    :::xml
    <?xml version="1.0" encoding="UTF-8"?>
    <project xmlns="http://maven.apache.org/POM/4.0.0"
             xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
             xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd">
         <modelVersion>4.0.0</modelVersion>

         <groupId>groupId</groupId>
         <artifactId>apache-metamodel-example</artifactId>
         <version>0.0.1-SNAPSHOT</version>

         <dependencies>
             <dependency>
                 <groupId>org.apache.metamodel</groupId>
                 <artifactId>MetaModel-full</artifactId>
                 <version>5.3.0</version>
             </dependency>
         </dependencies>
     </project>

Once the `pom.xml` file is saved, your IDE should download all the needed dependencies automatically; if you are doing everything manually, you can run the following command to trigger a first build:

    :::bash
    $ mvn package

Now let's create a new Java file called `MetaModelExample.java` with the following content:

    :::java
    package com.example;

    import org.apache.metamodel.data.DataSet;
    import org.apache.metamodel.data.Row;

    public class MetaModelExample {
        public static void main(String args[]) {
            MetaModelExample example = new MetamodelExample();
        }
    }

If you don't get any errors in the imports, the project is set up correctly.

### Examples

We can now start to add a few different data sources to explore MetaModel's capabilities.

#### CSV files

Let's start with a simple CSV file. We can manually create an `example.csv` file under `/tmp` with the following content:

    :::text
    project,language,completed
    Project1,Java,true
    Project2,Java,false
    Project3,Python,true

Let's add the following method to the `MetaModelExample` class:

    :::java
    public void processCsv(String filename) {
        DataContext dataContext = DataContextFactory.createCsvDataContext(new File(filename));
        List<String> tableNames = dataContext.getDefaultSchema().getTableNames();

        System.out.println(Arrays.toString(tableNames.toArray()));

        final String table = tableNames.get(0);

        DataSet dataSet = dataContext.query()
                .from(table)
                .select("project")
                .where("language").eq("Java")
                .and("completed").eq(false)
                .execute();

        for (Row r: dataSet.toRows())
            System.out.println(Arrays.toString(r.getValues()));
    }

and then a call to this method within the main:

    :::java
    ...
    MetaModelExample example = new MetamodelExample();

    example.processCsv("/tmp/example.csv");
    ...

If we run the main method, we will get the following output:

    :::text
    [example.csv, default_table]
    [Project2]

What have we just done?

- We created a `DataContext` (more specifically, a `CsvDataContext`) wrapping the CSV file.
- We extracted the names of all the tables from the default schema and printed them; since the data source is a single file, the default schema is the only available schema and there is only one table (the second one being a convenience `default_table` alias).
- We ran a SQL query on the first table: we selected the `project` column from the rows where the `language` is `Java` and `completed` is `false`.
- We printed the result of the query.

So, in the end, we ran a SQL query on a CSV file! Perhaps even more interestingly, we can update the file with some update instructions by replacing the `DataContext` class with `UpdateableDataContext` and then adding the following lines:

    :::java
    dataContext.executeUpdate(new UpdateScript() {
        public void run(UpdateCallback callback) {
            callback.update(table).value("completed", "true").where("language").eq("Java").execute();
            callback.insertInto(table)
                    .value("project", "Project4")
                    .value("language", "Java")
                    .value("completed", "false")
                    .execute();
        }
    });

If we run again the previous query, we'll see that the file has been updated and `Project2` is no longer listed, while `Project4` is. Neat!

#### XLSX files

Now let's look at a slightly more complex example. Spreadsheets can contain more than one table, which makes them closer to a relational database; MetaModel can use XLSX ([Office Open XML](https://en.wikipedia.org/wiki/Office_Open_XML) Workbook) files, which can be read and saved with open source tools such as LibreOffice and OpenOffice. You can find an example file on the repo, or create your own one. All we need to do is to add a method such as this one:

    :::java
    public void processSpreadsheet(String filename) {
        DataContext dataContext = DataContextFactory.createExcelDataContext(new File(filename));

        List<String> sheetNames = dataContext.getDefaultSchema().getTableNames();
        System.out.println(Arrays.toString(sheetNames.toArray()));

        for (String sheetName: sheetNames) {
            List<Column> sheetColumns = dataContext.getDefaultSchema().getTableByName(sheetName).getColumns();

            for (Column col: sheetColumns)
                System.out.println(col.getName());

            DataSet content = dataContext.query().from(sheetName).selectAll().execute();

            for (Row r: content.toRows())
                System.out.println(Arrays.toString(r.getValues()));
        }
    }

and include it in the main method as we did with the previous example. The output will show the name of all the sheets and, for each sheet, the names of its columns and its data. But there is more! Since in this example the first column of each sheet represents the ID of a customer, we can perform a join between the two sheets by adding the following lines:

    :::java
    DataSet joined = dataContext.query()
            .from(sheetNames.get(0))
            .innerJoin(sheetNames.get(1)).on("id", "id")
            .select("Names.surname", "Products.amount")
            .execute();

    for (Row r: joined.toRows())
        System.out.println(Arrays.toString(r.getValues()));

and the output will show the selected columns from the joined table.

#### JSON files

So far we have looked at tabular data, but what if we have data structured in a different format such as JSON? We may need to make some compromise between the expressivity of a non-relational model and the ease of use of a relational model, so in some cases we will need to "flatten out" some internal fields. Given instead a simple (and quite common) case, where the file is an array containing objects with the same fields like the following:

    :::json
    [
        {"id": 1, "value": 5},
        {"id": 2, "value": 10},
        {"id": 3, "value": 12}
    ]

we can write code similar to what we already wrote before and run SQL queries on JSON files:

    :::java
    public void processJson(String filename) {
        DataContext dataContext = DataContextFactory.createJsonDataContext(new File(filename));

        List<String> tableNames = dataContext.getDefaultSchema().getTableNames();
        System.out.println(Arrays.toString(tableNames.toArray()));

        DataSet dataSet = dataContext.query().from(tableNames.get(0))
                .select("id")
                .where("value")
                .gte(10)
                .execute();

        for (Row r: dataSet.toRows())
            System.out.println(Arrays.toString(r.getValues()));
    }

#### Databases

By now we have understood how to "enhance" static files with querying capabilities, but what if we want to connect to a real datastore such as SQLite, PostgreSQL or MongoDB?

MetaModel provides connectors for a wide variety of databases, including a generic JDBC connector and a specific connector for MongoDB, which support schema creation and inserts/updates as well. Let's see an example with MongoDB:

    :::java
    public void connectToMongo() {
        UpdateableDataContext dataContext = DataContextFactory.createMongoDbDataContext(
                "localhost", 27017, "test", null, null);

        List<String> tableNames = dataContext.getDefaultSchema().getTableNames();

        if (tableNames.isEmpty()) {
            dataContext.executeUpdate(new UpdateScript() {
                public void run(UpdateCallback callback) {
                    String table = "mytable";

                    callback.createTable(callback.getDataContext().getDefaultSchema(), table)
                            .withColumn("color").ofType(ColumnType.VARCHAR)
                            .withColumn("size").ofType(ColumnType.CHAR)
                            .execute();

                    callback.insertInto(table).value("color", "red").value("size", "L").execute();
                    callback.insertInto(table).value("color", "yellow").value("size", "S").execute();
                }
            });
        }

        tableNames = dataContext.getDefaultSchema().getTableNames();
        System.out.println(Arrays.toString(tableNames.toArray()));
    }

In this example, we create a connection to a MongoDB instance running on `localhost:27017` and we connect to the `test` database (which might not exist yet); then, we get the list of "tables" (MongoDB collections) and, if none is found, we create a new one called `mytable` with "columns" (MongoDB document fields) `color` and `size`; finally, we insert two example "records" (MongoDB documents) in the newly created collections. In order to make sure that this works, we can add a query section like in the previous examples:

    :::java
    DataSet dataSet = dataContext.query().from(tableNames.get(0))
            .selectAll()
            .where("size")
            .eq("S")
            .execute();

    for (Row r: dataSet.toRows())
        System.out.println(Arrays.toString(r.getValues()));

and we can see that only the second record will be printed, with the values we inserted plus an additional value (the `_id` field that MongoDB creates automatically if none is supplied).

In order to run this example, the easiest solution is to download and run a MongoDB Docker image:

    :::bash
    $ docker pull mongo
    $ docker run -p 27017:27017 mongo

If this is not an option, MongoDB can be installed manually following the instructions [here](https://www.mongodb.com/download-center/community).

Other data sources can be connected to and used in a similar fashion.

### Apache Membrane

A fantastic and little known addition to MetaModel is its subproject [Membrane](https://cwiki.apache.org/confluence/display/METAMODEL/Membrane). Membrane is essentially a [RESTful](https://en.wikipedia.org/wiki/Representational_state_transfer) Web service that can be used to manage and query different data sources _live_ by adding them to _"tenants"_ (which are basically independent contexts, each with its own connections to any number of data sources).

In order to run Membrane, we should clone the repository and build it:

    :::bash
    $ git clone https://github.com/apache/metamodel-membrane
    $ mvn clean install

Since it has many dependencies, the building process will take a while. When the build is ready, we can run it with the following command:

    :::bash
    $ java -server -jar undertow/target/membrane-undertow-server.jar

The server will now run on port 8080, and we can submit requests to it by using `curl` or any REST client such as [Postman](https://www.getpostman.com/), [Advanced REST Client](https://install.advancedrestclient.com/), [Restlet client](https://restlet.com/modules/client/), etc.

---
> If you are using Docker, you can use cool API description tools such as [Swagger UI](https://swagger.io/tools/swagger-ui/) or [ReDoc](https://github.com/Rebilly/ReDoc); they can both be easily installed with `docker pull` and run with `docker run`, making sure to use a port different from 8080 where Membrane is running, and to use the Membrane-generated `swagger.json` as the API specification:
>
>     $ docker pull redocly/redoc
>     $ docker run -p 8000:80 -e SPEC_URL=http://localhost:8080/swagger.json redocly/redoc
>
> In order to call Membrane from such services, though, [CORS headers](https://en.wikipedia.org/wiki/Cross-origin_resource_sharing#Request_headers) have to be enabled; I sent a [pull request](https://github.com/apache/metamodel-membrane/pull/22) to add this capability with the help of a `MEMBRANE_ENABLE_CORS` variable, so that the server can be run with:
>
>     $ MEMBRANE_ENABLE_CORS=true java -server -jar undertow/target/membrane-undertow-server.jar
---

Having the server running, we can try out the endpoints. Let's first of all create a tenant:

    :::bash
    $ curl -X PUT http://localhost:8080/my-tenant

We will now add our first data source, for instance a CSV file:

    :::bash
    $ curl -H "Content-Type: application/json" -X PUT http://localhost:8080/my-tenant/my-csv -d '
    {
      "type": "csv",
      "resource": "/tmp/example.csv",
      "quote-char": "\"",
      "separator-char": ",",
      "escape-char": "\\",
      "encoding": "UTF-8"
    }'

and we will get a response like the following:

    :::json
    {
        "type": "datasource",
        "name": "my-csv",
        "tenant": "my-tenant",
        "updateable": true,
        "query_uri": "/my-tenant/my-csv/query",
        "schemas": [
          {
            "name": "information_schema",
            "uri": "/my-tenant/my-csv/s/information_schema"
          },
          {
            "name": "resources",
            "uri": "/my-tenant/my-csv/s/resources"
          }
        ]
    }

which will show some endpoints we can explore. The `/my-tenant/my-csv/s/information_schema` endpoint, for instance, shows the structure of a generic information schema; the `/my-tenant/my-csv/s/resources` endpoint, instead, shows the tables of our datasource - we can, for instance, get the metadata on the CSV file by exploring the `/my-tenant/my-csv/s/resources/t/default_table` endpoint. The most interesting endpoint, though, is probably `/my-tenant/my-csv/query`: we can submit a query as a GET parameter and immediately get results. For instance, we can call:

    :::bash
    $ curl -G "http://localhost:8080/my-tenant/my-csv/query" --data-urlencode "sql=SELECT * FROM default_table"

to get the whole content of the example CSV file. (Here, `-G` and `--data-urlencode` are used in order to URL-encode the `sql` parameter and still send it as a `GET` request.)

### Conclusions

MetaModel is an easy-to-use and extendable tool that makes it easier to integrate multiple data sources programmatically (even at runtime, with its subproject Membrane). I believe it is worth exploring further since it can simplify what is usually a chore, although most likely it cannot easily scale.

Just a note of caution: since the project is at a very early stage, there are no strict security measures and the Membrane API could expose information that should not be exposed. Take this into account before releasing anything!