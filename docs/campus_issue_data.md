##### Campus Issue Data – Pipeline



The whole pipeline is designed to turn one raw meeting-record PDF into multiple structured issue records that can later be stored in the database. This involves the following steps, each executed one after another.



* **Get raw PDF**

&#x20;Start from the original PDF file and keep it unchanged as the raw source.

* **Default extraction**

&#x20;Extract the text and basic metadata from the PDF, such as filename and page count.

* **Text cleaning**

&#x20;Clean the extracted text by removing broken line breaks, repeated headers, page numbers, and other PDF noise.

* **Structural segmentation**

&#x20;Split the meeting record into meaningful parts.

&#x20;First split the main meeting body from the attached draft documents, then split the discussion section into separate issue items such as 案由一、案由二, etc.

* **Rule-based extraction**

&#x20;Use simple rules and config files to fill stable fields, such as source platform, source organization, content type, title, event time, and some initial topic hints.

* **Semantic extraction**

&#x20;Use an LLM to generate fields that require understanding, such as summary, topic, and subtopic.

* **Validation**

&#x20;Check whether the final structured record is complete enough and whether the field values are valid.

* **Fill DB**

&#x20;Insert the final issue-level records into the database, while keeping the link back to the original source PDF.





\--------------------------------------------------------------------------





##### Folder structure





campus\_issue\_data/

│

├─ README.md

├─ requirements.txt

├─ .env

│

├─ configs/

│  ├─ sources.yaml

│  ├─ segmentation.yaml

│  ├─ rules.yaml

│  ├─ schema.yaml

│  └─ prompts/

│     ├─ summary\_prompt.txt

│     └─ topic\_prompt.txt

│

├─ data/

│  ├─ raw/

│  │  └─ stuaffairs/

│  │     └─ 第59次會議紀錄.pdf

│  ├─ extracted/

│  ├─ segmented/

│  ├─ normalized/

│  ├─ enriched/

│  └─ failed/

│

├─ db/

│  ├─ schema.sql

│  └─ init\_db.py

│

├─ src/

│  ├─ main.py

│  ├─ pipeline.py

│  │

│  ├─ extract\_pdf.py

│  ├─ clean\_text.py

│  ├─ segment\_document.py

│  ├─ apply\_rules.py

│  ├─ semantic\_extract.py

│  ├─ validate\_record.py

│  ├─ insert\_db.py

│  │

│  ├─ llm\_client.py

│  ├─ io\_utils.py

│  ├─ text\_utils.py

│  └─ ids.py

│

└─ tests/

&#x20;  ├─ test\_segmentation.py

&#x20;  ├─ test\_rules.py

&#x20;  └─ test\_semantic.py



\--------------------------------------------------------------------------



The project structure is separated by stage, so each file or folder has one clear job. This makes the pipeline easier to debug and easier to extend later.



* **configs/**

&#x20;Stores configuration files, such as source defaults, segmentation rules, field rules, schema definition, and LLM prompts.



* **data/raw/**

&#x20;Stores the original PDF files.

* **data/extracted/**

&#x20;Stores the whole-document extraction result after reading the PDF.

* **data/segmented/**

&#x20;Stores the issue segments and attachment segments after splitting the document.

* **data/normalized/**

&#x20;Stores the records after rule-based extraction has filled the stable fields.

* **data/enriched/**

&#x20;Stores the records after LLM-based semantic extraction has added summary and topic fields.

* **data/failed/**

&#x20;Stores records that fail validation or processing.



* **db/**

&#x20;Stores the SQL schema and database initialization files.



* **src/main.py**

&#x20;Entry point of the program. Starts the whole pipeline.

* **src/pipeline.py**

&#x20;Controls the full workflow from raw PDF to DB insertion.

* **src/extract\_pdf.py**

&#x20;Extracts text and basic metadata from the PDF.

* **src/clean\_text.py**

&#x20;Cleans the extracted text.

* **src/segment\_document.py**

&#x20;Splits the cleaned meeting record into sections, issue items, and attachments.

* **src/apply\_rules.py**

&#x20;Applies rule-based extraction to fill stable structured fields.

* **src/semantic\_extract.py**

&#x20;Calls the LLM to generate summary and topic-related fields.

* **src/validate\_record.py**

&#x20;Checks whether the final record is valid.

* **src/insert\_db.py**

&#x20;Inserts validated records into the database.

* **src/llm\_client.py**

&#x20;Handles communication with the deployed LLM.

* **src/io\_utils.py**

&#x20;Handles shared file reading and writing, such as JSON and YAML.

* **src/text\_utils.py**

&#x20;Stores reusable text-processing helpers.

* **src/ids.py**

&#x20;Generates ids for source documents, segments, and records.







