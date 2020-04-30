Title: Apache Jena Fuseki - Adding reasoning and full-text search capabilities to a dataset
Date: 2020-04-30
Category: howto
Tags: Semantic Web, full-text search, reasoning, inferencing
Alias: /apache-fuseki-adding-reasoning-and-full-text-search-capabilities-to-a-dataset.html
Status: published

With this article I am kicking off a new series called **[howto](/category/howto.html)** where, instead of describing a whole Apache project, I will explore use cases, problems and solutions related to one. I will start with [Apache Jena Fuseki](https://jena.apache.org/documentation/fuseki2/) looking into how to enable both reasoning and full-text search on a given dataset, which took me some time to figure out as the documentation is a bit lacking on the topic. As usual, I will put the relevant files and examples in the [Apothem resources repository](https://github.com/nvitucci/apothem-resources/tree/master/howto/apache-jena-fuseki/reasoning_and_fts/).

[TOC]

### Setup

#### Downloading and running Fuseki

First of all, let's download Fuseki from the [Jena download page](https://jena.apache.org/download/) (at the time of writing, the latest version is the 3.14.0). There are [different ways](https://jena.apache.org/documentation/fuseki2/fuseki-run.html) to run Fuseki, although my preference is to use it as a Web application by deploying it to Tomcat.

#### Creating a dataset

Once up and running, let's create a persistent TDB2 dataset called `example-inf`; in my case (Linux) the dataset will be created in `/etc/fuseki/databases/example-inf` and its configuration file will be stored as `/etc/fuseki/configuration/example-inf.ttl`.

Creating a dataset is very easy using the Web UI, but nothing besides the storage (in memory, TDB or TDB2) can be configured. One can also create a dataset using the [HTTP admin protocol](https://jena.apache.org/documentation/fuseki2/fuseki-server-protocol.html) and passing the database type and the dataset name as parameters:

    :::bash
    $ curl -X POST 'http://localhost:8080/fuseki/$/datasets' --data 'dbType=tdb2' --data 'dbName=example-inf'

Assuming to have the configuration specified as a Turtle file (which we skip for now), the HTTP interface makes it even possible to create a dataset as follows:

    :::bash
    $ curl -X POST 'http://localhost:8080/fuseki/$/datasets' --upload-file /tmp/example-inf.ttl --header "Content-Type: text/turtle"

#### Loading some data

In the scenario I am interested in, the reasoner should support at least `rdfs:subClassOf`, `rdfs:subPropertyOf`, `rdf:type`, and `owl:sameAs`. A minimal `data1.ttl` document that we can use for testing may be:

    :::turtle
    @prefix rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
    @prefix owl:  <http://www.w3.org/2002/07/owl#>
    @prefix id:   <http://www.example.org/id/> .
    @prefix ont:  <http://www.example.org/ont#> .

    ont:MyType rdfs:subClassOf ont:MySuperType .
    ont:myProp rdfs:subPropertyOf ont:mySuperProp .
    id:a rdf:type ont:MyType .
    id:a ont:myProp id:x .
    id:b owl:sameAs id:a .

Let's load it on the `example-inf` dataset and run a simple _SPO_ query (with an `ORDER BY` for visualization convenience):

    :::sparql
    SELECT *
    WHERE {
      ?s ?p ?o .
    }
    ORDER BY ?p ?o

As a result we should see all and only the 5 triples, while the following query with `id:a` as a subject should only return the triples `id:a rdf:type ont:MyType` and `id:a ont:myProp id:x` :

    :::sparql
    PREFIX id: <http://www.example.org/id/>

    SELECT *
    WHERE {
      id:a ?p ?o .
    }

In the following, I will refer to these two queries as _SPO_ and _id:a_ respectively.

### Adding a reasoner

The reasoners that Fuseki can directly use are forward/backward rule-based reasoners, subclasses of [FBRuleReasoner](https://jena.apache.org/documentation/javadoc/jena/org/apache/jena/reasoner/rulesys/FBRuleReasoner.html) based on this hierarchy:

    :::text
    FBRuleReasoner
    ├── GenericRuleReasoner
    │   ├── OWLMicroReasoner
    │   ├── OWLMiniReasoner
    │   └── RDFSRuleReasoner
    ├── OWLFBRuleReasoner
    └── TransitiveReasoner

Each reasoner class has an associated URI (found in its corresponding `Factory` class) which we need to know as it will be used in the dataset configuration file:

    :::text
    GenericRuleReasoner -> <http://jena.hpl.hp.com/2003/GenericRuleReasoner>
    OWLMicroReasoner    -> <http://jena.hpl.hp.com/2003/OWLMicroFBRuleReasoner>
    OWLMiniReasoner     -> <http://jena.hpl.hp.com/2003/OWLMiniFBRuleReasoner>
    RDFSRuleReasoner    -> <http://jena.hpl.hp.com/2003/RDFSExptRuleReasoner>
    OWLFBRuleReasoner   -> <http://jena.hpl.hp.com/2003/OWLFBRuleReasoner>
    TransitiveReasoner  -> <http://jena.hpl.hp.com/2003/TransitiveReasoner>

The first thing to evaluate when choosing a reasoner is the desired level of inference, taking into account that the higher the level, the longer the reasoner will take to produce all the inferred triples; [Jena documentation](https://jena.apache.org/documentation/inference/index.html) provides a good description of each reasoner, and [my (old) presentation](https://www.slideshare.net/nvitucci/semantic-web-languages-expressivity-vs-scalability) discusses the balance between expressivity and scalability. For our (small) tests, anyway, we will use the "rich" `OWLFBRuleReasoner`, taking into account that any of the other reasoners can be used by simply replacing its URL (and, in the case of the `GenericRuleReasoner`, by adding a `ja:rulesFrom <rulefile>` triple) in the configuration file.

#### Scenario 1: no named graphs

We'll start with the case where we do not need to use named graphs and all the triples are added to the default graph.

Let's check the dataset configuration file that has been created in `/etc/fuseki/configuration/example-inf.ttl`. It will contain quite a number of triples, but the relevant section for us is the following:

    :::turtle
    :service_tdb_all  a               fuseki:Service ;
        rdfs:label                    "TDB2 example-inf" ;
        fuseki:dataset                :tdb_dataset_readwrite ;
        fuseki:name                   "example-inf" ;
        fuseki:serviceQuery           "query" , "" , "sparql" ;
        fuseki:serviceReadGraphStore  "get" ;
        fuseki:serviceReadQuads       "" ;
        fuseki:serviceReadWriteGraphStore "data" ;
        fuseki:serviceReadWriteQuads  "" ;
        fuseki:serviceUpdate          "" , "update" ;
        fuseki:serviceUpload          "upload" .

    :tdb_dataset_readwrite
        a              tdb2:DatasetTDB2 ;
        tdb2:location  "/etc/fuseki/databases/example-inf" ;
        .

All we need to do is to add the following triples at the end of the file:

    :::turtle
    :dataset a ja:RDFDataset ;
        ja:defaultGraph :model_inf .

    :model_inf a ja:InfModel ;
         ja:baseModel :graph ;
         ja:reasoner [
             ja:reasonerURL <http://jena.hpl.hp.com/2003/OWLFBRuleReasoner>
         ] .

    :graph rdf:type tdb2:GraphTDB ;
      tdb2:dataset :tdb_dataset_readwrite ;
      .

and replace this line:

    :::turtle
    fuseki:dataset                :tdb_dataset_readwrite ;

with the following:

    :::turtle
    fuseki:dataset                :dataset ;

and then we need to restart Fuseki. (To avoid restarting Fuseki, the alternative would be to produce the configuration file first and then to add the new dataset via the HTTP interface.)

Now, if we run the _SPO_ query, we get a whole lot of triples including the ones related to the OWL schema; the _id:a_ query, instead, will return the five base triples plus the inferred triples:

    :::text
    ont:myProp id:x
    ont:mySuperProp id:x
    rdf:type ont:MySuperType
    rdf:type ont:MyType
    rdf:type rdfs:Resource
    rdf:type owl:Thing
    owl:sameAs id:a
    owl:sameAs id:b

What happens if we add some new triples? Let's create a `data2.ttl` file with the following content:

    :::turtle
    @prefix rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
    @prefix owl:  <http://www.w3.org/2002/07/owl#>
    @prefix id:   <http://www.example.org/id/> .
    @prefix ont:  <http://www.example.org/ont#> .

    ont:MySubType rdfs:subClassOf ont:MyType .
    id:d rdf:type ont:MySubType .
    id:d owl:sameAs id:a .

and load it. Now the _id:a_ query returns two more triples:

    :::text
    rdf:type ont:MySubType
    owl:sameAs id:d

Reasoning works fine! So let's make it even more interesting: what if we want to put our triples in a named graph?

#### Scenario 2: named graphs and no online updates

If we don't need online updates (i.e. to have the reasoner run as soon as new triples are inserted), but we are fine with restarting the server for the reasoner to catch up, all we need is to add one triple to the `:graph` section of the previous configuration:

    :::turtle hl_lines="3"
    :graph rdf:type tdb2:GraphTDB ;
      tdb2:dataset :tdb_dataset_readwrite ;
      tdb2:graphName <urn:x-arq:UnionGraph> ;
      .

The triple uses the special `<urn:x-arq:UnionGraph>` (as described [here](https://jena.apache.org/documentation/tdb/datasets.html)) to perform reasoning on _all_ the graphs. Optionally, if we want to be able to query all the named graphs without having to use the `FROM` construct, we can slightly modify the `:tdb_dataset_readwrite` section adding another triple:

    :::turtle hl_lines="4"
    :tdb_dataset_readwrite
        a              tdb2:DatasetTDB2 ;
        tdb2:location  "/etc/fuseki/databases/example-inf" ;
        tdb2:unionDefaultGraph true ;
        .

We need to keep in mind, though, that this will hide the "real" default graph replacing it with the "virtual" special union graph.

#### Scenario 3: named graphs and online updates

When using named graph, online updates will only be supported on a per-graph basis. This means that adding triples to a named graph does not "refresh" its corresponding inference model; the reasoner will be triggered only by the addition and deletion of triples to the model itself, but this change will be persisted in the underlying named graph as well.

##### One named graph

If we have only one named graph and we are fine with the inferenced triples be inserted in the default graph, the configuration is still pretty easy in that we only need to add the following triples:

    :::turtle
    :dataset a ja:RDFDataset ;
        ja:defaultGraph :model_inf ;
        ja:namedGraph [
            ja:graph        :mygraph ;
            ja:graphName    <http://www.example.org/id/mygraph>
        ] .

    :mygraph rdf:type tdb2:GraphTDB ;
      tdb2:dataset :tdb_dataset_readwrite ;
      tdb2:graphName <http://www.example.org/id/mygraph> .

    :model_inf a ja:InfModel ;
         ja:baseModel :graph ;
         ja:reasoner [
             ja:reasonerURL <http://jena.hpl.hp.com/2003/OWLFBRuleReasoner>
         ] .

    :graph rdf:type tdb2:GraphTDB ;
      tdb2:dataset :tdb_dataset_readwrite ;
      tdb2:graphName <http://www.example.org/id/mygraph>
      .

and, again, replace this line:

    :::turtle
    fuseki:dataset                :tdb_dataset_readwrite ;

with the following:

    :::turtle
    fuseki:dataset                :dataset ;

Basically, the example `<http://www.example.org/id/mygraph>` named graph has to be added explicitly both to the `:dataset` (via `ja:namedGraph`) and to the `:graph` underlying the `:model_inf` (via `tdb2:graphName`); this will let us query both the original named graph and the inferred model, and updates to the default graph will be reflected in the named graph.

##### Many named graphs

If we have more than one named graph and we want to support cross-graph inference, things get more complicated. One possible solution is to have each named graph be wrapped by a model (updated in real time) and the default graph be the union of _all_ the graphs (updated upon server restart).

    :::turtle
    :dataset a ja:RDFDataset ;
        ja:defaultGraph :model_inf ;
        ja:namedGraph [
            ja:graph        :mygraph ;
            ja:graphName    <http://www.example.org/id/mygraph>
        ] ;
        ja:namedGraph [
            ja:graph        :mygraph2 ;
            ja:graphName    <http://www.example.org/id/mygraph2>
        ] ;
        ja:namedGraph [
            ja:graph        :inf ;
            ja:graphName    <http://www.example.org/id/inf>
        ] ;
        ja:namedGraph [
            ja:graph        :inf2 ;
            ja:graphName    <http://www.example.org/id/inf2>
        ] .

    :mygraph rdf:type tdb2:GraphTDB ;
      tdb2:dataset :tdb_dataset_readwrite ;
      tdb2:graphName <http://www.example.org/id/mygraph>
      .

    :mygraph2 rdf:type tdb2:GraphTDB ;
      tdb2:dataset :tdb_dataset_readwrite ;
      tdb2:graphName <http://www.example.org/id/mygraph2>
      .

    :inf a ja:InfModel ;
         ja:baseModel :graph ;
         ja:reasoner [
             ja:reasonerURL <http://jena.hpl.hp.com/2003/OWLFBRuleReasoner>
         ] .

    :inf2 a ja:InfModel ;
         ja:baseModel :graph2 ;
         ja:reasoner [
             ja:reasonerURL <http://jena.hpl.hp.com/2003/OWLFBRuleReasoner>
         ] .

    :graph rdf:type tdb2:GraphTDB ;
      tdb2:dataset :tdb_dataset_readwrite ;
      tdb2:graphName <http://www.example.org/id/mygraph>
      .

    :graph2 rdf:type tdb2:GraphTDB ;
      tdb2:dataset :tdb_dataset_readwrite ;
      tdb2:graphName <http://www.example.org/id/mygraph2>
      .

    :model_inf a ja:InfModel ;
         ja:baseModel :union_graph ;
         ja:reasoner [
             ja:reasonerURL <http://jena.hpl.hp.com/2003/OWLFBRuleReasoner>
         ] .

    :union_graph rdf:type tdb2:GraphTDB ;
      tdb2:dataset :tdb_dataset_readwrite ;
      tdb2:graphName <urn:x-arq:UnionGraph>
      .

Let's test this complex configuration. We will:

1. create an `example-inf-multinamed` dataset, update its configuration file, and restart Fuseki;

- upload the `data1.ttl` file under the `<http://www.example.org/id/mygraph>` named graph;

- run the following _g-id:a_ query (similar to the _id:a_ query but including the graph):

        :::sparql
        PREFIX id: <http://www.example.org/id/>

        SELECT *
        WHERE {
          GRAPH ?g {
          	id:a ?p ?o
          }
        }
        ORDER BY ?g ?p ?o

    and make sure we get the following triples as a result (to verify that inference is working correctly on the `<http://www.example.org/id/inf>` model based on the `<http://www.example.org/id/mygraph>` graph):

        :::text
        ont:myProp id:x id:inf
        ont:mySuperProp id:x id:inf
        rdf:type ont:MySuperType id:inf
        rdf:type ont:MyType id:inf
        rdf:type rdfs:Resource id:inf
        rdf:type owl:Thing id:inf
        owl:sameAs id:a id:inf
        owl:sameAs id:b id:inf
        ont:myProp id:x id:mygraph
        rdf:type ont:MyType id:mygraph

- run the _id:a_ query and make sure we get the following triples as a result (to verify that the default union graph contains at least the original triples):

        :::text
        ont:myProp id:x
        rdf:type ont:MyType
        rdf:type rdfs:Resource
        rdf:type owl:Thing
        owl:sameAs id:a
        owl:sameAs id:b

- load `data2.ttl` under the same `<http://www.example.org/id/mygraph>` graph and rerun both queries (to verify that no change occurs when the base named graph is updated);

- load `data2.ttl` under `<http://www.example.org/id/inf>` instead, then run the _g-id:a_ query and make sure we get the following triples as a result (to verify that adding triples to a model makes inference happen right away):

        :::text
        rdf:type ont:MySuperType id:inf
        owl:sameAs id:d id:inf

- run the _id:a_ query and make sure that the results are the same as before (to verify that no, or limited, inference happens in the default graph without a restart);

- restart Fuseki and run the _id:a_ query again to check that all the inferred triples are present;

- create a `data3.ttl` file with the following content, then add it to `<http://www.example.org/id/inf2>`:

        :::turtle
        @prefix rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
        @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
        @prefix owl:  <http://www.w3.org/2002/07/owl#>
        @prefix id:   <http://www.example.org/id/> .
        @prefix ont:  <http://www.example.org/ont#> .

        ont:MyOtherSubType rdfs:subClassOf ont:MyType .
        id:XXX rdf:type ont:MyOtherSubType .
        id:XXX owl:sameAs id:a .

- run the _g-id:a_ query and make sure that the following results are included (to verify again that adding triples to a model makes inference happen right away):

        :::text
        ...
        rdf:type ont:MyOtherSubType id:inf2
        rdf:type ont:MyType id:inf2
        rdf:type rdfs:Resource id:inf2
        rdf:type owl:Thing id:inf2
        owl:sameAs id:XXX id:inf2
        owl:sameAs id:a id:inf2
        ...

- run the _id:a_ query again and make sure it gives the same results as before (to verify again that no, or limited, inference happens in the default graph without a restart);

- restart Fuseki and run the _id:a_ query again and make sure we get the following triples in addition (to verify that cross-graph inference works upon restart):

        :::text
        ...
        rdf:type ont:MyOtherSubType
        owl:sameAs id:XXX
        ...

### Adding full-text search

After such a complex exercise on the reasoners, we may wonder whether it would be possible to add full-text search capabilities to a configuration that already includes a reasoner. The answer is: yes! The index will not include inferred triples though, but it will be useful to find some base triples to base other queries on. The configuration of a full-text index would require an article by itself, so here we will just stick to a base configuration to verify that it can work together with a reasoner.

We will build upon the simplest configuration that includes a reasoner, so we will start by creating a `example-inf-lucene` dataset as before, then we will update its configuration file by adding the following triples:

    :::turtle
    @prefix text: <http://jena.apache.org/text#>
    ...

    :dataset a ja:RDFDataset ;
        ja:defaultGraph :model_inf .

    :model_inf a ja:InfModel ;
         ja:baseModel :graph ;
         ja:reasoner [
             ja:reasonerURL <http://jena.hpl.hp.com/2003/OWLFBRuleReasoner>
         ] .

    :graph rdf:type tdb2:GraphTDB ;
      tdb2:dataset :tdb_dataset_readwrite .

    :text_dataset rdf:type     text:TextDataset ;
        text:dataset   :dataset ;
        text:index     :indexLucene .

    :indexLucene a text:TextIndexLucene ;
        text:directory <file:/etc/fuseki/databases/example-inf-lucene-index> ;
        text:entityMap :entMap ;
        text:storeValues true ;
        text:analyzer [ a text:StandardAnalyzer ] ;
        text:queryAnalyzer [ a text:StandardAnalyzer ] ;
        text:queryParser text:AnalyzingQueryParser .

    :entMap a text:EntityMap ;
        text:defaultField     "label" ;
        text:entityField      "uri" ;
        text:uidField         "uid" ;
        text:langField        "lang" ;
        text:graphField       "graph" ;
        text:map (
            [ text:field "label" ;
              text:predicate rdfs:label ]
            [ text:field "title" ;
              text:predicate <http://www.example.org/ont#title> ]
        ) .

and replace this line:

    :::turtle
    fuseki:dataset                :tdb_dataset_readwrite ;

with the following:

    :::turtle
    fuseki:dataset                :text_dataset ;

This configuration wraps the dataset containing the inference model with a `TextDataset` so that a full-text index can be added; more specifically, it will let us search on the objects of the `rdfs:label` and `<http://www.example.org/ont#title>` predicates. The important bits to remember are:

- the prefix `<http://jena.apache.org/text#>`;
- the `text:directory <file:/etc/fuseki/databases/example-inf-lucene-index>` triple (the physical location of the text index);
- the `text:map` triples that create Lucene document fields (the values of `text:field`) associated to RDF properties (the values of `text:predicate`).

Let's restart and load `data1.ttl` to this new dataset, then run the following query:

    :::sparql
    PREFIX ont: <http://www.example.org/ont#>
    PREFIX id: <http://www.example.org/id/>
    PREFIX text: <http://jena.apache.org/text#>

    SELECT *
    WHERE {
      ?s text:query (ont:title 'title') .
    }

which will give no result as no triples with the `ont:title` predicate have been inserted. Now let's create a new file `data4.ttl` with the following content:

    :::turtle
    @prefix rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
    @prefix owl:  <http://www.w3.org/2002/07/owl#>
    @prefix id:   <http://www.example.org/id/> .
    @prefix ont:  <http://www.example.org/ont#> .

    id:with-label rdfs:label "Usual label" .
    id:with-label owl:sameAs id:a .
    id:with-title ont:title "Meaningful title" .
    id:with-title owl:sameAs id:a .


and rerun the query. Now the result will be `	id:with-title`, and we can get more information if we run the following query instead:

    :::sparql
    PREFIX ont: <http://www.example.org/ont#>
    PREFIX id: <http://www.example.org/id/>
    PREFIX text: <http://jena.apache.org/text#>

    SELECT *
    WHERE {
      (?s ?score ?title ?graph ?prop) text:query (ont:title 'title') .
    }

which will give the following result:

    :::text
    id:with-title "0.14181954"^^xsd:float "Meaningful title" <urn:x-arq:DefaultGraphNode> ont:title

To verify that the reasoner still works, let's run the _id:a_ query again and make sure that the results include `rdfs:label "Usual label"` and `owl:sameAs id:with-title`.

### Conclusions

Automated reasoning is a complex topic, and we have seen how Jena and Fuseki are flexible enough to allow for advanced solutions. Sometimes this flexibility may come at the cost of clarity, but I am sure that, once the community starts discussing more and more use cases, simpler and cleaner solutions will come up.