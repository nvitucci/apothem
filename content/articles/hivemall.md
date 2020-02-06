Title: Apache Hivemall
Date: 2020-02-02
Category: projects
Tags: Big Data, Machine Learning

With this article we will move a little bit out of the data engineering space and delve into another subject I love: we will explore the world of distributed machine learning with [Apache Hivemall](https://hivemall.incubator.apache.org/). From the project's homepage:

    :::quote
    Hivemall is a scalable machine learning library that runs on Apache Hive, Spark and Pig.

In short, Hivemall is a collection of Hive UDFs (User-Defined Functions) to create, train, and evaluate machine learning models using any of the supported engines. Since Hive provides a SQL-like query language, Hivemall is basically **machine learning in SQL**; it is then well suited to users who are already fluent in SQL or who need an additional abstraction layer on top of machine learning libraries.

We will explore some of the many capabilities that Hivemall provides by tackling one of the most common machine learning tasks: classification. Let's start by setting up the environment.

### Setting up Hivemall and Spark

Like for other Java-based Apache projects, we will need to install git, Java 8, and Maven 3.5+ (check [the article on Apache Atlas](https://apothem.blog/apache-atlas.html) if you need a detailed walkthrough). Once we have installed everything, we need to build Hivemall:

    :::bash
    $ git clone https://github.com/apache/incubator-hivemall.git
    $ cd incubator-hivemall
    $ bin/build.sh

Since Hive is a bit cumbersome to install and configure, and we will need to do a bit of data preprocessing as well, we will run Hive queries from Spark instead. We therefore need to:

- download Spark 2.4.4 from [this page](https://spark.apache.org/downloads.html) (choosing the 2.4.4 release pre-built for Hadoop 2.7);

- extract the content of the .tgz file into a directory, possibly alongside the directory where we cloned the Hivemall repository:

        :::bash
        $ tar zxvf spark-2.4.4-bin-hadoop2.7.tgz

- launch the Spark shell with the Hivemall JAR file (release `0.6.2-SNAPSHOT` as of now) built before:

        :::bash
        $ spark-2.4.4-bin-hadoop2.7/bin/spark-shell \
          --jars incubator-hivemall/target/hivemall-all-0.6.2-incubating-SNAPSHOT.jar

Once the Spark shell is running, we need to load all the Hivemall functions:

    :::scala
    scala> :load incubator-hivemall/resources/ddl/define-all.spark

We will likely see some errors because some Hivemall functions already exist in Spark 2.4.4, but there is no need to worry because the Spark functions will not be overridden. We are now ready to start using Hivemall!

### Classification

[Classification](https://en.wikipedia.org/wiki/Classification_(machine_learning)) is the task of assigning a category to an _observation_ based on the value of its _features_. For example, we may have some emails that we want to classify as "spam" or "non-spam" based on the presence of one or more keywords; this is called _binary classification_ because we only have two categories, or one category that an instance belongs to or not. Another example, which is a sort of "Hello world" for machine learning and classification, is the categorization of a specific variant of the [iris](https://en.wikipedia.org/wiki/Iris_(plant)) plant depending on features such as the length and width of its sepals and petals; this is called _multiclass classification_ because there are more than two different classes. We will use the [Iris Data Set](https://archive.ics.uci.edu/ml/datasets/Iris) in this section.

The algorithm we will use is called [XGBoost](https://xgboost.readthedocs.io/en/latest/). There are several reasons behind this choice:

- I like its conceptual simplicity and its _interpretability_, which is an important feature of modern machine learning algorithms;
- it is designed for efficiency and has already proved itself;
- it does not require a lot of preprocessing (for instance, it does not require feature scaling);
- it is now supported in Hivemall starting with version 0.6.0 (the supported XGBoost version being 0.90).

If you are interested in the theoretical and technical details, do take a look at the excellent documentation [here](https://xgboost.readthedocs.io/en/latest/tutorials/model.html). For our purposes, we need to keep in mind just one thing: simplifying a lot, XGBoost will basically give us a group of decision trees.

#### Data preprocessing

First of all, we need to download our dataset from [here](https://archive.ics.uci.edu/ml/machine-learning-databases/iris/iris.data) and put it alongside the previous directories. The data will look like the following:

    :::text
    5.1,3.5,1.4,0.2,Iris-setosa
    4.9,3.0,1.4,0.2,Iris-setosa
    4.7,3.2,1.3,0.2,Iris-setosa
    4.6,3.1,1.5,0.2,Iris-setosa
    5.0,3.6,1.4,0.2,Iris-setosa
    ...

Let's go back to our Spark shell and run the following command:

    :::scala
    scala> val iris = spark.read.option("inferSchema", true).csv("iris.data").toDF(
        "sepal_length", "sepal_width", "petal_length", "petal_width", "class")

This command will read the dataset file interpreting it as a CSV file, automatically creating a schema and assigning the provided names to the columns. We can check both the schema and the first 5 rows of the dataset:

    :::scala
    scala> iris.printSchema
    scala> iris.show(5)

Now we can create a temporary view of our Spark Dataframe so that we can use it like a Hive table:

    :::scala
    scala> iris.createOrReplaceTempView("iris")

and then we can run a SQL query as a check:

    :::scala
    scala> spark.sql("SELECT * FROM iris").show(5)

<!-- This is commented out. -->

    :::text
    +------------+-----------+------------+-----------+-----------+
    |sepal_length|sepal_width|petal_length|petal_width|      class|
    +------------+-----------+------------+-----------+-----------+
    |         5.1|        3.5|         1.4|        0.2|Iris-setosa|
    |         4.9|        3.0|         1.4|        0.2|Iris-setosa|
    |         4.7|        3.2|         1.3|        0.2|Iris-setosa|
    |         4.6|        3.1|         1.5|        0.2|Iris-setosa|
    |         5.0|        3.6|         1.4|        0.2|Iris-setosa|
    +------------+-----------+------------+-----------+-----------+

We have our raw data table, but in order to run any Hivemall algorithm we need to tweak it a little. More specifically, we need to:

- assign a unique ID to each row;
- create a _feature vector_ such as `[1:5.1, 2:3.5, 3:1.4, 4:0.2]`, that is a string array where each element is of the form `feature:value`, from the feature columns;
- transform the iris "class" from a string to an integer value.

These steps are part of a very important phase of a machine learning pipeline called _feature engineering_. We can create a new table with all these transformations with the following command:

    :::scala
    scala> spark.sql("""
        CREATE TABLE iris_processed AS
        SELECT monotonically_increasing_id() rowid,
        indexed_features(sepal_length, sepal_width, petal_length, petal_width) features,
        quantify(true, class) label
        FROM iris
        ORDER BY class""")

While `monotonically_increasing_id` is a Spark function, `indexed_features` and `quantify` are both Hivemall UDFs:

- `indexed_features` will create an array from the values passed as parameters, prepending each value with its position in the array (starting from 1, not 0, since 0 is reserved for the [bias feature](https://hivemall.incubator.apache.org/userguide/tips/addbias.html));
- `quantify` can be used to convert a categorical variable into a numerical variable (the `ORDER BY` is used to make sure that it is applied on one reducer only, thus consistently associating the same number to the same non-numerical variable).

There are [other ways](https://hivemall.incubator.apache.org/userguide/tips/rowid.html) to create a unique ID for each row; Hivemall provides a function called `rowid`, but it does not work in Spark (it would throw a `java.lang.IllegalStateException: MapredContext is not set` exception).

Let's see how the new table looks like:

    :::scala
    scala> spark.sql("SELECT * FROM iris_processed").show(5, false)

<!-- This is commented out. -->

    :::text
    +-----+----------------------------+-----+
    |rowid|features                    |label|
    +-----+----------------------------+-----+
    |0    |[1:5.1, 2:3.5, 3:1.4, 4:0.2]|0    |
    |1    |[1:4.9, 2:3.0, 3:1.4, 4:0.2]|0    |
    |2    |[1:4.7, 2:3.2, 3:1.3, 4:0.2]|0    |
    |3    |[1:4.6, 2:3.1, 3:1.5, 4:0.2]|0    |
    |4    |[1:5.0, 2:3.6, 3:1.4, 4:0.2]|0    |
    +-----+----------------------------+-----+

The table is ready to be used for training.

#### Training

We need to add one more function first (which should be included in the `define-all.spark` file now, but are not at the moment):

    :::scala
    scala> spark.sql("CREATE TEMPORARY FUNCTION train_xgboost AS 'hivemall.xgboost.XGBoostTrainUDTF'")

We also need to set the `spark.sql.shuffle.partitions` (or `mapred.reduce.tasks` if we use Hive directly, not through Spark) configuration parameter to a "low" number, for instance to 10 (instead of the default 200).

    :::scala
    scala> spark.sql("SET spark.sql.shuffle.partitions=10")

If we don't do this and the dataset is small (as in our case, with only 150 rows), we will have some empty partitions which will cause an error like the following during the training phase:

    :::text
    ...
    Caused by: ml.dmlc.xgboost4j.java.XGBoostError: [01:14:14] /home/travis/build/myui/build-xgboost-jvm/xgboost/src/learner.cc:723: Check failed: mparam_.num_feature != 0 (0 vs. 0) : 0 feature is supplied.  Are you using raw Booster interface?
    ...

Let's check that there are no empty partitions by running this command, which should give no output:

    :::scala
    scala> spark.sql("SELECT * FROM iris_processed CLUSTER BY rand(0)").foreachPartition(
        part => if (part.length == 0) println(s"Zero-length partition"))

Another way to check is to run the following command, which should return the same number of partitions as the value of the `spark.sql.shuffle.partitions` parameter:

    :::scala
    scala> spark.sql("SELECT DISTINCT spark_partition_id() FROM (SELECT * FROM iris_processed CLUSTER BY rand(0))").count

(Try to set `spark.sql.shuffle.partitions` to 50 or 100 and run the previous commands to see a different behaviour.)

Finally we can create the model:

    :::scala
    scala> spark.sql("""
        CREATE TABLE iris_model_softmax AS
        SELECT train_xgboost(features, label, '-objective multi:softmax -num_class 3') AS (model_id, model)
        FROM (SELECT features, label FROM iris_processed CLUSTER BY rand(0))
        """).show

When performing a multiclass classification task, we have to explicitly specify the `-num_class` parameter; we have 3 classes in our dataset, therefore we set it to 3. The other parameter is the objective function: `multi:softmax` will use the `softmax` objective and return only the predicted class, while `multi:softprob` will use the `softprob` objective and return the probability associated to each class (see [the XGBoost docs](https://xgboost.readthedocs.io/en/release_0.90/parameter.html#learning-task-parameters) for more information, and for the other parameters). A model using the `softprob` objective can be created as follows:

    scala> spark.sql("""
        CREATE TABLE iris_model_softprob AS
        SELECT train_xgboost(features, label, '-objective multi:softprob -num_class 3') AS (model_id, model)
        FROM (SELECT features, label FROM iris_processed CLUSTER BY rand(0))
        """).show

Another important consideration is the use of `CLUSTER BY rand(0)`, which is used to shuffle the dataset in order to prevent any bias. Please note that, for simplicity, we didn't split the dataset into a training and a test set; in real-world applications this should always be done.

Now that the model is trained, we can read it:

    :::scala
    scala> val modelArray: String = spark.sql("SELECT * FROM iris_model_softprob").take(1).head(1).toString

and then visualize it:

    :::scala
    scala> import org.apache.hadoop.io.Text
    scala> import hivemall.xgboost.utils.XGBoostUtils.deserializeBooster
    scala> val booster = deserializeBooster(new Text(modelArray))
    scala> println(booster.getModelDump(Array[String](), false, "json").mkString("\n"))

The parameters of the `getModelDump` method are:

- an array of feature names (potentially empty, to map the default `f0...fn` names to user-defined names);
- a boolean to include/exclude the split statistics;
- the output format (at the moment only `"text"` or `"json"`).

We can also get the importance of each feature:

    :::scala
    scala> println(booster.getFeatureScore(Array[String]()))

<!-- Empty -->

    :::text
    {f1=18, f2=2, f3=17}

and the feature importances for several measures (one of `"weight"`, `"gain"`, `"cover"`, `"total_gain"`, `"total_cover"`):

    :::scala
    scala> booster.getScore(Array[String](), "gain")

<!-- Empty -->

    :::text
    {f1=1.4596930238833332, f2=0.0668432191, f3=1.5014036119411764}

We can customize the feature names in both methods:

    :::scala
    scala> val featureNames = Array("bias", "sepal_length", "sepal_width", "petal_length", "petal_width")
    scala> println(booster.getFeatureScore(featureNames))
    scala> booster.getScore(featureNames, "gain")

<!-- Empty -->

    :::text
    {sepal_width=2, sepal_length=18, petal_length=17}
    {sepal_width=0.0668432191, sepal_length=1.4596930238833332, petal_length=1.5014036119411764}

#### Prediction

Now that the model is ready, we can use it to classify some data. It is important to note that the way Hivemall makes XGBoost parallel is somewhat different from the parallel implementation of the official library; in fact, instead of using the [AllReduce paradigm](https://xgboost.readthedocs.io/en/latest/jvm/xgboost4j_spark_tutorial.html) where all the parallel workers have to communicate, Hivemall uses a [voting classifier](https://scikit-learn.org/stable/modules/ensemble.html#voting-classifier) on top of many _independent_ XGBoost learners. In this way every worker can train its own local model based on its partition of data (possibly overlapping with other partitions if the `amplify` or `rand_amplify` functions are used), and the actual prediction happens via a majority vote (if the objective function is `softmax`, since its output is a class label) or by averaging (if the objective function is `softprob`, since its output is a list of probabilities). We will see both examples.

Like we did for training, we need first of all to include a few more functions:

    :::scala
    scala> spark.sql("CREATE TEMPORARY FUNCTION xgboost_predict_one AS 'hivemall.xgboost.XGBoostPredictOneUDTF'")
    scala> spark.sql("CREATE TEMPORARY FUNCTION xgboost_predict_triple AS 'hivemall.xgboost.XGBoostPredictTripleUDTF'")
    scala> spark.sql("CREATE TEMPORARY FUNCTION majority_vote AS 'hivemall.tools.aggr.MajorityVoteUDAF'")

and to set another configuration option:

    :::scala
    scala> spark.sql("SET spark.sql.crossJoin.enabled=true")

This is necessary because Hivemall uses a left join without condition (basically a cross join) between the model and the data to make predictions, and cross joins are disabled by default for performance reasons.

Let's now create a table containing our predictions:

    :::scala
    scala> spark.sql("""
        CREATE TABLE iris_pred_softmax AS
        SELECT rowid, majority_vote(CAST(predicted AS INT)) AS label
        FROM (
            SELECT xgboost_predict_one(rowid, features, model_id, model) AS (rowid, predicted)
            FROM iris_model_softmax l LEFT JOIN iris_processed r) t
        GROUP BY rowid""")

We use the `xgboost_predict_one` function to predict the class of each row of the `iris_processed` table with the model stored in the `model` column of the `iris_model_softmax` table; the `rowid` is stored as well to make the model evaluation easier later on. In this case we use the `majority_vote` function to "vote" for the most frequent prediction, which will become the actual prediction. We can check the predicted values from the new table:

    :::scala
    scala> spark.sql("SELECT * FROM iris_pred_softmax ORDER BY rowid").show

Once again, keep in mind that for this example we didn't split the dataset into a training set and a test set. If we want to get the probability of each class assignment, instead, we can use the `xgboost_predict_triple` function as follows:

    :::scala
    scala> spark.sql("""
        SELECT rowid, argmax(collect_list(avg_proba)) label, collect_list(avg_proba) proba
        FROM (
            CREATE TABLE iris_pred_softprob AS
            SELECT rowid, label, avg(proba) avg_proba
            FROM (
                SELECT xgboost_predict_triple(rowid, features, model_id, model) AS (rowid, label, proba)
                FROM iris_model_softprob l LEFT JOIN iris_processed r)
            GROUP BY rowid, label ORDER BY rowid, label)
        GROUP BY rowid ORDER BY rowid""")

The prediction works in the same way as before, with three important differences:

- the prediction function now returns three values instead of two, including the probability as well;
- we do not "vote" for the most frequent class, but rather we average the probabilities of each class and select the class with the maximum average probability;
- the model we run the prediction against has to be created with the `multi:softprob` objective, otherwise the `xgboost_predict_triple` will return the wrong results.

We can also use two simpler functions, `xgboost_predict` and `xgboost_batch_predict`, to obtain the same result. The difference between the two is that `xgboost-predict` uses [xgboost-predictor-java](https://github.com/komiya-atsushi/xgboost-predictor-java) while `xgboost_batch_predict` uses [xgboost4j](https://github.com/dmlc/xgboost/tree/master/java/xgboost4j); the former runs on a per-row basis and is faster, but does not support all the models and objectives that the latter (which runs on batches) supports. Here is an example on how to use both; you can take a look at the [Hivemall examples](https://hivemall.incubator.apache.org/userguide/binaryclass/news20b_xgboost.html) for more details.

    :::scala
    scala> spark.sql("CREATE TEMPORARY FUNCTION xgboost_predict AS 'hivemall.xgboost.XGBoostOnlinePredictUDTF'")
    scala> spark.sql("CREATE TEMPORARY FUNCTION xgboost_batch_predict AS 'hivemall.xgboost.XGBoostBatchPredictUDTF'")

    spark.sql("""
        CREATE TABLE iris_pred_softprob AS
        SELECT rowid, argmax(array_avg(predicted)), array_avg(predicted) as prob
        FROM (
            SELECT xgboost_predict(rowid, features, model_id, model) AS (rowid, predicted)
            FROM iris_model_softprob l LEFT JOIN iris_processed r)
        GROUP BY rowid ORDER BY rowid""").show(5, false)

    spark.sql("""
        CREATE TABLE iris_pred_softprob AS
        SELECT rowid, argmax(array_avg(predicted)), array_avg(predicted) as prob
        FROM (
            SELECT xgboost_batch_predict(rowid, features, model_id, model) AS (rowid, predicted)
            FROM iris_model_softprob l LEFT JOIN iris_processed r)
        GROUP BY rowid ORDER BY rowid""").show(5, false)

The `array_avg` function is used to calculate the average of an array column. Again, we can check the predicted values:

    :::scala
    scala> spark.sql("SELECT * FROM iris_pred_softprob ORDER BY rowid").show

#### Evaluation

It is time now to evaluate our models. Since we performed our predictions on the same dataset that we used for training, we would expect the models to perform really good. Let's start with the `softmax` model:

    :::scala
    scala> spark.sql("""
        SELECT sum(if(actual=predicted, 1.0, 0.0))/count(1)
        FROM (
            SELECT source.label actual, pred.label predicted
            FROM iris_processed source JOIN iris_pred_softmax pred USING (rowid))""").show

Here we are simply counting all the instances where the actual value corresponds to the predicted value (using the `rowid` column to join the training dataset and the predicted dataset), then we divide that number by the number of all the instances to get a ratio. As expected, the ratio is really high (even though not exactly 1.0); we can also run exactly the same query by just swapping `iris_pred_softmax` with `iris_pred_softprob` to evaluate the second model. If we do not find very close values, the reason can be parallelization (since each partition calculates its own model); in order to get very close results we would need to reduce the `spark.sql.shuffle.partitions` value to one, effectively making the whole computation happen in only one partition by creating a single XGBoost model, which will contain the full dataset (obviously not recommended for large datasets).

### Conclusions

We have seen how Hivemall makes the XGBoost algorithm (and the classification task in general) very easy to implement and to understand. Of course there is much more to it, for instance:

- XGBoost can be configured with many different parameters, so it's worth reading its [Hivemall usage guide](https://hivemall.incubator.apache.org/userguide/binaryclass/news20b_xgboost.html) and its [configuration docs](https://xgboost.readthedocs.io/en/release_0.90/parameter.html);
- XGBoost can be used also for [binary classification](https://hivemall.incubator.apache.org/userguide/binaryclass/news20b_xgboost.html) and for [regression](https://hivemall.incubator.apache.org/userguide/regression/e2006_xgboost.html) tasks;
- Hivemall features other algorithms for classification, including a [general and highly customizable classifier](https://hivemall.incubator.apache.org/userguide/binaryclass/a9a_generic.html), [logistic regression](https://hivemall.incubator.apache.org/userguide/binaryclass/a9a_lr.html), and [mini-batch gradient descent](https://hivemall.incubator.apache.org/userguide/binaryclass/a9a_minibatch.html).

There are many other machine learning tasks to cover, such as [regression](https://en.wikipedia.org/wiki/Regression_analysis) and [clustering](https://en.wikipedia.org/wiki/Cluster_analysis), and we have just barely touched on feature engineering. So, stay tuned for another article on this very interesting project!