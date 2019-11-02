Title: Apache CarbonData (part 2)
Date: 2019-10-31
Category: projects
Tags: Big Data, data storage format

In the [previous article](https://apothem.blog/apache-carbondata.html) we have seen many exciting features that CarbonData offers, but we haven't explored them all; in this article we will try out the streaming capabilities and we will delve a bit deeper into the data layout, looking at concept like compaction and partitioning, and the way the different files are managed.

## Streaming

Another feature that sets CarbonData apart from other Hadoop data formats is the support for streaming data. Rather than writing many small files or waiting until a larger file can be written, CarbonData uses a slightly different format where single rows can be added as they arrive; such files can later be converted to the standard columnar format (via compaction) in order to support all the features we have already discussed. Every task, including the creation of the sink table and the management of the streaming job, can be performed using SQL commands. Let's see how.

First of all, we need to create a streaming source. An easy way to do this is to use [netcat](https://en.wikipedia.org/wiki/Netcat), a Linux utility that, among many other things, can be used to send data through a socket, thus simulating a process streaming data over the network. We need to open a new terminal (or to use another utility like [screen](https://en.wikipedia.org/wiki/GNU_Screen) or [tmux](https://en.wikipedia.org/wiki/Tmux)) in order to keep *netcat* running while we use the Spark shell; on the new terminal we need to run the following command:

    :::bash
    $ nc -lk 9099

which will seem to be "hanging up", while it will actually be waiting for our input. Let's leave it for now and switch to our running Spark shell with a CarbonData session active.

We need to create a source table that CarbonData will use to interpret the format of the incoming data. For instance, if we want to stream data in CSV format where the first field is an integer and the second is a string, we can create the table like the following:

    :::scala
    > carbon.sql(s"""
        CREATE TABLE source(col1 INT, col2 STRING)
        STORED AS carbondata
        TBLPROPERTIES(
            'streaming' = 'source',
            'format' = 'socket',
            'host' = 'localhost’,
            'port' = '9099',
            'record_format' = 'csv',
            'delimiter' = ',')
       """)

The table properties should be self-explanatory; they are basically Spark Structured Streaming [DataStreamReader]'s(https://spark.apache.org/docs/2.3.4/structured-streaming-programming-guide.html#creating-streaming-dataframes-and-streaming-datasets) options. Once the source table is created, we need to create a sink table as well:

    :::scala
    > carbon.sql(s"""
        CREATE TABLE sink(col1 INT, col2 STRING)
        STORED AS carbondata
        TBLPROPERTIES('streaming' = 'true')
      """)

In this case our sink table mimics the source table exactly, but this is not mandatory. Now we are ready to create the actual streaming job:

    :::scala
    > carbon.sql(s"""
        CREATE STREAM job1 ON TABLE sink
        STMPROPERTIES(
            'trigger' = 'ProcessingTime',
            'interval' = '1 seconds')
        AS
            SELECT *
            FROM source
      """)

which is translated as a Spark [Streaming Query](https://spark.apache.org/docs/2.3.4/structured-streaming-programming-guide.html#starting-streaming-queries). That's all the setup we need.

If we run a `SELECT` query on the sink table, we will not see any results; this is normal because we haven't streamed any data yet. Let's switch to the terminal where *netcat* is running and add a few lines like the following:

    :::text
    1,value1
    2,value2
    10,value10

then switch back to the Spark shell and run a `SELECT` query on the sink table again:

    :::scala
    carbon.sql("SELECT * FROM sink").show

Now we should see the rows we have just inserted!

    :::text
    +----+-------+
    |col1|   col2|
    +----+-------+
    |   1| value1|
    |   2| value2|
    |  10|value10|
    +----+-------+

While the streaming job is running, we can see some information on the job itself by running the following command:

    :::scala
    > carbon.sql("SHOW STREAMS").show

To terminate the streaming job we need to run a `DROP` command using the stream name:

    :::scala
    > carbon.sql("DROP STREAM job1").show

After closing the stream, we could decide to *compact* the sink table and convert its files to the standard CarbonData column-based format. Let's check the table's *segments* first:

    :::scala
    > carbon.sql("SHOW SEGMENTS FOR TABLE sink").show

which should output something like the following:

    :::text
    +-----------------+---------+--------------------+-------------+---------+-----------+---------+----------+
    |SegmentSequenceId|   Status|     Load Start Time|Load End Time|Merged To|File Format|Data Size|Index Size|
    +-----------------+---------+--------------------+-------------+---------+-----------+---------+----------+
    |                0|Streaming|2019-10-31 22:46:...|           NA|       NA|     ROW_V1|   634.0B|    174.0B|
    +-----------------+---------+--------------------+-------------+---------+-----------+---------+----------+

Let's now compact the table:

    :::scala
    > carbon.sql("ALTER TABLE sink COMPACT 'CLOSE_STREAMING'").show

and check the segments again:

    :::text
    +-----------------+---------+--------------------+--------------------+---------+-----------+---------+----------+
    |SegmentSequenceId|   Status|     Load Start Time|       Load End Time|Merged To|File Format|Data Size|Index Size|
    +-----------------+---------+--------------------+--------------------+---------+-----------+---------+----------+
    |                1|  Success|2019-10-31 23:04:...|2019-10-31 23:04:...|       NA|COLUMNAR_V3|   1,22KB|    744.0B|
    |                0|Compacted|2019-10-31 22:46:...|2019-10-31 23:04:...|        1|     ROW_V1|   634.0B|    174.0B|
    +-----------------+---------+--------------------+--------------------+---------+-----------+---------+----------+

The format of the data has actually changed, and it cannot be changed back to `ROW_V1`. We'll see compaction into more detail in the next section.

## Compaction

Whenever we load data into CarbonData, a new folder called *segment* is created; this makes dealing with transactions easier and helps maintaining consistency. In the long run, anyway, the growing number of segments degrades the query performance; *compaction* can then be used to merge multiple segments into one.

CarbonData supports two main types of compaction besides the `CLOSE_STREAMING` that we've seen in the previous section, namely *minor* (based on the number of new segments) and *major* (based on the size of the new segments). We'll see how they work using another table from the TPCH benchmark.

Let's create the `order` table:

    :::scala
    > carbon.sql(s"""
        CREATE TABLE IF NOT EXISTS orders(
            o_orderdate DATE,
            o_orderpriority STRING,
            o_orderstatus STRING,
            o_orderkey INT,
            o_custkey STRING,
            o_totalprice DOUBLE,
            o_clerk STRING,
            o_shippriority INT,
            o_comment STRING)
        STORED AS carbondata
        TBLPROPERTIES(
            'SORT_COLUMNS' = 'o_orderdate')
      """)

and the load some data:

    :::scala
    > carbon.sql(s"""
        LOAD DATA INPATH '/tmp/tpch-dbgen/orders.tbl'
        INTO TABLE orders
        OPTIONS(
            'DELIMITER' = '|',
            'FILEHEADER' = 'o_orderkey,o_custkey,o_orderstatus,o_totalprice,o_orderdate,o_orderpriority,o_clerk,o_shippriority,o_comment')
      """)

We can now look at the segment information for this table:

    :::text
    > carbon.sql("SHOW SEGMENTS FOR TABLE orders").show

which returns:

    :::text
    +-----------------+-------+--------------------+--------------------+---------+-----------+---------+----------+
    |SegmentSequenceId| Status|     Load Start Time|       Load End Time|Merged To|File Format|Data Size|Index Size|
    +-----------------+-------+--------------------+--------------------+---------+-----------+---------+----------+
    |                0|Success|2019-11-02 12:41:...|2019-11-02 12:41:...|       NA|COLUMNAR_V3|  51,20MB|    1,59KB|
    +-----------------+-------+--------------------+--------------------+---------+-----------+---------+----------+

and, if we look at the content of the CarbonData store directory containing the `order` table, we will see something like this:

    :::bash
    $ tree /var/carbondata/data/store/default/orders

    /var/carbondata/data/store/default/orders
    ├── Fact
    │   └── Part0
    │       └── Segment_0
    │           ├── 0_1572694894322.carbonindexmerge
    │           └── part-0-0_batchno0-0-0-1572694887333.carbondata
    ├── LockFiles
    │   ├── Segment_0.lock
    │   └── tablestatus.lock
    └── Metadata
        ├── schema
        ├── segments
        │   └── 0_1572694887333.segment
        └── tablestatus

Let's now load some more data running the same `LOAD` command as before for three more times (there will be duplicate rows, but it does not matter), then check again the segments:

    :::scala
    > carbon.sql("SHOW SEGMENTS FOR TABLE orders").show

which look like this:

    +-----------------+-------+--------------------+--------------------+---------+-----------+---------+----------+
    |SegmentSequenceId| Status|     Load Start Time|       Load End Time|Merged To|File Format|Data Size|Index Size|
    +-----------------+-------+--------------------+--------------------+---------+-----------+---------+----------+
    |                3|Success|2019-11-02 12:50:...|2019-11-02 12:50:...|       NA|COLUMNAR_V3|  51,20MB|    1,59KB|
    |                2|Success|2019-11-02 12:41:...|2019-11-02 12:41:...|       NA|COLUMNAR_V3|  51,20MB|    1,59KB|
    |                1|Success|2019-11-02 12:41:...|2019-11-02 12:41:...|       NA|COLUMNAR_V3|  51,21MB|    1,59KB|
    |                0|Success|2019-11-02 12:41:...|2019-11-02 12:41:...|       NA|COLUMNAR_V3|  51,20MB|    1,59KB|
    +-----------------+-------+--------------------+--------------------+---------+-----------+---------+----------+

and the directory:

    :::bash
    $ tree /var/carbondata/data/store/default/orders

    /var/carbondata/data/store/default/orders
    ├── Fact
    │   └── Part0
    │       ├── Segment_0
    │       │   ├── 0_1572694894322.carbonindexmerge
    │       │   └── part-0-0_batchno0-0-0-1572694887333.carbondata
    │       ├── Segment_1
    │       │   ├── 1_1572694906502.carbonindexmerge
    │       │   └── part-0-0_batchno0-0-1-1572694899093.carbondata
    │       ├── Segment_2
    │       │   ├── 2_1572694914891.carbonindexmerge
    │       │   └── part-0-0_batchno0-0-2-1572694907902.carbondata
    │       └── Segment_3
    │           ├── 3_1572695453562.carbonindexmerge
    │           └── part-0-0_batchno0-0-3-1572695446456.carbondata
    ├── LockFiles
    │   ├── compaction.lock
    │   ├── Segment_0.lock
    │   ├── Segment_1.lock
    │   ├── Segment_2.lock
    │   ├── Segment_3.lock
    │   ├── tablestatus.lock
    │   └── update.lock
    └── Metadata
        ├── schema
        ├── segments
        │   ├── 0_1572694887333.segment
        │   ├── 1_1572694899093.segment
        │   ├── 2_1572694907902.segment
        │   └── 3_1572695446456.segment
        └── tablestatus

Now we can run a minor compaction:

    :::scala
    > carbon.sql("ALTER TABLE orders COMPACT 'MINOR'").show

and see what changed in the segments:

    :::scala
    > carbon.sql("SHOW SEGMENTS FOR TABLE orders").show

which look like this:

    :::text
    +-----------------+---------+--------------------+--------------------+---------+-----------+---------+----------+
    |SegmentSequenceId|   Status|     Load Start Time|       Load End Time|Merged To|File Format|Data Size|Index Size|
    +-----------------+---------+--------------------+--------------------+---------+-----------+---------+----------+
    |                3|Compacted|2019-11-02 12:50:...|2019-11-02 12:50:...|      0.1|COLUMNAR_V3|  51,20MB|    1,59KB|
    |                2|Compacted|2019-11-02 12:41:...|2019-11-02 12:41:...|      0.1|COLUMNAR_V3|  51,20MB|    1,59KB|
    |                1|Compacted|2019-11-02 12:41:...|2019-11-02 12:41:...|      0.1|COLUMNAR_V3|  51,21MB|    1,59KB|
    |              0.1|  Success|2019-11-02 12:51:...|2019-11-02 12:51:...|       NA|COLUMNAR_V3| 146,33MB|    2,81KB|
    |                0|Compacted|2019-11-02 12:41:...|2019-11-02 12:41:...|      0.1|COLUMNAR_V3|  51,20MB|    1,59KB|
    +-----------------+---------+--------------------+--------------------+---------+-----------+---------+----------+

and in the directory:

    :::bash
    $ tree /var/carbondata/data/store/default/orders

    /var/carbondata/data/store/default/orders
    ├── Fact
    │   └── Part0
    │       ├── Segment_0
    │       │   ├── 0_1572694894322.carbonindexmerge
    │       │   └── part-0-0_batchno0-0-0-1572694887333.carbondata
    │       ├── Segment_0.1
    │       │   ├── 0.1_1572695514980.carbonindexmerge
    │       │   └── part-0-0_batchno0-0-0.1-1572695501043.carbondata
    │       ├── Segment_1
    │       │   ├── 1_1572694906502.carbonindexmerge
    │       │   └── part-0-0_batchno0-0-1-1572694899093.carbondata
    │       ├── Segment_2
    │       │   ├── 2_1572694914891.carbonindexmerge
    │       │   └── part-0-0_batchno0-0-2-1572694907902.carbondata
    │       └── Segment_3
    │           ├── 3_1572695453562.carbonindexmerge
    │           └── part-0-0_batchno0-0-3-1572695446456.carbondata
    ├── LockFiles
    │   ├── compaction.lock
    │   ├── Segment_0.lock
    │   ├── Segment_1.lock
    │   ├── Segment_2.lock
    │   ├── Segment_3.lock
    │   ├── tablestatus.lock
    │   └── update.lock
    └── Metadata
        ├── schema
        ├── segments
        │   ├── 0.1_1572695501043.segment
        │   ├── 0_1572694887333.segment
        │   ├── 1_1572694899093.segment
        │   ├── 2_1572694907902.segment
        │   └── 3_1572695446456.segment
        └── tablestatus

A new segment with ID `0.1` has been created, while the other segments are marked as compacted. We had to create 4 segments because the default setting for the parameter `carbon.compaction.level.threshold`, which controls the way minor compactions are performed, is `(4,3)`; it means that 4 segments will be compacted in a "level 1" new segment, and 3 "level 1" segments (when present) will be compacted to a single "level 2" segment. More information on the other configuration parameters can be found on the [website](https://carbondata.apache.org/configuration-parameters.html).

After compaction, the segments which have been compacted are still present; if we want to delete them and free up the space, we can use the following SQL command:

    :::scala
    > carbon.sql("CLEAN FILES FOR TABLE orders").show

which will give the following segments:

    :::text
    +-----------------+-------+--------------------+--------------------+---------+-----------+---------+----------+
    |SegmentSequenceId| Status|     Load Start Time|       Load End Time|Merged To|File Format|Data Size|Index Size|
    +-----------------+-------+--------------------+--------------------+---------+-----------+---------+----------+
    |              0.1|Success|2019-11-02 12:51:...|2019-11-02 12:51:...|       NA|COLUMNAR_V3| 146,33MB|    2,81KB|
    +-----------------+-------+--------------------+--------------------+---------+-----------+---------+----------+

and the following directory structure:

    :::bash
    $ tree /var/carbondata/data/store/default/orders

    /var/carbondata/data/store/default/orders
    ├── Fact
    │   └── Part0
    │       └── Segment_0.1
    │           ├── 0.1_1572695514980.carbonindexmerge
    │           └── part-0-0_batchno0-0-0.1-1572695501043.carbondata
    ├── LockFiles
    │   ├── clean_files.lock
    │   ├── compaction.lock
    │   ├── Segment_0.lock
    │   ├── Segment_1.lock
    │   ├── Segment_2.lock
    │   ├── Segment_3.lock
    │   ├── tablestatus.lock
    │   └── update.lock
    └── Metadata
        ├── schema
        ├── segments
        │   └── 0.1_1572695501043.segment
        ├── tablestatus
        └── tablestatus.history

The major compaction works in a similar way and it is performed by running the following command:

    :::scala
    carbon.sql("ALTER TABLE orders COMPACT 'MAJOR'").show

By default (parameter `carbon.major.compaction.size`) the compaction will only take place on the segments whose sum of the sizes is below 1024 MB. You can try this out as well by loading data once more and running the SQL command.

### Update and Delete operations

There is another type of compaction, called *horizontal compaction*, that takes place on delta files created by Update and Delete operations. Whenever an Update is performed, two files are created:

- an *Insert Delta* file which stores newly added rows in the CarbonData columnar format;
- a *Delete Delta* file which only stores the IDs of the rows that are deleted in a Bitmap file format.

For instance, if we start from this directory structure (clean table, one load):

    :::text
    ├── Fact
    │   └── Part0
    │       └── Segment_0
    │           ├── 0_1572700087590.carbonindexmerge
    │           └── part-0-0_batchno0-0-0-1572700080525.carbondata
    ├── LockFiles
    │   ├── Segment_0.lock
    │   └── tablestatus.lock
    └── Metadata
        ├── schema
        ├── segments
        │   └── 0_1572700080525.segment
        └── tablestatus

and run this update:

    :::scala
    > carbon.sql(s"""
        UPDATE orders
        SET (o_orderdate) = ('2016-06-06')
        WHERE o_orderdate = '1996-06-06'
    """).show

the directory will be updated like so:

    :::text
    ├── Fact
    │   └── Part0
    │       └── Segment_0
    │           ├── 0_1572700087590.carbonindexmerge
    │           ├── 1_batchno0-0-0-1572700111168.carbonindex
    │           ├── part-0-0_batchno0-0-0-1572700080525.carbondata
    │           ├── part-0-0_batchno0-0-0-1572700111168.deletedelta
    │           └── part-0-1_batchno0-0-0-1572700111168.carbondata
    ├── LockFiles
    │   ├── compaction.lock
    │   ├── meta.lock
    │   ├── Segment_0.lock
    │   ├── Segment_.lock
    │   ├── tablestatus.lock
    │   ├── tableupdatestatus.lock
    │   └── update.lock
    └── Metadata
        ├── schema
        ├── segments
        │   ├── 0_1572700080525.segment
        │   └── 0_1572700111168.segment
        ├── tablestatus
    └── tableupdatestatus-1572700111168

basically creating:

- a `.carbonindex` file;
- a `.deletedelta` file;
- a new `.carbondata` file;
- a new `.segment` file;
- a `tableupdatestatus-` file.

A Delete operation, instead, creates the *Delete Delta* file only. Let's run another update:

    :::scala
    > carbon.sql(s"""
        UPDATE orders
        SET (o_orderdate) = ('2016-06-05')
        WHERE o_orderdate = '1996-06-05'
    """).show

If we run the `tree` command we'll see that there will be one or more files for each of the 4 types in the list. Now, if we run the `CLEAN` command again:

    :::scala
    > carbon.sql("CLEAN FILES FOR TABLE orders").show

we will see that there is again only one file per type (except for the `.segment` files). This behaviour is controlled by the following parameters:

- `carbon.horizontal.compaction.enable`: enables this kind of compaction (default is `true`);
- `carbon.horizontal.update.compaction.threshold`: number of *Update delta* files above which the compaction will take place (default is 1);
- `carbon.horizontal.delete.compaction.threshold`: number of *Delete delta* files above which the compaction will take place (default is 1).

## Partitioning

Partitioning is a data organization strategy used to increase performance and isolation. CarbonData offers two kinds of partitions, a "standard" one (similar to [Spark](https://spark.apache.org/docs/2.3.4/sql-programming-guide.html#partition-discovery) and Hive partitions) and a "CarbonData" one (that supports several partitioning schemes such as ranges, hashes, and lists, but no Update/Delete); since the latter is still experimental, we will only focus on the former.

A partitioned table can be created with the usual Spark/Hive `PARTITIONED BY` syntax:

    :::scala
    > carbon.sql(s"""
        CREATE TABLE IF NOT EXISTS orders_part(
            o_orderdate DATE,
            o_orderpriority STRING,
            o_orderkey INT,
            o_custkey STRING,
            o_totalprice DOUBLE,
            o_clerk STRING,
            o_shippriority INT,
            o_comment STRING)
        PARTITIONED BY(o_orderstatus STRING)
        STORED AS carbondata
        TBLPROPERTIES('SORT_COLUMNS' = 'o_orderdate')
      """)

paying attention to exclude the partitioning column from both the list of columns and from the `SORT_COLUMNS` table property (if present).

The data can be loaded in the usual way when using *dynamic partitioning*, i.e. without specifying the partition to write to:

    :::scala
    > carbon.sql(s"""
        LOAD DATA INPATH '/tmp/tpch-dbgen/orders.tbl'
        INTO TABLE orders_part
        OPTIONS(
            'DELIMITER' = '|',
            'FILEHEADER' = 'o_orderkey,o_custkey,o_orderstatus,o_totalprice,o_orderdate,o_orderpriority,o_clerk,o_shippriority,o_comment')
      """)

and the partitioned column can be used to quickly filter data:

    :::scala
    > carbon.sql("SELECT COUNT(*) FROM orders_part WHERE o_orderstatus = 'F'").show

The partitions can be shown using the following command:

    :::scala
    > carbon.sql("SHOW PARTITIONS orders_part").show

and we can see their layout using the `tree` command on the new directory:

    :::bash
    $ tree /var/carbondata/data/store/default/orders_part

    /var/carbondata/data/store/default/orders_part
    ├── LockFiles
    │   ├── Segment_0.lock
    │   └── tablestatus.lock
    ├── Metadata
    │   ├── schema
    │   ├── segments
    │   │   └── 0_1572701993390.segment
    │   └── tablestatus
    ├── o_orderstatus=F
    │   ├── 0_1572702007421.carbonindexmerge
    │   ├── part-0-100100000100001_batchno0-0-0-1572701993390.carbondata
    │   ├── part-0-100100001100001_batchno0-0-0-1572701993390.carbondata
    │   ├── part-0-100100002100001_batchno0-0-0-1572701993390.carbondata
    │   ├── part-0-100100003100001_batchno0-0-0-1572701993390.carbondata
    │   ├── part-0-100100004100001_batchno0-0-0-1572701993390.carbondata
    │   └── part-0-100100005100001_batchno0-0-0-1572701993390.carbondata
    ├── o_orderstatus=O
    │   ├── 0_1572702007422.carbonindexmerge
    │   ├── part-0-100100000100002_batchno0-0-0-1572701993390.carbondata
    │   ├── part-0-100100001100002_batchno0-0-0-1572701993390.carbondata
    │   ├── part-0-100100002100002_batchno0-0-0-1572701993390.carbondata
    │   ├── part-0-100100003100002_batchno0-0-0-1572701993390.carbondata
    │   ├── part-0-100100004100002_batchno0-0-0-1572701993390.carbondata
    │   └── part-0-100100005100002_batchno0-0-0-1572701993390.carbondata
    ├── o_orderstatus=P
    │   ├── 0_1572702007422.carbonindexmerge
    │   ├── part-0-100100000100003_batchno0-0-0-1572701993390.carbondata
    │   ├── part-0-100100001100003_batchno0-0-0-1572701993390.carbondata
    │   ├── part-0-100100002100003_batchno0-0-0-1572701993390.carbondata
    │   ├── part-0-100100003100003_batchno0-0-0-1572701993390.carbondata
    │   ├── part-0-100100004100003_batchno0-0-0-1572701993390.carbondata
    │   └── part-0-100100005100003_batchno0-0-0-1572701993390.carbondata
    └── _SUCCESS

where we can see that, instead of the usual `Fact/Part0/Segment_0` structure, we have one directory per partition. With this structure, Update Delta and Delete Delta files are created within each folder. Whether partitions can make queries more efficient as opposed to MDKs and dictionaries will likely depend on the use case.

## Conclusions

As we have been digging deeper into the internals of CarbonData, we have discovered that there are not only many interesting features to cover different use cases, but also many tools to increase the performance. I would suggest to take a look at the list of [configuration parameters](https://carbondata.apache.org/configuration-parameters.html) as well as at the list of [use cases](https://carbondata.apache.org/usecases.html), since they can provide some guidance in the (daunting) task getting the better out of CarbonData. Have fun!