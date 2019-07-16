### Documentation



#### Project Structure

```yaml
astminer:
 - src:
 	- main:
 		- antlr:
 			- Java8Lexer.g4
 			- Java8Parser.g4
 			- Python3.g4
 		- generated
 		- java
 		- kotlin: do actual work
 	- test
 - py_example: a classification task
 	- data: dir for input Python files
 	- data_processing:
 		- PathMinerDataset: a tailor-made torch Dataset
 		- PathMinerLoader: a loader for PathMinerDataset
 		- UtilityEntities: PathContext and Path
 	- model:
 		- CodeVectorizer: code2vec model
 		- ProjectClassifier: a classification model
 	- run_example: run the classification example from scratch
 - testData: dir for input files
```



#### Mechanism in `/src/main/kotlin/astminer`

The main worker is written in kotlin.

`VocabularyPathStorage` class in `/paths/VocabularyPathStorage` file is the worker of saving generated information.



#### Preprocess Output

+ node_types.csv: (node_id, node_type)
+ paths.csv: (path_id, path_by_node_id)



+ tokens.csv: (token_id, token)

+ path_context.csv: (file_id, path)

  其中path的表示方式为：startTokenId pathId endTokenId

  pathId是paths.csv文件中的Id，startTokenId与endTokenId是tokens.csv中的Id