Title: Apache CarbonData
Date: 2019-09-30
Category: projects
Tags: Big Data, data storage format

In the last few years I have been working quite extensively with Apache Spark, and I have come to realize that a good storage format goes a long way toward efficiency and speed. For instance, when dealing with large CSV or JSON files, adding an [Apache Parquet](https://parquet.apache.org/) writing step would improve performance in virtually every subsequent task, or at least in all tasks that would profit from a columnar storage. I have briefly dabbled with [Apache ORC](https://orc.apache.org/) and, then, I found out a rather new format which I haven't really explored until last month, which is what we will see in this article: enter [Apache CarbonData](https://carbondata.apache.org/).

Developed by Huawei and launched as an Apache Incubator project in 2016, CarbonData is now is at version 1.6.0. The reasons why it caught my interest are several:

- the promise to cover different use cases (full scan queries, small scan queries, multi-dimensional OLAP queries) at the same time;
- the tight integration with Spark and other processing engines;
- the increased encoding efficiency thanks to global and local dictionaries;
- the speed-up on filter queries thanks to multi-level indexing;
- the support for Update and Delete operations;
- the concept of Datamaps, additional structures (Time Series, Bloom filter, Lucene full-text, Materialized Views); to reduce execution time for some classes of analytics queries;
- the support of streaming use cases via near-real time insertion.

That's quite a lot of features! So, let's see how to make use of each one of them. As usual, I will refer to a CentOS 7 system; there are not so many tools that need to be installed: besides the usual `wget`, `git`, and `Java 8`, we will need `gcc` in order to compile the data generation library.

## Data

In order to generate data to load in our CarbonData tables we will use the TPC-H *dbgen* tool, which is commonly used for database benchmarks (and, in fact, is used to benchmark CarbonData as well). The tool creates synthetic data based on a real-world scenario, where vendors place orders to buy parts from suppliers and to sell parts to customers. The TPC-H benchmark includes a query generation tool as well, which we won't use here.

To build our dataset, let's clone the repo into `/tmp` (or any other folder) and build the tools:

    :::bash
    $ cd /tmp
    $ git clone https://github.com/electrum/tpch-dbgen
    $ cd tpch-dbgen
    $ make

and, once finished, let's run the following command:

    :::bash
    $ ./dbgen -v

which will create 8 files for a total size of about 1 GB. If you want to create larger files you can use the `-s` parameter (the scale factor) as in this example, which will generate about 10 GB of data:

    :::bash
    $ ./dbgen -s 10 -v

We will mostly use only one file, `lineitem.tbl`, which is the largest one; anyway, the other files can provide some more context - and can be used for more experiments.

## Spark and CarbonData

We will explore CarbonData features using the simplest setup: a Spark shell in standalone mode with CarbonData already packaged as a JAR file. We therefore need to:

- download Spark from [this page](https://www.apache.org/dyn/closer.lua/spark/spark-2.3.4/spark-2.3.4-bin-hadoop2.7.tgz) (we will use Spark 2.3.4 since the latest version of CarbonData is compatible with Spark up to 2.3.2);
- extract the content of the `.tgz` file into a folder (e.g. `/opt/spark`);
- download the latest version of the CarbonData JAR file built for Spark 2.3.2 from [here](https://dist.apache.org/repos/dist/release/carbondata/1.6.0/apache-carbondata-1.6.0-bin-spark2.3.2-hadoop2.7.2.jar);
- copy the JAR file to the Spark folder.

We can then launch the Spark shell from the Spark folder as follows:

    :::bash
    $ spark-shell --jars apache-carbondata-1.6.0-bin-spark2.3.2-hadoop2.7.2.jar

and, once the shell is running, we need to create a `CarbonSession` (which is similar to a `SparkSession`). Since we will run everything on the local filesystem, we can create a folder such as `/var/carbondata` (and assign it a suitable owner and permissions) where we will store both the data and the metastore; supposing that the data will be saved in `/var/carbondata/data/store` and the metastore in `/var/carbondata/metastore`, the `CarbonSession` can be created as follows:

    :::scala
    import org.apache.spark.sql.SparkSession
    import org.apache.spark.sql.CarbonSession._

    val carbon = SparkSession.builder()
                .config(sc.getConf)
                .getOrCreateCarbonSession("/var/carbondata/data/store", "/var/carbondata/metastore")

(Pro tip: a whole piece of code can be pasted and run into the Scala shell by running the command `:paste`, pasting the code, and pressing Ctrl + D)

Now we are ready!

## Creating tables and loading data

First of all, we need to create a table and load some data into it. Every SQL command can be run via the `carbon.sql()` method, so we can create a `lineitem` table in this way:

    :::scala
    carbon.sql("CREATE TABLE IF NOT EXISTS lineitem(l_shipdate DATE, l_shipmode STRING, l_shipinstruct STRING, l_returnflag STRING, l_receiptdate DATE, l_orderkey INT, l_partkey INT, l_suppkey STRING, l_linenumber INT, l_quantity DOUBLE, l_extendedprice DOUBLE, l_discount DOUBLE, l_tax DOUBLE, l_linestatus STRING, l_commitdate DATE, l_comment STRING) STORED AS carbondata")

and then load data like so:

    :::scala
    carbon.sql("LOAD DATA INPATH '/tmp/tpch-dbgen/lineitem.tbl' INTO TABLE lineitem OPTIONS('DELIMITER' = '|', 'FILEHEADER' = 'l_orderkey,l_partkey,l_suppkey,l_linenumber,l_quantity,l_extendedprice,l_discount,l_tax,l_returnflag,l_linestatus,l_shipdate,l_commitdate,l_receiptdate,l_shipinstruct,l_shipmode,l_comment')")

We can run SQL queries like so:

    :::scala
    carbon.sql("SELECT COUNT(*) FROM lineitem WHERE l_shipdate = '1996-06-06'").show

and also time every query using `spark.time()`, for instance:

    :::scale
    spark.time(carbon.sql("SELECT COUNT(*) FROM lineitem WHERE l_shipdate = '1996-06-06'").show)

## Multi-dimensional keys (MDKs)

Let's now create and populate a new table using multi-dimensional keys (MDKs) by means of the `SORT_COLUMNS` table property:

    :::scala
    carbon.sql("CREATE TABLE IF NOT EXISTS lineitem_sorted(l_shipdate DATE, l_shipmode STRING, l_shipinstruct STRING, l_returnflag STRING, l_receiptdate DATE, l_orderkey INT, l_partkey INT, l_suppkey STRING, l_linenumber INT, l_quantity DOUBLE, l_extendedprice DOUBLE, l_discount DOUBLE, l_tax DOUBLE, l_linestatus STRING, l_commitdate DATE, l_comment STRING) STORED AS carbondata TBLPROPERTIES ('SORT_COLUMNS' = 'l_shipdate,l_shipmode,l_shipinstruct,l_receiptdate,l_commitdate,l_returnflag,l_linestatus')")

    carbon.sql("LOAD DATA INPATH '/tpch-dbgen/small/lineitem.tbl' INTO TABLE lineitem_dic OPTIONS('DELIMITER' = '|', 'FILEHEADER' = 'l_orderkey,l_partkey,l_suppkey,l_linenumber,l_quantity,l_extendedprice,l_discount,l_tax,l_returnflag,l_linestatus,l_shipdate,l_commitdate,l_receiptdate,l_shipinstruct,l_shipmode,l_comment')")

Let's run the following query:

    :::scala
    spark.time(carbon.sql("SELECT COUNT(*) FROM lineitem WHERE l_shipdate = '1996-06-06'").show)

On my machine, a VPS with 8 vCPUs and 32 GB of RAM, it took about 4.2 seconds. Now let's run the same query on the `lineitem_sorted` table:

    :::scala
    spark.time(carbon.sql("SELECT COUNT(*) FROM lineitem_sorted WHERE l_shipdate = '1996-06-06'").show)

It took 90 *milliseconds*! So, indeed, MDKs are improving significantly the queries that make use of filters. Let's try with another query on both tables:

    :::scala
    spark.time(carbon.sql("SELECT l_shipdate, COUNT(*) c FROM lineitem WHERE l_commitdate < '1996-01-01' GROUP BY l_shipdate ORDER BY c DESC").show)

    spark.time(carbon.sql("SELECT l_shipdate, COUNT(*) c FROM lineitem_sorted WHERE l_commitdate < '1996-01-01' GROUP BY l_shipdate ORDER BY c DESC").show)

In this case the first one takes about 5 seconds, while the second one takes about 3 seconds.

Let's now take a look at the directories and files that CarbonData created under `/var/carbondata/data/store`:

    :::bash
    $ ls -lah /var/carbondata/data/store

We'll see that there are two folders, `default` and `_system`, where the first one is used to store the default database; since we didn't create a new database, our tables will be a `lineitem` and a `lineitem_sorted` directories within `default`. If we have `tree` installed (and, if not, we can simply install it with `sudo yum install tree`), we can see for instance the structure of `lineitem`:

    :::bash
    $ tree /var/carbondata/data/store/default/lineitem

    :::text
    /var/carbondata/data/store/default/lineitem
    ├── Fact
    │   └── Part0
    │       └── Segment_0
    │           ├── 0_1569876396402.carbonindexmerge
    │           └── part-0-0_batchno0-0-0-1569876355317.carbondata
    ├── LockFiles
    │   ├── Segment_0.lock
    │   └── tablestatus.lock
    └── Metadata
        ├── schema
        ├── segments
        │   └── 0_1569876355317.segment
        └── tablestatus

The file names will most likely be different, but we are interested in the directory structure; for more details on CarbonData file format, take a look at the [documentation](https://carbondata.apache.org/file-structure-of-carbondata.html). If we look at the size of the `Fact` directory, we will see that it is approximately 222 MB:

    :::bash
    $ du -sh /var/carbondata/data/store/default/lineitem/Fact

If we look at the size of the same directory for the `lineitem_sorted` directory, instead, we will see that it's 190 MB! So, MDKs are convenient from the storage point of view as well.

## Update and Delete operations

Update operations are very simple in CarbonData. The format is the following:

    :::sql
    UPDATE <table_name> 
    SET (column_name_1, column_name_2, ... column_name_n) = (column_1_expression, column_2_expression, ... column_n_expression )
    [ WHERE { <filter_condition> } ]

for simple updates where the column expressions are calculated from the same table, or the following for more generic updates:

    :::sql
    UPDATE <table_name>
    SET (column_name_1, column_name_2) = (SELECT sourceColumn_1, sourceColumn_2 FROM sourceTable [ WHERE { <filter_condition> } ] )
    [ WHERE { <filter_condition> } ]

Let's see an example. First of all, let's check the total number of records and the number of records for a specific `l_shipdate`:

    :::scala
    carbon.sql("SELECT COUNT(*) FROM lineitem_sorted").show

    carbon.sql("SELECT COUNT(*) FROM lineitem_sorted WHERE l_shipdate = '1996-06-06'").show

We get 6,001,215 and 2,454 results respectively. Let's update the `l_shipdate` for those same records:

    :::scala
    carbon.sql("UPDATE lineitem_sorted SET (l_shipdate) = ('2016-06-06') WHERE l_shipdate = '1996-06-06'").show

Now, running the second `COUNT` query will not return any results, while we'll get 2,454 results by running this query instead:

    :::scala
    carbon.sql("SELECT COUNT(*) FROM lineitem_sorted WHERE l_shipdate = '2016-06-06'").show

The Delete operation is even simpler. Let's run the following query:

    :::scala
    carbon.sql("DELETE FROM lineitem_sorted WHERE l_shipdate = '2016-06-06'").show

Now the last `COUNT` query will return zero results.

## Datamaps

The concept of datamap is quite interesting: basically, a new data structure is added on top of the existing data in order to improve the performance of some specific queries. Let's look for instance at the *Lucene* datamap, which adds a Lucene-based full-text index to a give column. 

### Lucene datamap

In order to create a Lucene full-text datamap, we run the following query:

    :::scala
    carbon.sql("CREATE DATAMAP comment ON TABLE lineitem_sorted USING 'lucene' DMPROPERTIES('INDEX_COLUMNS' = 'l_comment', 'SPLIT_BLOCKLET' = 'false')")

We have just created a Lucene index on the `l_comment` column which stores the BlockletIds as well (it is not very clear to me why but, if this property is not present, the full-text queries throw exceptions). When the index is ready we can run queries such as the following, where we ask for comments containing words that start with `quick`:

    :::scala
    carbon.sql("SELECT l_comment FROM lineitem_sorted WHERE TEXT_MATCH_WITH_LIMIT('l_comment:quick*', 10)").show(false)

which will return a result like this:

    :::text
    +------------------------------------------+
    |l_comment                                 |
    +------------------------------------------+
    |fix. quickly ironic instruct              |
    | packages detect furiously quick          |
    |ely ironic deposits sleep quickly un      |
    |ffily regular ideas haggle quick          |
    |y ironic instructions among the quick     |
    |ts wake quickly after the u               |
    |e quickly along the express ideas-- slyly |
    |ctions. quickly even                      |
    |about the quickly express pl              |
    |s nag quick                               |
    |ly regular deposits. even deposits kindle |
    |ly. furiously                             |
    |ajole slyly after the blithely re         |
    |aggle blithely slyly even inst            |
    |ithe pinto beans. special, iron           |
    |silent foxes. slyly                       |
    |sts sleep af                              |
    |. daring pinto beans wake                 |
    |slyly after the furio                     |
    | ironic requests. final, ironic depo      |
    +------------------------------------------+

or like the following, where we ask for comments containing words that start with `quick` but no words that start with `ironic`:

    :::scala
    carbon.sql("SELECT l_comment FROM lineitem_sorted WHERE TEXT_MATCH_WITH_LIMIT('l_comment:quick* -l_comment:ironic*', 10)").show(false)

which will result in something like this:

    :::text
    +------------------------------------------+
    |l_comment                                 |
    +------------------------------------------+
    | packages detect furiously quick          |
    |ffily regular ideas haggle quick          |
    |ts wake quickly after the u               |
    |e quickly along the express ideas-- slyly |
    |ctions. quickly even                      |
    |about the quickly express pl              |
    |s nag quick                               |
    |gle slowly. quickly regular theodo        |
    |t quickly blithely                        |
    |unts affix quickly! regu                  |
    |ly. furiously                             |
    |aggle blithely slyly even inst            |
    |silent foxes. slyly                       |
    |sts sleep af                              |
    |. daring pinto beans wake                 |
    |slyly after the furio                     |
    | ironic requests. final, ironic depo      |
    | orbits. blithely unusual ideas above th  |
    |ost after the furiously express           |
    |kly final accounts wake b                 |
    +------------------------------------------+

Another thing which is not clearly specified is why more than 10 results are returned even though, starting with the 11th, they seem irrelevant; until this is clarified, I would recommend to add a `LIMIT 10` to the query.

### Time Series datamap

Another useful datamap is the Time Series datamap, which creates a separate table to optimize queries on time series. We can run queries like the following without a datamap:

    :::scala
    carbon.sql("SELECT TIMESERIES(l_shipdate, 'year') t, AVG(l_quantity) FROM lineitem_sorted GROUP BY t ORDER BY t DESC")

where we calculate the average `l_quantity` for every year, but the performance would not be great (it takes about 4.2 seconds on my machine). We can instead create a Time Series datamap, but we first need to convert the `l_shipdate` to a `timestamp` field, and since we already created a datamap on our table we cannot run any `ALTER TABLE` statements; we can anyway create a new table with a *CTAS* (*create table as*) statement adding a `l_shipdate_t` field of type `timestamp` from the existing `l_shipdate` field:

    :::scala
    carbon.sql("CREATE TABLE lineitem_t STORED AS carbondata AS SELECT *, timestamp(l_shipdate) l_shipdate_t FROM lineitem")

and then create a datamap on top of the newly-created table:

    :::scala
    carbon.sql("CREATE DATAMAP agg_qty_year ON TABLE lineitem_t USING 'timeseries' DMPROPERTIES('EVENT_TIME' = 'l_shipdate_t', 'YEAR_GRANULARITY' = '1') AS SELECT l_shipdate_t, AVG(l_quantity) qty FROM lineitem_t GROUP BY l_shipdate_t")

Now, the previous query (rewritten just to use the new table and the added field) will run much faster:

    :::scala
    spark.time(carbon.sql("SELECT TIMESERIES(l_shipdate_t, 'year') t, AVG(l_quantity) FROM lineitem_t GROUP BY t ORDER BY t DESC").show)

(it takes less than 1 second on my machine).

The query and the datamap we have created work on a year granularity, but we can create as many datamaps as we need to support finer granularities (down to the minute).

### Multivalue datamap

The last datamap we will see (as we are not going to cover the Bloom datamap) is the Multivalued (MV) datamap, which generalizes the deprecated Pre-Aggregate datamap. This type of datamap is very useful for aggregation queries such as the following:

    :::scala
    carbon.sql("SELECT l_partkey, AVG(l_quantity) avg_q, AVG(l_extendedprice) avg_p FROM lineitem_sorted GROUP BY l_partkey ORDER BY avg_q DESC LIMIT 10").show

where we calculate several aggregated quantities after grouping by the `l_partkey` field, whose cardinality is relatively high. This query takes about 2.8 seconds on my machine.

Let's create an MV datamap:

    :::scala
    carbon.sql("CREATE DATAMAP avg_qty_price ON TABLE lineitem_sorted USING 'MV' AS SELECT l_partkey, AVG(l_quantity) avg_q, AVG(l_extendedprice) avg_p FROM lineitem_sorted GROUP BY l_partkey")

Now the previous query takes less than half a second. It is worth noting that, now that the datamap is in place, every time that new data are added (for instance via the `INSERT` statement) the datamap will reflect the changes.

We can also make sure that the query actually makes use of the datamap by using the `explain` method:

    :::bash
    carbon.sql("SELECT l_partkey, AVG(l_quantity) avg_q, AVG(l_extendedprice) avg_p FROM lineitem_sorted GROUP BY l_partkey ORDER BY avg_q DESC LIMIT 10").explain

The resulting plan is the following:

    :::text
    == Physical Plan ==
    TakeOrderedAndProject(limit=10, orderBy=[avg_q#2573 DESC NULLS LAST], output=[l_partkey#2689,avg_q#2573,avg_p#2574])
    +- *(1) Project [lineitem_sorted_l_partkey#2572 AS l_partkey#2689, avg_q#2573, avg_p#2574]
       +- *(1) FileScan carbondata default.avg_qty_price_table[lineitem_sorted_l_partkey#2572,avg_q#2573,avg_p#2574] ReadSchema: struct<avg_p:double,avg_q:double,lineitem_sorted_l_partkey:int>

where we can see a `FileScan` on the `avg_qty_price_table` table (the MV datamap is backed by a table).

## Conclusions

We have seen some of the best features that CarbonData offers, although we haven't looked in too much detail at the performance and at the structure of the data, and we haven't explored the streaming capabilities and other integrations. The documentation is quite good even though some changes are not well described (for instance, after the `SORT_COLUMNS` option has been introduced, do we still need the `DICTIONARY_INCLUDE` option? what is the difference?), but the project is still alive and has a fairly large community to support it. I definitely want to find out more and to follow it closely.